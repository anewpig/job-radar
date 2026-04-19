"""Connector implementation for 104 job sources."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from urllib.error import HTTPError
from urllib.parse import quote_plus

from ..detail_parsing import merge_unique_items, select_requirement_like_items, split_structured_items
from ..models import JobListing
from ..utils import normalize_text
from .base import BaseConnector


class Site104Connector(BaseConnector):
    source = "104"
    search_url_template = (
        "https://www.104.com.tw/jobs/search/api/jobs?keyword={query}&page={page}"
    )
    operation_announcement_url = "https://www.104.com.tw/js/operation-announcement.js"
    operation_time_pattern = re.compile(r'window\.OPERATION_TIME\s*=\s*"([^"]*)"')
    job_href_pattern = re.compile(r"/job/[A-Za-z0-9]+")
    detail_keywords = ("工作內容", "條件要求", "職務類別", "工作待遇", "技能")

    @property
    def base_url(self) -> str:
        return "https://www.104.com.tw"

    def search_delay_seconds(self) -> float:
        """104 搜尋 API 可承受較積極的節流設定。"""
        return max(0.08, float(self.settings.request_delay) * 0.30)

    def detail_delay_seconds(self) -> float:
        """104 detail API 通常比搜尋 API 更穩，可再更積極一點。"""
        return max(0.05, float(self.settings.request_delay) * 0.12)

    def search_max_workers(self) -> int:
        """104 搜尋頁預設允許較高併發，以縮短首批結果等待時間。"""
        return min(4, self.settings.max_concurrent_requests)

    def detail_max_workers(self) -> int:
        """104 detail enrich 預設使用更高併發。"""
        return min(6, self.settings.max_concurrent_requests)

    def fetch_search_page(self, query: str, page: int) -> str:
        url = self.search_url_template.format(
            query=quote_plus(query), page=page, location=""
        )
        try:
            return self.fetcher.fetch(
                url,
                force_refresh=self.force_refresh,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.104.com.tw/jobs/search/",
                },
                delay_seconds=self.search_delay_seconds(),
                cache_ttl_seconds=self.search_cache_ttl_seconds(),
            )
        except HTTPError as exc:
            raise self._translate_http_error(exc, phase="search") from exc

    def parse_search_page(self, html: str, query: str) -> list[JobListing]:
        payload = json.loads(html)
        jobs: list[JobListing] = []
        for item in payload.get("data", []):
            link = (item.get("link") or {}).get("job", "")
            job_code = self._extract_job_no(link)
            description = normalize_text(item.get("description", ""))
            summary = normalize_text(item.get("descSnippet", "")) or description[:320]
            tags = [
                normalize_text(tag.get("label", ""))
                for tag in item.get("tags", [])
                if isinstance(tag, dict)
            ]
            salary = normalize_text(item.get("salaryDesc", "")) or self._format_salary_range(
                item.get("salaryLow"),
                item.get("salaryHigh"),
            )
            jobs.append(
                JobListing(
                    source=self.source,
                    title=normalize_text(item.get("jobName", "")),
                    company=normalize_text(item.get("custName", "")) or "未提供公司名稱",
                    location=normalize_text(item.get("jobAddrNoDesc", "")),
                    salary=salary,
                    posted_at=normalize_text(item.get("appearDate", "")),
                    url=link,
                    summary=summary,
                    description=description,
                    tags=[tag for tag in tags if tag],
                    metadata={
                        "query": query,
                        "job_no": item.get("jobNo"),
                        "job_code": job_code,
                        "industry": item.get("coIndustryDesc"),
                        "salary_low": item.get("salaryLow"),
                        "salary_high": item.get("salaryHigh"),
                    },
                )
            )
        return jobs

    @staticmethod
    def _format_salary_range(low: object, high: object) -> str:
        low_value = int(low or 0)
        high_value = int(high or 0)
        if low_value <= 0 and high_value <= 0:
            return ""

        unit = "年薪" if max(low_value, high_value) >= 300_000 else "月薪"
        if high_value >= 9_999_999 and low_value > 0:
            return f"{unit} {low_value:,} 元以上"
        if low_value > 0 and high_value > 0:
            if low_value == high_value:
                return f"{unit} {low_value:,} 元"
            return f"{unit} {low_value:,} - {high_value:,} 元"
        if low_value > 0:
            return f"{unit} {low_value:,} 元以上"
        return f"{unit}最高 {high_value:,} 元"

    def enrich_details(self, jobs: list[JobListing]) -> list[JobListing]:
        detail_jobs = jobs
        if self.settings.max_detail_jobs_per_source > 0:
            detail_jobs = jobs[: self.settings.max_detail_jobs_per_source]

        max_workers = max(1, min(self.detail_max_workers(), len(detail_jobs)))
        if max_workers <= 1:
            for job in detail_jobs:
                self._populate_detail_job(job)
            return jobs

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._populate_detail_job, job) for job in detail_jobs]
            for future in as_completed(futures):
                future.result()
        return jobs

    def _populate_detail_job(self, job: JobListing) -> None:
        job_code = (
            str(job.metadata.get("job_code", "")).strip()
            or self._extract_job_no(job.url)
        )
        if not job_code:
            return
        detail_url = f"{self.base_url}/job/ajax/content/{job_code}"
        try:
            detail_payload = self.fetcher.fetch(
                detail_url,
                force_refresh=self.force_refresh,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": job.url or f"{self.base_url}/job/{job_code}",
                },
                delay_seconds=self.detail_delay_seconds(),
                cache_ttl_seconds=self.detail_cache_ttl_seconds(),
            )
            payload = json.loads(detail_payload)
        except HTTPError as exc:
            job.metadata["detail_error"] = str(self._translate_http_error(exc, phase="detail"))
            return
        except Exception as exc:  # noqa: BLE001
            job.metadata["detail_error"] = str(exc)
            return

        self._populate_detail_payload(job, payload.get("data", {}))
        job.metadata["detail_enriched"] = True

    def _populate_detail_payload(self, job: JobListing, payload: dict) -> None:
        job_detail = payload.get("jobDetail", {})
        condition = payload.get("condition", {})
        work_description = str(job_detail.get("jobDescription", "") or "")
        work_items = split_structured_items(work_description)

        requirement_items: list[str] = []
        for label, value in (
            ("工作經歷", condition.get("workExp")),
            ("學歷要求", condition.get("edu")),
            ("科系要求", "、".join(condition.get("major", []) or [])),
        ):
            normalized = normalize_text(str(value or ""))
            if normalized and normalized != "不拘":
                requirement_items.append(f"{label}：{normalized}")

        language_items = self._format_language_items(condition.get("language", []))
        specialty_items = self._flatten_condition_values(condition.get("specialty", []))
        skill_items = self._flatten_condition_values(condition.get("skill", []))
        certificate_items = self._flatten_condition_values(condition.get("certificate", []))
        driver_license_items = self._flatten_condition_values(condition.get("driverLicense", []))
        other_text = str(condition.get("other", "") or "")
        other_items = split_structured_items(other_text)

        requirement_items = merge_unique_items(
            requirement_items,
            language_items,
            [f"擅長工具：{item}" for item in specialty_items],
            [f"工作技能：{item}" for item in skill_items],
            [f"具備證照：{item}" for item in certificate_items],
            [f"具備駕照：{item}" for item in driver_license_items],
            other_items,
        )
        required_skill_items = merge_unique_items(
            specialty_items,
            skill_items,
            certificate_items,
            driver_license_items,
            select_requirement_like_items(other_items),
        )

        job.description = normalize_text(work_description) or job.description
        job.work_content_items = work_items
        job.requirement_items = requirement_items
        job.required_skill_items = required_skill_items
        job.detail_sections = {
            "work_content": work_description,
            "requirements": "\n".join(requirement_items),
            "required_skills": "\n".join(required_skill_items),
        }

    def _extract_job_no(self, url: str) -> str:
        match = re.search(r"/job/([A-Za-z0-9]+)", url)
        return match.group(1) if match else ""

    def _flatten_condition_values(self, values) -> list[str]:
        flattened: list[str] = []
        for value in values or []:
            if isinstance(value, str):
                normalized = normalize_text(value)
            elif isinstance(value, dict):
                normalized = normalize_text(
                    str(
                        value.get("description")
                        or value.get("name")
                        or value.get("label")
                        or value.get("text")
                        or ""
                    )
                )
            else:
                normalized = normalize_text(str(value))
            if normalized and normalized != "不拘":
                flattened.append(normalized)
        return flattened

    def _format_language_items(self, values) -> list[str]:
        items: list[str] = []
        for value in values or []:
            if not isinstance(value, dict):
                continue
            language_name = normalize_text(
                str(value.get("description") or value.get("language") or "")
            )
            abilities = value.get("ability") or {}
            ability_parts = [
                f"{label}{normalize_text(str(abilities.get(key, '')))}"
                for key, label in (
                    ("listening", "聽"),
                    ("speaking", "說"),
                    ("reading", "讀"),
                    ("writing", "寫"),
                )
                if normalize_text(str(abilities.get(key, "")))
            ]
            joined = " / ".join(ability_parts)
            if language_name and joined:
                items.append(f"語文條件：{language_name}（{joined}）")
            elif language_name:
                items.append(f"語文條件：{language_name}")
        return items

    def _translate_http_error(self, exc: HTTPError, *, phase: str) -> Exception:
        if exc.code != 404:
            return exc

        maintenance_window = self._fetch_operation_time()
        if maintenance_window:
            return RuntimeError(
                f"104 {phase} 目前顯示維護公告，維護時段為 {maintenance_window}"
            )
        return RuntimeError(f"104 {phase} 目前回傳公告頁或維護頁，暫時無法抓取")

    def _fetch_operation_time(self) -> str:
        try:
            script = self.fetcher.fetch(
                self.operation_announcement_url,
                force_refresh=True,
                headers={
                    "Accept": "*/*",
                    "Referer": self.base_url,
                },
                delay_seconds=0,
                cache_ttl_seconds=300,
            )
        except Exception:  # noqa: BLE001
            return ""

        match = self.operation_time_pattern.search(script)
        if not match:
            return ""
        return normalize_text(match.group(1))
