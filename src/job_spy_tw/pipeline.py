from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .analysis import JobAnalyzer
from .config import Settings, load_settings
from .connectors import LinkedInConnector, Site104Connector, Site1111Connector
from .models import JobListing, MarketSnapshot, TargetRole
from .storage import now_iso, save_snapshot
from .targets import DEFAULT_TARGET_ROLES, build_default_queries
from .utils import CachedFetcher, ensure_directory


class JobMarketPipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        role_targets: list[TargetRole] | None = None,
        force_refresh: bool = False,
    ) -> None:
        self.settings = settings or load_settings()
        self.role_targets = role_targets or DEFAULT_TARGET_ROLES
        self.force_refresh = bool(force_refresh)
        ensure_directory(self.settings.data_dir)
        self.fetcher = CachedFetcher(
            cache_dir=self.settings.cache_dir,
            timeout=self.settings.request_timeout,
            delay_seconds=self.settings.request_delay,
            user_agent=self.settings.user_agent,
            allow_insecure_ssl_fallback=self.settings.allow_insecure_ssl_fallback,
        )
        self.connectors = [
            Site104Connector(settings=self.settings, fetcher=self.fetcher),
            Site1111Connector(settings=self.settings, fetcher=self.fetcher),
        ]
        if self.settings.enable_linkedin:
            self.connectors.append(
                LinkedInConnector(settings=self.settings, fetcher=self.fetcher)
            )
        for connector in self.connectors:
            connector.force_refresh = self.force_refresh

    def run(self, queries: list[str] | None = None) -> MarketSnapshot:
        queries = queries or build_default_queries(self.role_targets)
        collected: list[JobListing] = []
        errors: list[str] = []
        max_workers = max(1, min(self.settings.max_concurrent_requests, len(self.connectors)))
        if max_workers <= 1:
            for connector in self.connectors:
                try:
                    collected.extend(connector.search(queries))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{connector.source}: {exc}")
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(connector.search, queries): connector
                    for connector in self.connectors
                }
                for future in as_completed(future_map):
                    connector = future_map[future]
                    try:
                        collected.extend(future.result())
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{connector.source}: {exc}")

        deduped = self._dedupe_jobs(collected)
        analyzer = JobAnalyzer(self.role_targets)
        initially_scored = analyzer.score_jobs(deduped)
        self._enrich_details_by_relevance(initially_scored, errors)
        rescored = analyzer.score_jobs(initially_scored)
        filtered_jobs = self._filter_low_relevance_jobs(rescored, errors)
        skills = analyzer.summarize_skills(filtered_jobs)
        task_insights = analyzer.summarize_tasks(filtered_jobs)

        snapshot = MarketSnapshot(
            generated_at=now_iso(),
            queries=queries,
            role_targets=self.role_targets,
            jobs=filtered_jobs,
            skills=skills,
            task_insights=task_insights,
            errors=errors,
        )
        save_snapshot(snapshot, self.settings.snapshot_path)
        return snapshot

    def _enrich_details_by_relevance(
        self,
        jobs: list[JobListing],
        errors: list[str],
    ) -> None:
        for connector in self.connectors:
            source_jobs = [job for job in jobs if job.source == connector.source]
            if not source_jobs:
                continue
            source_jobs.sort(key=lambda item: item.relevance_score, reverse=True)
            if self.settings.max_detail_jobs_per_source > 0:
                source_jobs = source_jobs[: self.settings.max_detail_jobs_per_source]
            try:
                connector.enrich_details(source_jobs)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{connector.source} detail: {exc}")

    def _filter_low_relevance_jobs(
        self,
        jobs: list[JobListing],
        errors: list[str],
    ) -> list[JobListing]:
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
        deduped: dict[tuple[str, str], JobListing] = {}
        for job in jobs:
            key = (job.source, job.url or f"{job.title}|{job.company}|{job.location}")
            if key in deduped and len(job.description) < len(deduped[key].description):
                continue
            deduped[key] = job
        return list(deduped.values())
