"""Main crawl-and-analysis pipeline orchestration."""

from __future__ import annotations

from copy import deepcopy
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
import hashlib
import json
import socket
import time
from typing import Sequence
from urllib.parse import urlsplit

from .analysis import JobAnalyzer
from .config import Settings, load_settings
from .connectors import CakeConnector, LinkedInConnector, Site104Connector, Site1111Connector
from .data_quality import build_snapshot_data_quality_report
from .job_cleaning import merge_duplicate_jobs
from .market_history_store import MarketHistoryStore
from .models import JobListing, MARKET_SNAPSHOT_SCHEMA_VERSION, MarketSnapshot, TargetRole
from .storage import now_iso, save_snapshot
from .targets import DEFAULT_TARGET_ROLES, build_default_queries
from .utils import CachedFetcher, ensure_directory


class JobMarketPipeline:
    """Coordinate search collection, detail enrichment, scoring, and snapshot creation."""

    INITIAL_WAVE_JOB_TARGET = 20
    INITIAL_WAVE_SOURCE_TARGET = 2
    INITIAL_WAVE_TIMEOUT_SECONDS = 2.0
    INITIAL_WAVE_MIN_RESULTS_GRACE_SECONDS = 4.0

    def __init__(
        self,
        settings: Settings | None = None,
        role_targets: list[TargetRole] | None = None,
        force_refresh: bool = False,
        perform_cache_maintenance: bool = False,
    ) -> None:
        self.settings = settings or load_settings()
        self.role_targets = role_targets or DEFAULT_TARGET_ROLES
        self.force_refresh = bool(force_refresh)
        self._raw_collection_jobs: list[JobListing] = []
        self._last_deduped_jobs: list[JobListing] = []
        ensure_directory(self.settings.data_dir)
        self.fetcher = CachedFetcher(
            cache_dir=self.settings.cache_dir,
            timeout=self.settings.request_timeout,
            delay_seconds=self.settings.request_delay,
            user_agent=self.settings.user_agent,
            allow_insecure_ssl_fallback=self.settings.allow_insecure_ssl_fallback,
            backend=self.settings.cache_backend,
        )
        if perform_cache_maintenance:
            self.fetcher.purge_cache(
                max_bytes=self.settings.cache_max_bytes,
                max_files=self.settings.cache_max_files,
            )
        self.connectors = [
            Site104Connector(settings=self.settings, fetcher=self.fetcher),
            Site1111Connector(settings=self.settings, fetcher=self.fetcher),
        ]
        if self.settings.enable_cake:
            self.connectors.append(CakeConnector(settings=self.settings, fetcher=self.fetcher))
        if self.settings.enable_linkedin:
            self.connectors.append(
                LinkedInConnector(settings=self.settings, fetcher=self.fetcher)
            )
        for connector in self.connectors:
            connector.force_refresh = self.force_refresh

    def collect_jobs(
        self,
        queries: list[str] | None = None,
    ) -> tuple[list[JobListing], list[str]]:
        """Collect, deduplicate, and initially score jobs without expensive detail analysis."""
        queries = queries or build_default_queries(self.role_targets)
        self._reset_collection_quality()
        dns_ok, dns_error = self._preflight_dns(self.connectors)
        if not dns_ok:
            return [], [dns_error]
        collected: list[JobListing] = []
        errors: list[str] = []
        max_workers = max(1, min(self.settings.max_concurrent_requests, len(self.connectors)))
        if max_workers <= 1:
            for connector in self.connectors:
                jobs, connector_errors = self._collect_from_connector(connector, queries)
                collected.extend(jobs)
                errors.extend(connector_errors)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self._collect_from_connector, connector, queries): connector
                    for connector in self.connectors
                }
                for future in as_completed(future_map):
                    connector = future_map[future]
                    try:
                        jobs, connector_errors = future.result()
                        collected.extend(jobs)
                        errors.extend(connector_errors)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{connector.source}: {exc}")

        scored_jobs = self._score_and_sort_jobs(collected)
        self._record_collection_quality(new_raw_jobs=collected, deduped_jobs=scored_jobs)
        return scored_jobs, errors

    def collect_initial_wave(
        self,
        queries: list[str] | None = None,
    ) -> tuple[list[JobListing], list[str], list[str]]:
        """Collect only page 1 and return as soon as the first visible wave is ready."""
        queries = queries or build_default_queries(self.role_targets)
        self._reset_collection_quality()
        dns_ok, dns_error = self._preflight_dns(self.connectors)
        if not dns_ok:
            return [], [dns_error], []
        collected: list[JobListing] = []
        errors: list[str] = []
        completed_sources: set[str] = set()
        max_workers = max(1, min(self.settings.max_concurrent_requests, len(self.connectors)))
        start_time = time.monotonic()

        if max_workers <= 1:
            for connector in self.connectors:
                jobs, connector_errors = self._collect_from_connector(
                    connector,
                    queries,
                    pages=[1],
                )
                collected.extend(jobs)
                errors.extend(connector_errors)
                completed_sources.add(connector.source)
                if self._initial_wave_ready(
                    collected_jobs=collected,
                    completed_sources=completed_sources,
                    started_at=start_time,
                ):
                    break
            scored_jobs = self._score_and_sort_jobs(collected)
            self._record_collection_quality(new_raw_jobs=collected, deduped_jobs=scored_jobs)
            return scored_jobs, errors, sorted(completed_sources)

        executor = ThreadPoolExecutor(max_workers=max_workers)
        future_map = {
            executor.submit(self._collect_from_connector, connector, queries, [1]): connector
            for connector in self.connectors
        }
        pending = set(future_map)
        try:
            while pending:
                remaining_timeout = max(
                    0.0,
                    self.INITIAL_WAVE_TIMEOUT_SECONDS - (time.monotonic() - start_time),
                )
                done, pending = wait(
                    pending,
                    timeout=remaining_timeout,
                    return_when=FIRST_COMPLETED,
                )
                if not done:
                    break
                for future in done:
                    connector = future_map[future]
                    try:
                        jobs, connector_errors = future.result()
                        collected.extend(jobs)
                        errors.extend(connector_errors)
                        completed_sources.add(connector.source)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{connector.source}: {exc}")
                if self._initial_wave_ready(
                    collected_jobs=collected,
                    completed_sources=completed_sources,
                    started_at=start_time,
                ):
                    break
            if not collected and pending:
                grace_timeout = min(
                    max(
                        self.INITIAL_WAVE_MIN_RESULTS_GRACE_SECONDS,
                        len(queries) * 0.75,
                    ),
                    max(self.settings.request_timeout, self.INITIAL_WAVE_TIMEOUT_SECONDS),
                )
                done, pending = wait(
                    pending,
                    timeout=grace_timeout,
                    return_when=FIRST_COMPLETED,
                )
                for future in done:
                    connector = future_map[future]
                    try:
                        jobs, connector_errors = future.result()
                        collected.extend(jobs)
                        errors.extend(connector_errors)
                        completed_sources.add(connector.source)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{connector.source}: {exc}")
        finally:
            for future in pending:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)

        scored_jobs = self._score_and_sort_jobs(collected)
        self._record_collection_quality(new_raw_jobs=collected, deduped_jobs=scored_jobs)
        return scored_jobs, errors, sorted(completed_sources)

    def collect_remaining_waves(
        self,
        queries: list[str],
        existing_jobs: list[JobListing],
        *,
        page_cursor: int,
        completed_initial_sources: Sequence[str] | None = None,
    ) -> tuple[list[JobListing], list[str], int]:
        """Collect one follow-up search wave and merge it into the current scored results."""
        dns_ok, dns_error = self._preflight_dns(self.connectors)
        if not dns_ok:
            stop_cursor = self.settings.max_pages_per_source + 1
            return self._score_and_sort_jobs(existing_jobs), [dns_error], stop_cursor
        if page_cursor > self.settings.max_pages_per_source:
            return self._score_and_sort_jobs(existing_jobs), [], page_cursor

        completed_sources = {str(source) for source in (completed_initial_sources or [])}
        if page_cursor == 1:
            target_connectors = [
                connector
                for connector in self.connectors
                if connector.source not in completed_sources
            ]
        else:
            target_connectors = list(self.connectors)

        if not target_connectors:
            return self._score_and_sort_jobs(existing_jobs), [], page_cursor + 1

        collected: list[JobListing] = []
        errors: list[str] = []
        max_workers = max(1, min(self.settings.max_concurrent_requests, len(target_connectors)))
        if max_workers <= 1:
            for connector in target_connectors:
                jobs, connector_errors = self._collect_from_connector(
                    connector,
                    queries,
                    pages=[page_cursor],
                )
                collected.extend(jobs)
                errors.extend(connector_errors)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(
                        self._collect_from_connector,
                        connector,
                        queries,
                        [page_cursor],
                    ): connector
                    for connector in target_connectors
                }
                for future in as_completed(future_map):
                    connector = future_map[future]
                    try:
                        jobs, connector_errors = future.result()
                        collected.extend(jobs)
                        errors.extend(connector_errors)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{connector.source}: {exc}")

        merged_jobs = self._dedupe_jobs([*existing_jobs, *collected])
        self._record_collection_quality(new_raw_jobs=collected, deduped_jobs=merged_jobs)
        return self._score_and_sort_jobs(merged_jobs), errors, page_cursor + 1

    def build_partial_snapshot(
        self,
        *,
        queries: list[str],
        jobs: list[JobListing],
        errors: list[str],
        generated_at: str | None = None,
    ) -> MarketSnapshot:
        """Create a lightweight snapshot that can be rendered before analysis finishes."""
        partial_jobs = deepcopy(jobs)
        return MarketSnapshot(
            generated_at=generated_at or now_iso(),
            queries=list(queries),
            role_targets=deepcopy(self.role_targets),
            jobs=partial_jobs,
            skills=[],
            task_insights=[],
            errors=list(errors),
            snapshot_kind="partial",
            data_quality=self._build_snapshot_data_quality(
                queries=queries,
                final_jobs=partial_jobs,
                errors=errors,
                snapshot_kind="partial",
            ),
        )

    def complete_snapshot(
        self,
        *,
        queries: list[str],
        jobs: list[JobListing],
        errors: list[str],
    ) -> MarketSnapshot:
        """Finish scoring, filtering, summarization, and persistence for a crawl result."""
        rescored = JobAnalyzer(self.role_targets).score_jobs(deepcopy(jobs))
        working_errors = list(errors)
        filtered_jobs = self._filter_low_relevance_jobs(rescored, working_errors)
        analyzer = JobAnalyzer(self.role_targets)
        skills = analyzer.summarize_skills(filtered_jobs)
        task_insights = analyzer.summarize_tasks(filtered_jobs)
        snapshot = MarketSnapshot(
            generated_at=now_iso(),
            queries=list(queries),
            role_targets=deepcopy(self.role_targets),
            jobs=filtered_jobs,
            skills=skills,
            task_insights=task_insights,
            errors=working_errors,
            snapshot_kind="complete",
            data_quality=self._build_snapshot_data_quality(
                queries=queries,
                final_jobs=filtered_jobs,
                errors=working_errors,
                snapshot_kind="complete",
            ),
        )
        save_snapshot(snapshot, self.settings.snapshot_path)
        MarketHistoryStore(
            self.settings.market_history_db_path,
            retention_days=self.settings.market_history_retention_days,
            max_runs_per_query=self.settings.market_history_max_runs_per_query,
        ).record_snapshot(snapshot)
        return snapshot

    def finalize_snapshot(
        self,
        *,
        queries: list[str],
        jobs: list[JobListing],
        errors: list[str],
    ) -> MarketSnapshot:
        """Run full detail enrichment first, then materialize the final saved snapshot."""
        working_jobs = deepcopy(jobs)
        working_errors = list(errors)
        self._enrich_details_by_relevance(working_jobs, working_errors)
        return self.complete_snapshot(
            queries=queries,
            jobs=working_jobs,
            errors=working_errors,
        )

    def run(self, queries: list[str] | None = None) -> MarketSnapshot:
        """Compatibility wrapper that executes the full staged pipeline in one call."""
        queries = queries or build_default_queries(self.role_targets)
        collected_jobs, errors = self.collect_jobs(queries)
        return self.finalize_snapshot(queries=queries, jobs=collected_jobs, errors=errors)

    def _enrich_details_by_relevance(
        self,
        jobs: list[JobListing],
        errors: list[str],
    ) -> None:
        """Enrich the top detail candidates for each source in relevance order."""
        detail_candidates = self._detail_candidates_by_source(jobs)
        for connector in self.connectors:
            source_jobs = detail_candidates.get(connector.source, [])
            if not source_jobs:
                continue
            try:
                connector.enrich_details(source_jobs)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{connector.source} detail: {exc}")

    def enrich_job_batch(
        self,
        jobs: list[JobListing],
        errors: list[str],
        *,
        start_index: int,
        batch_size: int,
    ) -> tuple[int, int]:
        """Enrich one global detail batch and return the next cursor with total candidates."""
        detail_candidates = self._detail_candidates(jobs)
        total_candidates = len(detail_candidates)
        if total_candidates == 0:
            return 0, 0
        batch_start = max(0, start_index)
        batch_end = min(total_candidates, batch_start + max(0, batch_size))
        batch_jobs = detail_candidates[batch_start:batch_end]
        if not batch_jobs:
            return total_candidates, total_candidates

        for connector in self.connectors:
            connector_jobs = [job for job in batch_jobs if job.source == connector.source]
            if not connector_jobs:
                continue
            try:
                connector.enrich_details(connector_jobs)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{connector.source} detail: {exc}")
        return batch_end, total_candidates

    def _filter_low_relevance_jobs(
        self,
        jobs: list[JobListing],
        errors: list[str],
    ) -> list[JobListing]:
        """Drop jobs below the configured relevance threshold and emit user-facing notes."""
        filtered = [
            job for job in jobs if job.relevance_score >= self.settings.min_relevance_score
        ]
        removed = len(jobs) - len(filtered)
        if removed > 0:
            errors.append(f"已略過 {removed} 筆低相關職缺，避免統計被無關職缺污染。")
        if not filtered and jobs:
            errors.append("目前沒有達到關聯度門檻的職缺，建議調整目標職缺或關鍵字。")
        return filtered

    def _dedupe_jobs(self, jobs: list[JobListing]) -> list[JobListing]:
        """Normalize fields, then merge same-source and cross-source duplicates."""
        return merge_duplicate_jobs(jobs)

    def _collect_from_connector(
        self,
        connector,
        queries: list[str],
        pages: Sequence[int] | None = None,
    ) -> tuple[list[JobListing], list[str]]:
        """Run one connector search safely and normalize connector-local error capture."""
        try:
            try:
                jobs = connector.search(queries, pages=pages)
            except TypeError:
                jobs = connector.search(queries)
        except Exception as exc:  # noqa: BLE001
            return [], [f"{connector.source}: {exc}"]
        connector_errors = [str(message) for message in getattr(connector, "last_errors", [])]
        return jobs, connector_errors

    @staticmethod
    def _preflight_dns(connectors) -> tuple[bool, str]:
        hosts: list[str] = []
        for connector in connectors:
            base_url = getattr(connector, "base_url", "") or ""
            host = urlsplit(base_url).hostname
            if not host:
                host = urlsplit(str(getattr(connector, "search_url_template", ""))).hostname
            if host:
                hosts.append(host)
        if not hosts:
            return True, ""
        for host in dict.fromkeys(hosts):
            try:
                socket.getaddrinfo(host, 443)
            except OSError as exc:
                return (
                    False,
                    f"DNS 解析失敗：{host} 無法解析（{exc}）。"
                    "請確認網路連線或 DNS 設定。",
                )
        return True, ""

    def _detail_candidates_by_source(
        self,
        jobs: list[JobListing],
    ) -> dict[str, list[JobListing]]:
        """Select the top N detail candidates per source before expensive enrichment."""
        candidates: dict[str, list[JobListing]] = {}
        for connector in self.connectors:
            source_jobs = [
                job
                for job in jobs
                if job.source == connector.source and not job.metadata.get("detail_enriched")
            ]
            if not source_jobs:
                continue
            source_jobs.sort(key=lambda item: item.relevance_score, reverse=True)
            if self.settings.max_detail_jobs_per_source > 0:
                source_jobs = source_jobs[: self.settings.max_detail_jobs_per_source]
            candidates[connector.source] = source_jobs
        return candidates

    def _detail_candidates(self, jobs: list[JobListing]) -> list[JobListing]:
        """Flatten source-specific detail candidates into one relevance-sorted list."""
        candidates: list[JobListing] = []
        detail_candidates = self._detail_candidates_by_source(jobs)
        for connector in self.connectors:
            candidates.extend(detail_candidates.get(connector.source, []))
        candidates.sort(key=lambda item: item.relevance_score, reverse=True)
        return candidates

    def _score_and_sort_jobs(self, jobs: list[JobListing]) -> list[JobListing]:
        """Deduplicate and re-score jobs after each search wave merge."""
        deduped = self._dedupe_jobs(jobs)
        analyzer = JobAnalyzer(self.role_targets)
        return analyzer.score_jobs(deduped)

    def _initial_wave_ready(
        self,
        *,
        collected_jobs: list[JobListing],
        completed_sources: set[str],
        started_at: float,
    ) -> bool:
        """Determine whether enough first-wave results are ready to render."""
        deduped_count = len(self._dedupe_jobs(collected_jobs))
        elapsed = time.monotonic() - started_at
        return (
            deduped_count >= self.INITIAL_WAVE_JOB_TARGET
            or len(completed_sources) >= self.INITIAL_WAVE_SOURCE_TARGET
            or elapsed >= self.INITIAL_WAVE_TIMEOUT_SECONDS
        )

    def _reset_collection_quality(self) -> None:
        """Reset collection-quality trackers for a new crawl session."""
        self._raw_collection_jobs = []
        self._last_deduped_jobs = []

    def _record_collection_quality(
        self,
        *,
        new_raw_jobs: list[JobListing],
        deduped_jobs: list[JobListing],
    ) -> None:
        """Track raw and deduped jobs across staged crawl waves."""
        self._raw_collection_jobs.extend(deepcopy(new_raw_jobs))
        self._last_deduped_jobs = deepcopy(deduped_jobs)

    def _build_snapshot_data_quality(
        self,
        *,
        queries: list[str],
        final_jobs: list[JobListing],
        errors: list[str],
        snapshot_kind: str,
    ) -> dict[str, object]:
        """Build quality and lineage metadata for the current snapshot."""
        raw_jobs = deepcopy(self._raw_collection_jobs) if self._raw_collection_jobs else deepcopy(final_jobs)
        deduped_jobs = deepcopy(self._last_deduped_jobs) if self._last_deduped_jobs else deepcopy(final_jobs)
        report = build_snapshot_data_quality_report(
            connector_sources=[connector.source for connector in self.connectors],
            raw_jobs=raw_jobs,
            deduped_jobs=deduped_jobs,
            final_jobs=deepcopy(final_jobs),
            errors=list(errors),
            snapshot_kind=snapshot_kind,
        )
        cross_source_merge_count = sum(
            1
            for job in final_jobs
            if bool((job.metadata or {}).get("cross_source_merged"))
        )
        lineage_record_count = sum(len(job.lineage_trail or []) for job in final_jobs)
        detail_enriched_count = sum(
            1
            for job in final_jobs
            if bool((job.metadata or {}).get("detail_enriched"))
        )
        report["snapshot_version"] = MARKET_SNAPSHOT_SCHEMA_VERSION
        report["snapshot_query_signature"] = self._build_snapshot_query_signature(queries=queries)
        report["lineage"] = {
            "connector_sources": [connector.source for connector in self.connectors],
            "query_terms": list(queries),
            "role_targets": [role.name for role in self.role_targets],
            "raw_collection_count": len(raw_jobs),
            "deduped_count": len(deduped_jobs),
            "final_count": len(final_jobs),
            "detail_enriched_count": detail_enriched_count,
            "cross_source_merge_count": cross_source_merge_count,
            "lineage_record_count": lineage_record_count,
        }
        return report

    def _build_snapshot_query_signature(self, *, queries: list[str]) -> str:
        payload = {
            "queries": list(queries),
            "roles": [
                {
                    "name": role.name,
                    "priority": role.priority,
                    "keywords": role.keywords,
                }
                for role in self.role_targets
            ],
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
