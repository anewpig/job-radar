from __future__ import annotations

import re

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

    @property
    def base_url(self) -> str:
        return "https://www.1111.com.tw"

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
