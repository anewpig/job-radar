from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import load_settings
from job_spy_tw.connectors.linkedin import LinkedInConnector
from job_spy_tw.connectors.site_104 import Site104Connector
from job_spy_tw.models import JobListing
from job_spy_tw.utils import CachedFetcher


class ConnectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = load_settings(ROOT)
        self.fetcher = CachedFetcher(
            cache_dir=ROOT / "data" / "test-cache",
            timeout=5,
            delay_seconds=0,
            user_agent=self.settings.user_agent,
        )

    def test_104_json_parser_maps_fields(self) -> None:
        connector = Site104Connector(self.settings, self.fetcher)
        payload = {
            "data": [
                {
                    "jobName": "AI工程師",
                    "custName": "測試公司",
                    "jobAddrNoDesc": "台北市信義區",
                    "salaryDesc": "月薪60,000元以上",
                    "appearDate": "20260401",
                    "description": "需要 Python、LLM、RAG 經驗",
                    "descSnippet": "需要 Python、LLM、RAG 經驗",
                    "link": {"job": "https://www.104.com.tw/job/abc123"},
                    "tags": [{"label": "遠端工作"}],
                    "jobNo": "abc123",
                    "coIndustryDesc": "電腦軟體服務業",
                    "salaryLow": 60000,
                    "salaryHigh": 90000,
                }
            ]
        }
        jobs = connector.parse_search_page(json.dumps(payload), "AI工程師")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "AI工程師")
        self.assertEqual(jobs[0].company, "測試公司")
        self.assertEqual(jobs[0].location, "台北市信義區")
        self.assertIn("遠端工作", jobs[0].tags)

    def test_linkedin_card_parser_extracts_job(self) -> None:
        connector = LinkedInConnector(self.settings, self.fetcher)
        html = """
        <html>
          <body>
            <div class="base-card">
              <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/1234567890?position=1&pageNum=0"></a>
              <h3 class="base-search-card__title">AI Engineer</h3>
              <h4 class="base-search-card__subtitle">Example Corp</h4>
              <span class="job-search-card__location">Taipei, Taiwan</span>
              <time>1 day ago</time>
            </div>
          </body>
        </html>
        """
        jobs = connector.parse_search_page(html, "AI Engineer")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "AI Engineer")
        self.assertEqual(jobs[0].company, "Example Corp")
        self.assertEqual(jobs[0].location, "Taipei, Taiwan")

    def test_104_detail_payload_extracts_original_items(self) -> None:
        connector = Site104Connector(self.settings, self.fetcher)
        job = JobListing(
            source="104",
            title="AI應用工程師",
            company="測試公司",
            location="台北市",
            url="https://www.104.com.tw/job/abc123",
            metadata={"job_no": "abc123"},
        )
        payload = {
            "jobDetail": {
                "jobDescription": (
                    "1.企業 AI 應用導入與推行\n"
                    "規劃並推動企業內部 AI 專案\n"
                    "2.需求分析與跨部門協作\n"
                    "蒐集並分析業務單位需求"
                )
            },
            "condition": {
                "workExp": "3年以上",
                "edu": "碩士",
                "major": ["資訊管理相關"],
                "specialty": [],
                "skill": [],
                "certificate": [],
                "driverLicense": [],
                "language": [],
                "other": (
                    "1.具備企業 IT 或系統導入經驗\n"
                    "2.對生成式 AI 有實務理解\n"
                    "3.具備良好跨部門溝通與需求分析能力"
                ),
            },
        }

        connector._populate_detail_payload(job, payload)

        self.assertIn(
            "企業 AI 應用導入與推行：規劃並推動企業內部 AI 專案",
            job.work_content_items,
        )
        self.assertIn(
            "需求分析與跨部門協作：蒐集並分析業務單位需求",
            job.work_content_items,
        )
        self.assertIn("具備企業 IT 或系統導入經驗", job.required_skill_items)
        self.assertIn("對生成式 AI 有實務理解", job.required_skill_items)

    def test_linkedin_detail_parser_extracts_work_and_requirement_items(self) -> None:
        connector = LinkedInConnector(self.settings, self.fetcher)
        job = JobListing(
            source="LinkedIn",
            title="AI Engineer",
            company="Example Corp",
            location="Taipei, Taiwan",
            url="https://www.linkedin.com/jobs/view/1234567890",
        )
        html = """
        <html>
          <body>
            <div class="show-more-less-html__markup">
              <strong>Job Description</strong>
              <ul>
                <li>Build RAG applications for internal knowledge search.</li>
                <li>Collaborate with product and engineering teams.</li>
              </ul>
              <strong>Qualifications</strong>
              <ul>
                <li>3+ years of Python experience.</li>
                <li>Experience with LLM and prompt engineering.</li>
              </ul>
            </div>
          </body>
        </html>
        """

        connector.populate_job_details(job, html)

        self.assertIn(
            "Build RAG applications for internal knowledge search.",
            job.work_content_items,
        )
        self.assertIn(
            "Collaborate with product and engineering teams.",
            job.work_content_items,
        )
        self.assertIn("3+ years of Python experience.", job.requirement_items)
        self.assertIn(
            "Experience with LLM and prompt engineering.",
            job.required_skill_items,
        )


if __name__ == "__main__":
    unittest.main()
