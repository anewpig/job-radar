"""Connector implementation for cake job sources."""

from __future__ import annotations

import re
import time
from urllib.error import HTTPError
from urllib.parse import quote

from bs4 import BeautifulSoup, Tag

from ..detail_parsing import (
    extract_jobposting_description,
    merge_unique_items,
    select_requirement_like_items,
    split_structured_items,
)
from ..models import JobListing
from ..utils import (
    POSTED_AT_PATTERN,
    SALARY_PATTERN,
    TAIWAN_LOCATION_PATTERN,
    absolutize_url,
    first_match,
    normalize_text,
    strip_query_params,
)
from .base import BaseConnector


class CakeConnector(BaseConnector):
    source = "Cake"
    search_url_template = "https://www.cake.me/jobs/{query}?page={page}"
    job_href_pattern = re.compile(r"/companies/[^/]+/jobs/[^?#]+")
    retryable_status_codes = {403, 429}
    detail_keywords = (
        "Job Description",
        "Responsibilities",
        "Requirements",
        "Qualifications",
        "職缺描述",
        "工作內容",
        "條件要求",
    )

    WORK_SECTION_LABELS = (
        "job description",
        "description",
        "responsibilities",
        "what you'll do",
        "what you will do",
        "工作內容",
        "職缺描述",
        "主要職責",
    )
    REQUIREMENT_SECTION_LABELS = (
        "requirements",
        "qualifications",
        "skills",
        "must have",
        "preferred qualifications",
        "basic qualifications",
        "requirements / qualifications",
        "條件要求",
        "必要條件",
        "技能需求",
        "其他條件",
    )

    @property
    def base_url(self) -> str:
        return "https://www.cake.me"

    def search_delay_seconds(self) -> float:
        """Cake 搜尋頁使用保守一點的節流，降低 403 風險但保留速度。"""
        return max(0.22, float(self.settings.request_delay) * 0.70)

    def detail_delay_seconds(self) -> float:
        """Cake detail enrich 可比搜尋頁更積極。"""
        return max(0.08, float(self.settings.request_delay) * 0.22)

    def search_max_workers(self) -> int:
        """Cake 搜尋頁併發以 2 為上限，避免 page 1 多 query 同時觸發 403。"""
        return min(2, self.settings.max_concurrent_requests)

    def detail_max_workers(self) -> int:
        """Cake detail enrich 預設採中度併發。"""
        return min(3, self.settings.max_concurrent_requests)

    def fetch_search_page(self, query: str, page: int) -> str:
        """以較接近瀏覽器的 request context 抓取 Cake 搜尋頁，並在被擋時自動退避重試。"""
        encoded_query = quote(query.strip())
        url = self.search_url_template.format(query=encoded_query, page=page)
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": f"{self.base_url}/jobs",
            "Upgrade-Insecure-Requests": "1",
        }
        base_delay = self.search_delay_seconds()
        retry_delays = [
            base_delay,
            max(base_delay * 2, 0.75),
            max(base_delay * 4, 1.5),
        ]
        last_error: Exception | None = None

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

        if last_error is not None:
            raise last_error
        raise RuntimeError("Cake search failed without raising a concrete exception")

    def parse_search_page(self, html: str, query: str) -> list[JobListing]:
        soup = BeautifulSoup(html, "lxml")
        jobs: list[JobListing] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = absolutize_url(self.base_url, anchor.get("href", ""))
            if not self.job_href_pattern.search(href):
                continue

            title = normalize_text(anchor.get_text(" ", strip=True))
            if not self._looks_like_cake_title(title):
                continue

            url = strip_query_params(href)
            if not url or url in seen:
                continue
            seen.add(url)

            container = self._find_cake_container(anchor)
            text = normalize_text(container.get_text("\n", strip=True))
            if len(text) < max(24, len(title) + 8):
                continue

            company = self._extract_company(container, title, url) or "未提供公司名稱"
            location = first_match(TAIWAN_LOCATION_PATTERN, text)
            salary = self._extract_salary(text)
            posted_at = first_match(POSTED_AT_PATTERN, text)
            summary = self._build_summary(text=text, title=title, company=company)

            jobs.append(
                JobListing(
                    source=self.source,
                    title=title,
                    company=company,
                    location=location,
                    salary=salary,
                    posted_at=posted_at,
                    url=url,
                    summary=summary,
                    metadata={"query": query},
                )
            )
        return jobs

    def populate_job_details(self, job: JobListing, html: str) -> None:
        description = extract_jobposting_description(html) or self.extract_detail_text(html)
        soup = BeautifulSoup(html, "lxml")

        work_text = self._extract_section_from_text(
            description,
            section_labels=self.WORK_SECTION_LABELS,
            stop_labels=self.REQUIREMENT_SECTION_LABELS,
        )
        requirement_text = self._extract_section_from_text(
            description,
            section_labels=self.REQUIREMENT_SECTION_LABELS,
            stop_labels=(
                "about us",
                "meet the hiring team",
                "interview process",
                "application",
                "apply now",
            ),
        )

        if not work_text:
            work_text = self._extract_heading_section_text(
                soup,
                headings=self.WORK_SECTION_LABELS,
                stop_headings=self.REQUIREMENT_SECTION_LABELS,
            )
        if not requirement_text:
            requirement_text = self._extract_heading_section_text(
                soup,
                headings=self.REQUIREMENT_SECTION_LABELS,
                stop_headings=(
                    "about us",
                    "meet the hiring team",
                    "interview process",
                    "application",
                    "apply now",
                ),
            )

        work_items = merge_unique_items(
            split_structured_items(work_text),
            self._extract_inline_numbered_items(work_text),
        )
        requirement_items = merge_unique_items(
            split_structured_items(requirement_text),
            self._extract_inline_numbered_items(requirement_text),
        )
        required_skill_items = select_requirement_like_items(requirement_items)
        if not required_skill_items:
            required_skill_items = merge_unique_items(requirement_items)

        if not requirement_items and work_items:
            requirement_items = select_requirement_like_items(work_items)
            work_items = [item for item in work_items if item not in set(requirement_items)]
            required_skill_items = merge_unique_items(requirement_items)

        job.description = normalize_text(description) or job.description
        job.work_content_items = work_items
        job.requirement_items = requirement_items
        job.required_skill_items = required_skill_items
        job.detail_sections = {
            "work_content": work_text,
            "requirements": requirement_text,
            "required_skills": "\n".join(required_skill_items),
        }

    def _looks_like_cake_title(self, title: str) -> bool:
        if len(title) < 2 or len(title) > 140:
            return False
        lowered = title.lower()
        rejected = {
            "apply now",
            "save",
            "share",
            "view all jobs",
            "更多職缺",
            "看更多職缺",
        }
        if lowered in rejected:
            return False
        if any(marker in lowered for marker in ("apply now", "save job", "share job")):
            return False
        return True

    def _is_retryable_search_error(self, exc: Exception) -> bool:
        """判斷 Cake 搜尋錯誤是否值得以更慢的節奏重試。"""
        status_code = getattr(exc, "code", None)
        if status_code in self.retryable_status_codes:
            return True
        if isinstance(exc, HTTPError) and exc.code in self.retryable_status_codes:
            return True
        message = str(exc)
        return any(code in message for code in (" 403", " 429", "Error 403", "Error 429"))

    def _find_cake_container(self, anchor: Tag) -> Tag:
        current: Tag | None = anchor
        while current is not None:
            text = normalize_text(current.get_text(" ", strip=True))
            if 80 <= len(text) <= 2200:
                return current
            current = current.parent if isinstance(current.parent, Tag) else None
        return anchor

    def _extract_company(self, container: Tag, title: str, url: str) -> str:
        for candidate in container.find_all("a", href=True):
            href = candidate.get("href", "")
            text = normalize_text(candidate.get_text(" ", strip=True))
            if not text or text == title or len(text) > 60:
                continue
            if "/companies/" in href and "/jobs/" not in href:
                return text

        fallback = self._guess_company(container=container, title=title)
        if fallback:
            return fallback

        match = re.search(r"/companies/([^/]+)/jobs/", url)
        if not match:
            return ""
        slug = match.group(1).replace("-", " ")
        return normalize_text(slug.title())

    def _extract_section_from_text(
        self,
        text: str,
        *,
        section_labels: tuple[str, ...],
        stop_labels: tuple[str, ...],
    ) -> str:
        if not text:
            return ""
        prepared = normalize_text(str(text))
        escaped_labels = "|".join(re.escape(label) for label in section_labels)
        escaped_stops = "|".join(re.escape(label) for label in stop_labels)
        pattern = re.compile(
            rf"(?:{escaped_labels})\s*:?\s*(.+?)(?=(?:{escaped_stops})\s*:?\s*|$)",
            re.IGNORECASE,
        )
        match = pattern.search(prepared)
        return normalize_text(match.group(1)) if match else ""

    def _extract_heading_section_text(
        self,
        soup: BeautifulSoup,
        *,
        headings: tuple[str, ...],
        stop_headings: tuple[str, ...],
    ) -> str:
        heading_tag = soup.find(
            lambda tag: tag.name in {"h2", "h3", "h4"}
            and normalize_text(tag.get_text(" ", strip=True)).lower().rstrip(":") in headings
        )
        if not heading_tag:
            return ""

        chunks: list[str] = []
        for sibling in heading_tag.find_next_siblings():
            if not isinstance(sibling, Tag):
                continue
            if sibling.name in {"h2", "h3", "h4"}:
                heading_text = normalize_text(sibling.get_text(" ", strip=True)).lower().rstrip(":")
                if heading_text in stop_headings or heading_text not in headings:
                    break
            text = normalize_text(sibling.get_text("\n", strip=True))
            if text:
                chunks.append(text)
        return "\n".join(chunks).strip()

    def _extract_salary(self, text: str) -> str:
        salary = first_match(SALARY_PATTERN, text)
        if salary:
            return salary
        match = re.search(
            r"(月薪[^。；;\n]{0,24}|年薪[^。；;\n]{0,24}|時薪[^。；;\n]{0,24}|待遇面議)",
            text,
        )
        return normalize_text(match.group(1)) if match else ""

    def _extract_inline_numbered_items(self, text: str) -> list[str]:
        if not text:
            return []
        matches = re.findall(
            r"(?:^|\s)\d{1,2}[.)、．]\s*(.+?)(?=(?:\s\d{1,2}[.)、．]\s)|$)",
            normalize_text(text),
        )
        return [normalize_text(item) for item in matches if normalize_text(item)]
