"""Connector implementation for 1111 job sources."""

from __future__ import annotations

import re
import time
from urllib.error import HTTPError
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from ..detail_parsing import (
    extract_jobposting_description,
    extract_labeled_section,
    merge_unique_items,
    split_structured_items,
)
from ..models import JobListing
from ..utils import normalize_text
from .base import BaseConnector


class Site1111Connector(BaseConnector):
    source = "1111"
    search_url_template = "https://www.1111.com.tw/search/job?ks={query}&page={page}"
    job_href_pattern = re.compile(r"/job/\d+/?")
    detail_keywords = ("工作內容", "職缺描述", "要求條件", "工作待遇", "工作技能")
    retryable_status_codes = {403, 429, 449}

    @property
    def base_url(self) -> str:
        return "https://www.1111.com.tw"

    def search_delay_seconds(self) -> float:
        """1111 搜尋頁節流必須保守，避免過快觸發 449。"""
        return max(0.45, float(self.settings.request_delay) * 1.25)

    def detail_delay_seconds(self) -> float:
        """1111 detail enrich 仍保守，但比搜尋頁稍快。"""
        return max(0.22, float(self.settings.request_delay) * 0.60)

    def search_max_workers(self) -> int:
        """1111 搜尋頁對並發較敏感，預設使用較保守的搜尋併發。"""
        return min(2, self.settings.max_concurrent_requests)

    def detail_max_workers(self) -> int:
        """1111 detail enrich 同樣使用較保守的併發。"""
        return min(2, self.settings.max_concurrent_requests)

    def fetch_search_page(self, query: str, page: int) -> str:
        """以較接近瀏覽器的 request context 抓取 1111 搜尋頁，並在被擋時自動退避重試。"""
        url = self.search_url_template.format(query=quote_plus(query), page=page)
        referer = f"{self.base_url}/search/job"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": referer,
            "Upgrade-Insecure-Requests": "1",
        }
        base_delay = self.search_delay_seconds()
        retry_delays = [
            base_delay,
            max(base_delay * 2, 1.1),
            max(base_delay * 4, 2.2),
            max(base_delay * 6, 3.0),
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
        raise RuntimeError("1111 search failed without raising a concrete exception")

    def populate_job_details(self, job: JobListing, html: str) -> None:
        description = extract_jobposting_description(html)
        work_content = extract_labeled_section(
            description,
            "【工作內容】",
            ["；【工作制度/性質】", "；【要求條件】"],
        )
        requirement_summary = extract_labeled_section(
            description,
            "【要求條件】",
            ["；【福利制度】", "；【職務需求】"],
        )

        soup = BeautifulSoup(html, "lxml")
        skill_text = self._extract_heading_section_text(soup, "工作技能")
        extra_text = self._extract_heading_section_text(soup, "附加條件")

        work_items = split_structured_items(work_content)
        extra_items = split_structured_items(extra_text)
        skill_items = split_structured_items(skill_text)
        requirement_items = merge_unique_items(
            split_structured_items(requirement_summary),
            extra_items,
        )
        required_skill_items = merge_unique_items(skill_items, extra_items)

        job.description = normalize_text(description) or self.extract_detail_text(html)
        job.work_content_items = work_items
        job.requirement_items = requirement_items
        job.required_skill_items = required_skill_items
        job.detail_sections = {
            "work_content": work_content,
            "requirements": requirement_summary,
            "required_skills": "\n".join(required_skill_items),
        }

    def _extract_heading_section_text(self, soup: BeautifulSoup, heading: str) -> str:
        heading_tag = soup.find(
            lambda tag: tag.name in {"h2", "h3", "h4"}
            and normalize_text(tag.get_text(" ", strip=True)) == heading
        )
        if not heading_tag:
            return ""

        sibling = heading_tag.find_next_sibling()
        if sibling:
            text = sibling.get_text("\n", strip=True)
        else:
            text = heading_tag.parent.get_text("\n", strip=True)
        text = text.replace(heading, "", 1)
        text = text.replace("展開全部", "").replace("收合內容", "")
        return text.strip()

    def _is_retryable_search_error(self, exc: Exception) -> bool:
        """判斷 1111 搜尋錯誤是否值得以更慢的節奏重試。"""
        status_code = getattr(exc, "code", None)
        if status_code in self.retryable_status_codes:
            return True
        if isinstance(exc, HTTPError) and exc.code in self.retryable_status_codes:
            return True
        message = str(exc)
        return any(code in message for code in (" 403", " 429", " 449", "Error 403", "Error 429", "Error 449"))
