"""Connector implementation for linkedin job sources."""

from __future__ import annotations

import hashlib
import re
import time
from urllib.error import HTTPError
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, Tag

from ..detail_parsing import merge_unique_items, select_requirement_like_items, split_structured_items
from ..models import JobListing
from ..utils import absolutize_url, normalize_text, strip_query_params
from .base import BaseConnector


class LinkedInConnector(BaseConnector):
    source = "LinkedIn"
    search_url_template = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        "?keywords={query}&location={location}"
    )
    job_href_pattern = re.compile(r"/jobs/view/\d+")
    retryable_status_codes = {403, 429, 999}
    detail_keywords = ("About the job", "Description", "Responsibilities", "Qualifications")

    def __init__(self, settings, fetcher) -> None:
        super().__init__(settings=settings, fetcher=fetcher)
        self._blocked_until = 0.0

    @property
    def base_url(self) -> str:
        return "https://www.linkedin.com"

    def search_delay_seconds(self) -> float:
        """LinkedIn 搜尋頁使用更保守的節流，降低 guest search 被限流的機率。"""
        return max(0.55, float(self.settings.request_delay) * 1.25)

    def detail_delay_seconds(self) -> float:
        """LinkedIn detail enrich 比搜尋頁更積極，但仍保守。"""
        return max(0.12, float(self.settings.request_delay) * 0.35)

    def search_max_workers(self) -> int:
        """LinkedIn 搜尋頁僅使用單工搜尋，降低多 query 連續觸發 request denied。"""
        return min(1, self.settings.max_concurrent_requests)

    def detail_max_workers(self) -> int:
        """LinkedIn detail enrich 預設使用較低併發。"""
        return min(2, self.settings.max_concurrent_requests)

    def fetch_search_page(self, query: str, page: int) -> str:
        """以較接近瀏覽器的 request context 抓取 LinkedIn 搜尋頁，並在被擋時自動退避重試。"""
        if self._blocked_until and time.monotonic() < self._blocked_until:
            remaining = int(max(0.0, self._blocked_until - time.monotonic()))
            self.last_errors.append(
                f"{self.source} search {query} p{page}: LinkedIn 暫時退避中，"
                f"{remaining} 秒後再嘗試。"
            )
            return ""
        candidate_urls = self._build_search_urls(query=query, page=page)
        cache_lookup_urls = self._build_cache_lookup_urls(query=query, page=page)
        search_referer = self._build_canonical_search_url(query=query, page=page)
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Origin": "https://www.linkedin.com",
            "Pragma": "no-cache",
            "Referer": search_referer,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        base_delay = self.search_delay_seconds()
        retry_delays = [
            base_delay,
            max(base_delay * 2, 1.5),
            max(base_delay * 4, 3.0),
            max(base_delay * 6, 5.0),
        ]
        last_error: Exception | None = None

        for url in candidate_urls:
            for attempt_index, delay_seconds in enumerate(retry_delays, start=1):
                try:
                    return self.fetcher.fetch(
                        url,
                        force_refresh=self.force_refresh,
                        headers=headers,
                        delay_seconds=delay_seconds,
                        cache_ttl_seconds=self.search_cache_ttl_seconds(),
                    )
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    if not self._is_retryable_search_error(exc):
                        raise
                    if attempt_index >= len(retry_delays):
                        break
                    time.sleep(delay_seconds)

        cached_html = self._load_cached_search_page(cache_lookup_urls)
        if cached_html:
            return cached_html
        if last_error is not None and self._is_retryable_search_error(last_error):
            if self._should_enter_cooldown(last_error):
                self._enter_cooldown()
            self.last_errors.append(
                f"{self.source} search {query} p{page}: LinkedIn guest search 暫時拒絕此頁，已略過。"
            )
            return ""
        if last_error is not None:
            raise last_error
        raise RuntimeError("LinkedIn search failed without raising a concrete exception")

    def parse_search_page(self, html: str, query: str) -> list[JobListing]:
        soup = BeautifulSoup(html, "lxml")
        jobs: list[JobListing] = []
        seen: set[str] = set()
        for card in soup.select("div.base-card"):
            link_tag = card.select_one("a.base-card__full-link[href]")
            title_tag = card.select_one("h3.base-search-card__title")
            company_tag = card.select_one("h4.base-search-card__subtitle")
            location_tag = card.select_one("span.job-search-card__location")
            time_tag = card.select_one("time")
            if not link_tag or not title_tag:
                continue

            url = strip_query_params(
                absolutize_url(self.base_url, link_tag.get("href", "")),
                keep={"position", "pageNum"},
            )
            if not url or url in seen:
                continue
            seen.add(url)

            summary = normalize_text(card.get_text(" ", strip=True))
            title = normalize_text(title_tag.get_text(" ", strip=True))
            company = normalize_text(company_tag.get_text(" ", strip=True)) or "未提供公司名稱"
            location = normalize_text(location_tag.get_text(" ", strip=True))
            posted_at = normalize_text(time_tag.get_text(" ", strip=True))
            jobs.append(
                JobListing(
                    source=self.source,
                    title=title,
                    company=company,
                    location=location,
                    posted_at=posted_at,
                    url=url,
                    summary=summary[:320],
                    metadata={"query": query},
                )
            )
        return jobs

    def extract_detail_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        selectors = (
            "div.show-more-less-html__markup",
            "div.description__text",
            "section.show-more-less-html",
        )
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = normalize_text(node.get_text(" ", strip=True))
                if text:
                    return text
        return super().extract_detail_text(html)

    def populate_job_details(self, job: JobListing, html: str) -> None:
        soup = BeautifulSoup(html, "lxml")
        node = soup.select_one("div.show-more-less-html__markup")
        if not node:
            super().populate_job_details(job, html)
            return

        section_map = self._extract_section_map(node)
        work_items = merge_unique_items(section_map["work"])
        requirement_items = merge_unique_items(section_map["requirements"])
        if not requirement_items:
            requirement_items = select_requirement_like_items(work_items)
            work_items = [item for item in work_items if item not in requirement_items]

        detail_text = normalize_text(node.get_text("\n", strip=True))
        job.description = detail_text
        job.work_content_items = work_items
        job.requirement_items = requirement_items
        job.required_skill_items = requirement_items
        job.detail_sections = {
            "work_content": "\n".join(work_items),
            "requirements": "\n".join(requirement_items),
            "required_skills": "\n".join(requirement_items),
        }

    def _extract_section_map(self, node: Tag) -> dict[str, list[str]]:
        work_headings = {
            "about the job",
            "job description",
            "responsibilities",
            "key responsibilities",
            "what you'll do",
            "what you will do",
            "工作內容",
            "主要職責",
        }
        requirement_headings = {
            "requirements",
            "qualifications",
            "preferred qualifications",
            "basic qualifications",
            "must have",
            "skills",
            "education",
            "work experience",
            "language",
            "requirements / qualifications",
        }

        section = "summary"
        buckets: dict[str, list[str]] = {"summary": [], "work": [], "requirements": []}

        for child in node.find_all(recursive=False):
            text = normalize_text(child.get_text("\n", strip=True))
            if not text:
                continue

            heading = text.lower().rstrip(":")
            if child.name in {"strong", "b", "h1", "h2", "h3", "h4"} and len(text) <= 80:
                if heading in work_headings:
                    section = "work"
                    continue
                if heading in requirement_headings:
                    section = "requirements"
                    continue

            if child.name == "ul":
                items = [
                    normalize_text(li.get_text(" ", strip=True))
                    for li in child.find_all("li", recursive=False)
                    if normalize_text(li.get_text(" ", strip=True))
                ]
            else:
                items = split_structured_items(text)

            if not items:
                continue
            if section == "requirements":
                buckets["requirements"].extend(items)
            elif section == "work":
                buckets["work"].extend(items)
            else:
                buckets["summary"].extend(items)

        if not buckets["work"]:
            buckets["work"] = buckets["summary"]
        return buckets

    def _is_retryable_search_error(self, exc: Exception) -> bool:
        """判斷 LinkedIn 搜尋錯誤是否值得以更慢的節奏重試。"""
        status_code = getattr(exc, "code", None)
        if status_code in self.retryable_status_codes:
            return True
        if isinstance(exc, HTTPError) and exc.code in self.retryable_status_codes:
            return True
        message = str(exc)
        return any(
            code in message
            for code in (
                " 403",
                " 429",
                " 999",
                "Error 403",
                "Error 429",
                "Error 999",
                "Request denied",
            )
        )

    def _should_enter_cooldown(self, exc: Exception) -> bool:
        status_code = getattr(exc, "code", None)
        if status_code in self.retryable_status_codes:
            return True
        message = str(exc)
        return any(
            token in message
            for token in (
                " 403",
                " 429",
                " 999",
                "Error 403",
                "Error 429",
                "Error 999",
                "Request denied",
            )
        )

    def _enter_cooldown(self) -> None:
        cooldown_seconds = max(0, int(self.settings.linkedin_cooldown_seconds))
        if cooldown_seconds <= 0:
            return
        self._blocked_until = time.monotonic() + cooldown_seconds

    def _build_search_urls(self, query: str, page: int) -> list[str]:
        start = max(page - 1, 0) * 25
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(self._search_location())
        return [
            (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={encoded_query}&location={encoded_location}&start={start}"
            ),
            (
                "https://www.linkedin.com/jobs/search"
                f"?keywords={encoded_query}&location={encoded_location}&start={start}"
            ),
        ]

    def _build_cache_lookup_urls(self, query: str, page: int) -> list[str]:
        start = max(page - 1, 0) * 25
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(self._search_location())
        cache_urls = list(self._build_search_urls(query=query, page=page))
        cache_urls.append(
            "https://tw.linkedin.com/jobs/search"
            f"?keywords={encoded_query}&location={encoded_location}&start={start}"
        )
        return cache_urls

    def _build_canonical_search_url(self, query: str, page: int) -> str:
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(self._search_location())
        start = max(page - 1, 0) * 25
        return (
            "https://www.linkedin.com/jobs/search"
            f"?keywords={encoded_query}&location={encoded_location}&start={start}"
        )

    def _search_location(self) -> str:
        location = self.settings.location
        if location in {"台灣", "臺灣"}:
            return "Taiwan"
        return location

    def _load_cached_search_page(self, urls: str | list[str]) -> str:
        """在 force refresh 被 LinkedIn 阻擋時，回退到既有快取避免整個來源空白。"""
        candidate_urls = [urls] if isinstance(urls, str) else list(urls)
        for url in candidate_urls:
            cache_path = self.fetcher.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.html"
            if cache_path.exists():
                return cache_path.read_text(encoding="utf-8")
        return ""
