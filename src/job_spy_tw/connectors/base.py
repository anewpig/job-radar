from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from abc import ABC, abstractmethod
from typing import Iterable
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, Tag

from ..config import Settings
from ..models import JobListing
from ..utils import (
    POSTED_AT_PATTERN,
    SALARY_PATTERN,
    TAIWAN_LOCATION_PATTERN,
    CachedFetcher,
    absolutize_url,
    first_match,
    normalize_text,
    strip_query_params,
)


class BaseConnector(ABC):
    source: str
    search_url_template: str
    job_href_pattern: re.Pattern[str]
    detail_keywords: tuple[str, ...] = ()
    search_url_suffix: str = ""

    def __init__(self, settings: Settings, fetcher: CachedFetcher) -> None:
        self.settings = settings
        self.fetcher = fetcher
        self.force_refresh = False

    def search(self, queries: Iterable[str]) -> list[JobListing]:
        results: list[JobListing] = []
        for query in queries:
            for page in range(1, self.settings.max_pages_per_source + 1):
                html = self.fetch_search_page(query=query, page=page)
                parsed = self.parse_search_page(html=html, query=query)
                results.extend(parsed)
        return self._dedupe(results)

    def fetch_search_page(self, query: str, page: int) -> str:
        url = self.search_url_template.format(
            query=quote_plus(query),
            location=quote_plus(self.settings.location),
            page=page,
        )
        if self.search_url_suffix:
            url = f"{url}{self.search_url_suffix}"
        return self.fetcher.fetch(url, force_refresh=self.force_refresh)

    def parse_search_page(self, html: str, query: str) -> list[JobListing]:
        soup = BeautifulSoup(html, "lxml")
        records: list[JobListing] = []
        seen_urls: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = absolutize_url(self.base_url, anchor["href"])
            if not self.job_href_pattern.search(href):
                continue
            title = normalize_text(anchor.get_text(" ", strip=True))
            if not self._looks_like_job_title(title):
                continue

            canonical_url = strip_query_params(href)
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)

            container = self._find_container(anchor)
            text = normalize_text(container.get_text(" ", strip=True))
            if not self._looks_like_job_text(text, title):
                continue

            company = self._guess_company(container=container, title=title)
            location = first_match(TAIWAN_LOCATION_PATTERN, text)
            salary = first_match(SALARY_PATTERN, text)
            posted_at = first_match(POSTED_AT_PATTERN, text)
            summary = self._build_summary(text=text, title=title, company=company)
            records.append(
                JobListing(
                    source=self.source,
                    title=title,
                    company=company or "未提供公司名稱",
                    location=location,
                    salary=salary,
                    posted_at=posted_at,
                    summary=summary,
                    url=canonical_url,
                    metadata={"query": query},
                )
            )
        return records

    def enrich_details(self, jobs: list[JobListing]) -> list[JobListing]:
        detail_jobs = jobs
        if self.settings.max_detail_jobs_per_source > 0:
            detail_jobs = jobs[: self.settings.max_detail_jobs_per_source]

        max_workers = max(1, min(self.settings.max_concurrent_requests, len(detail_jobs)))
        if max_workers <= 1:
            for job in detail_jobs:
                self._populate_job_detail(job)
            return jobs

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._populate_job_detail, job) for job in detail_jobs]
            for future in as_completed(futures):
                future.result()
        return jobs

    def _populate_job_detail(self, job: JobListing) -> None:
        try:
            html = self.fetcher.fetch(job.url, force_refresh=self.force_refresh)
        except Exception as exc:  # noqa: BLE001
            job.metadata["detail_error"] = str(exc)
            return
        self.populate_job_details(job, html)

    def populate_job_details(self, job: JobListing, html: str) -> None:
        detail_text = self.extract_detail_text(html)
        if detail_text:
            job.description = detail_text

    def extract_detail_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        scored_nodes: list[tuple[float, str]] = []
        for tag in soup.find_all(["main", "article", "section", "div"]):
            if not isinstance(tag, Tag):
                continue
            text = normalize_text(tag.get_text(" ", strip=True))
            if len(text) < 180 or len(text) > 6000:
                continue
            keyword_score = sum(4 for keyword in self.detail_keywords if keyword in text)
            length_score = min(len(text) / 400, 8)
            heading_score = 3 if any(h in text for h in ("工作內容", "職缺描述", "Qualifications", "Description")) else 0
            total = keyword_score + length_score + heading_score
            if total:
                scored_nodes.append((total, text))

        if scored_nodes:
            scored_nodes.sort(key=lambda item: item[0], reverse=True)
            return scored_nodes[0][1]
        return normalize_text(soup.get_text(" ", strip=True))[:2000]

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError

    def _find_container(self, anchor: Tag) -> Tag:
        current: Tag | None = anchor
        while current is not None:
            text = normalize_text(current.get_text(" ", strip=True))
            if 80 <= len(text) <= 2500 and anchor.get_text(" ", strip=True) in text:
                return current
            current = current.parent if isinstance(current.parent, Tag) else None
        return anchor

    def _guess_company(self, container: Tag, title: str) -> str:
        candidates: list[str] = []
        for candidate in container.find_all(["a", "span", "div", "p"]):
            text = normalize_text(candidate.get_text(" ", strip=True))
            if not text or text == title or len(text) > 40:
                continue
            if self._is_noise_text(text):
                continue
            candidates.append(text)
        return candidates[0] if candidates else ""

    def _build_summary(self, text: str, title: str, company: str) -> str:
        summary = text
        for value in (title, company):
            if value:
                summary = summary.replace(value, "")
        summary = re.sub(r"(儲存|應徵|立即加入|登入|加入 LinkedIn)", " ", summary)
        summary = normalize_text(summary)
        return summary[:320]

    def _looks_like_job_title(self, title: str) -> bool:
        if len(title) < 2 or len(title) > 120:
            return False
        lowered = title.lower()
        rejected = {
            "登入",
            "立即加入",
            "找工作",
            "更多職缺",
            "前往內容",
            "linkedin",
            "image",
        }
        if title in rejected:
            return False
        return any(token in lowered for token in self.title_tokens)

    def _looks_like_job_text(self, text: str, title: str) -> bool:
        lowered = text.lower()
        if title not in text:
            return False
        if len(text) < len(title) + 20:
            return False
        return any(
            marker in lowered or marker in text
            for marker in ("工程師", "manager", "應徵", "職缺", "salary", "待遇", "工作內容")
        )

    def _is_noise_text(self, text: str) -> bool:
        lowered = text.lower()
        noise_markers = (
            "應徵",
            "儲存",
            "完成",
            "登入",
            "清除文字",
            "更多",
            "個新職缺",
            "image",
            "input",
            "done",
            "搜尋",
        )
        if any(marker.lower() in lowered for marker in noise_markers):
            return True
        if SALARY_PATTERN.search(text) or POSTED_AT_PATTERN.search(text):
            return True
        if TAIWAN_LOCATION_PATTERN.fullmatch(text):
            return True
        return False

    @property
    def title_tokens(self) -> tuple[str, ...]:
        return (
            "engineer",
            "工程師",
            "manager",
            "經理",
            "pm",
            "developer",
            "scientist",
        )

    def _dedupe(self, jobs: list[JobListing]) -> list[JobListing]:
        deduped: dict[tuple[str, str], JobListing] = {}
        for job in jobs:
            key = (job.source, job.url)
            deduped[key] = job
        return list(deduped.values())
