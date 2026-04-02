from __future__ import annotations

import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, Tag

from ..detail_parsing import merge_unique_items, select_requirement_like_items, split_structured_items
from ..models import JobListing
from ..utils import absolutize_url, normalize_text, strip_query_params
from .base import BaseConnector


class LinkedInConnector(BaseConnector):
    source = "LinkedIn"
    search_url_template = "https://tw.linkedin.com/jobs/search?keywords={query}&location={location}"
    job_href_pattern = re.compile(r"/jobs/view/\d+")
    detail_keywords = ("About the job", "Description", "Responsibilities", "Qualifications")

    @property
    def base_url(self) -> str:
        return "https://www.linkedin.com"

    def fetch_search_page(self, query: str, page: int) -> str:
        start = max(page - 1, 0) * 25
        location = self.settings.location
        if location in {"台灣", "臺灣"}:
            location = "Taiwan"
        url = (
            f"https://tw.linkedin.com/jobs/search?keywords={quote_plus(query)}"
            f"&location={quote_plus(location)}&start={start}"
        )
        return self.fetcher.fetch(url, force_refresh=self.force_refresh)

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
