"""Tests for connectors behavior."""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import load_settings
from job_spy_tw.connectors.cake import CakeConnector
from job_spy_tw.connectors.linkedin import LinkedInConnector
from job_spy_tw.connectors.site_104 import Site104Connector
from job_spy_tw.connectors.site_1111 import Site1111Connector
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
        self.assertEqual(jobs[0].salary, "月薪60,000元以上")

    def test_104_json_parser_uses_salary_low_high_when_salary_desc_missing(self) -> None:
        connector = Site104Connector(self.settings, self.fetcher)
        payload = {
            "data": [
                {
                    "jobName": "自動化工程師",
                    "custName": "測試公司",
                    "jobAddrNoDesc": "台中市",
                    "salaryDesc": "",
                    "appearDate": "20260401",
                    "description": "需要 PLC、OPC-UA 經驗",
                    "descSnippet": "需要 PLC、OPC-UA 經驗",
                    "link": {"job": "https://www.104.com.tw/job/xyz123"},
                    "tags": [],
                    "jobNo": "xyz123",
                    "coIndustryDesc": "自動化產業",
                    "salaryLow": 45000,
                    "salaryHigh": 80000,
                }
            ]
        }

        jobs = connector.parse_search_page(json.dumps(payload), "自動化工程師")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].salary, "月薪 45,000 - 80,000 元")

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

    def test_cake_card_parser_extracts_job(self) -> None:
        connector = CakeConnector(self.settings, self.fetcher)
        html = """
        <html>
          <body>
            <div class="job-card">
              <h3>
                <a href="/companies/example-corp/jobs/123456789-ai-application-engineer">
                  AI應用工程師
                </a>
              </h3>
              <a href="/companies/example-corp">Example Corp</a>
              <div>Taipei City, Taiwan</div>
              <div>月薪 60,000 ~ 90,000 元</div>
              <p>負責企業 AI 導入、流程自動化與跨部門協作。</p>
            </div>
          </body>
        </html>
        """

        jobs = connector.parse_search_page(html, "AI應用工程師")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "AI應用工程師")
        self.assertEqual(jobs[0].company, "Example Corp")
        self.assertEqual(jobs[0].location, "Taipei")
        self.assertIn("月薪", jobs[0].salary)

    def test_source_specific_speed_profiles_follow_expected_caps(self) -> None:
        connector_104 = Site104Connector(self.settings, self.fetcher)
        connector_1111 = Site1111Connector(self.settings, self.fetcher)
        connector_cake = CakeConnector(self.settings, self.fetcher)
        connector_linkedin = LinkedInConnector(self.settings, self.fetcher)

        self.assertEqual(connector_104.search_max_workers(), min(4, self.settings.max_concurrent_requests))
        self.assertEqual(connector_104.detail_max_workers(), min(6, self.settings.max_concurrent_requests))
        self.assertEqual(connector_1111.search_max_workers(), min(2, self.settings.max_concurrent_requests))
        self.assertEqual(connector_1111.detail_max_workers(), min(2, self.settings.max_concurrent_requests))
        self.assertEqual(connector_cake.search_max_workers(), min(2, self.settings.max_concurrent_requests))
        self.assertEqual(connector_linkedin.search_max_workers(), min(1, self.settings.max_concurrent_requests))
        self.assertGreaterEqual(connector_1111.search_delay_seconds(), 0.45)
        self.assertGreaterEqual(connector_104.search_delay_seconds(), 0.08)
        self.assertGreaterEqual(connector_cake.detail_delay_seconds(), 0.08)
        self.assertGreaterEqual(connector_linkedin.detail_delay_seconds(), 0.12)
        self.assertGreaterEqual(connector_linkedin.search_delay_seconds(), 0.55)

    def test_cake_search_retries_retryable_403_with_browser_headers(self) -> None:
        class RetryFetcher:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict[str, str] | None, float | None]] = []
                self.attempt = 0

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del cache_ttl_seconds
                self.attempt += 1
                self.calls.append((url, headers, delay_seconds))
                if self.attempt < 3:
                    raise HTTPError(url, 403, "Forbidden", hdrs=None, fp=None)
                return "<html></html>"

        fetcher = RetryFetcher()
        connector = CakeConnector(self.settings, fetcher)  # type: ignore[arg-type]

        with patch("job_spy_tw.connectors.cake.time.sleep") as mocked_sleep:
            html = connector.fetch_search_page("AI工程師", 1)

        self.assertEqual(html, "<html></html>")
        self.assertEqual(len(fetcher.calls), 3)
        self.assertEqual(fetcher.calls[0][0], "https://www.cake.me/jobs/AI%E5%B7%A5%E7%A8%8B%E5%B8%AB?page=1")
        self.assertIsNotNone(fetcher.calls[0][1])
        self.assertEqual(fetcher.calls[0][1]["Referer"], "https://www.cake.me/jobs")  # type: ignore[index]
        self.assertIn("text/html", fetcher.calls[0][1]["Accept"])  # type: ignore[index]
        self.assertGreaterEqual(mocked_sleep.call_count, 2)

    def test_linkedin_search_retries_retryable_429_with_browser_headers(self) -> None:
        class RetryFetcher:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict[str, str] | None, float | None]] = []
                self.attempt = 0

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del cache_ttl_seconds
                self.attempt += 1
                self.calls.append((url, headers, delay_seconds))
                if self.attempt < 3:
                    raise HTTPError(url, 429, "Request denied", hdrs=None, fp=None)
                return "<html></html>"

        fetcher = RetryFetcher()
        connector = LinkedInConnector(self.settings, fetcher)  # type: ignore[arg-type]

        with patch("job_spy_tw.connectors.linkedin.time.sleep") as mocked_sleep:
            html = connector.fetch_search_page("韌體工程師", 1)

        self.assertEqual(html, "<html></html>")
        self.assertEqual(len(fetcher.calls), 3)
        self.assertIn("linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search", fetcher.calls[0][0])
        self.assertIsNotNone(fetcher.calls[0][1])
        self.assertEqual(
            fetcher.calls[0][1]["Referer"],  # type: ignore[index]
            "https://www.linkedin.com/jobs/search?keywords=%E9%9F%8C%E9%AB%94%E5%B7%A5%E7%A8%8B%E5%B8%AB&location=Taiwan&start=0",
        )
        self.assertIn("text/html", fetcher.calls[0][1]["Accept"])  # type: ignore[index]
        self.assertGreaterEqual(mocked_sleep.call_count, 2)

    def test_linkedin_search_falls_back_to_stale_cache_after_retryable_denial(self) -> None:
        settings = self.settings
        temp_cache_dir = Path(tempfile.mkdtemp())

        class AlwaysDeniedFetcher:
            def __init__(self) -> None:
                self.cache_dir = temp_cache_dir

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del force_refresh, headers, delay_seconds, cache_ttl_seconds
                raise HTTPError(url, 999, "Request denied", hdrs=None, fp=None)

        connector = LinkedInConnector(settings, AlwaysDeniedFetcher())  # type: ignore[arg-type]
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            "?keywords=%E9%9F%8C%E9%AB%94%E5%B7%A5%E7%A8%8B%E5%B8%AB&location=Taiwan&start=0"
        )
        cache_path = temp_cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.html"
        cache_path.write_text("<html>cached</html>", encoding="utf-8")

        with patch("job_spy_tw.connectors.linkedin.time.sleep"):
            html = connector.fetch_search_page("韌體工程師", 1)

        self.assertEqual(html, "<html>cached</html>")

    def test_linkedin_search_uses_secondary_public_search_url_after_guest_denial(self) -> None:
        class FallbackUrlFetcher:
            def __init__(self) -> None:
                self.calls: list[str] = []
                self.cache_dir = Path(tempfile.mkdtemp())

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del force_refresh, headers, delay_seconds, cache_ttl_seconds
                self.calls.append(url)
                if "jobs-guest" in url:
                    raise HTTPError(url, 999, "Request denied", hdrs=None, fp=None)
                return "<html>public-search</html>"

        fetcher = FallbackUrlFetcher()
        connector = LinkedInConnector(self.settings, fetcher)  # type: ignore[arg-type]

        with patch("job_spy_tw.connectors.linkedin.time.sleep"):
            html = connector.fetch_search_page("LLM", 1)

        self.assertEqual(html, "<html>public-search</html>")
        self.assertTrue(any("jobs-guest" in url for url in fetcher.calls))
        self.assertTrue(any("/jobs/search?" in url for url in fetcher.calls))

    def test_linkedin_search_reuses_legacy_tw_cache_after_public_denial(self) -> None:
        temp_cache_dir = Path(tempfile.mkdtemp())

        class AlwaysDeniedFetcher:
            def __init__(self) -> None:
                self.cache_dir = temp_cache_dir

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del force_refresh, headers, delay_seconds, cache_ttl_seconds
                raise HTTPError(url, 999, "Request denied", hdrs=None, fp=None)

        connector = LinkedInConnector(self.settings, AlwaysDeniedFetcher())  # type: ignore[arg-type]
        legacy_url = (
            "https://tw.linkedin.com/jobs/search"
            "?keywords=LLM&location=Taiwan&start=0"
        )
        cache_path = temp_cache_dir / f"{hashlib.sha256(legacy_url.encode()).hexdigest()}.html"
        cache_path.write_text("<html>legacy-cache</html>", encoding="utf-8")

        with patch("job_spy_tw.connectors.linkedin.time.sleep"):
            html = connector.fetch_search_page("LLM", 1)

        self.assertEqual(html, "<html>legacy-cache</html>")

    def test_linkedin_search_denial_without_cache_becomes_soft_warning(self) -> None:
        class AlwaysDeniedFetcher:
            def __init__(self) -> None:
                self.cache_dir = Path(tempfile.mkdtemp())

            def fetch(
                self,
                url: str,
                force_refresh: bool = False,
                headers: dict[str, str] | None = None,
                delay_seconds: float | None = None,
                cache_ttl_seconds: float | None = None,
            ) -> str:
                del force_refresh, headers, delay_seconds, cache_ttl_seconds
                raise HTTPError(url, 999, "Request denied", hdrs=None, fp=None)

        connector = LinkedInConnector(self.settings, AlwaysDeniedFetcher())  # type: ignore[arg-type]

        with patch("job_spy_tw.connectors.linkedin.time.sleep"):
            jobs = connector.search(["LLM"], pages=[1])

        self.assertEqual(jobs, [])
        self.assertEqual(len(connector.last_errors), 1)
        self.assertIn("LinkedIn search LLM p1", connector.last_errors[0])
        self.assertIn("已略過", connector.last_errors[0])
        self.assertNotIn("HTTP Error 999", connector.last_errors[0])

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

    def test_cake_detail_parser_extracts_work_and_requirement_items(self) -> None:
        connector = CakeConnector(self.settings, self.fetcher)
        job = JobListing(
            source="Cake",
            title="AI應用工程師",
            company="Example Corp",
            location="Taipei City, Taiwan",
            url="https://www.cake.me/companies/example-corp/jobs/123456789-ai-application-engineer",
        )
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "description": "Job Description\\n1. 導入企業內部 AI 工作流\\n2. 與產品及工程團隊合作\\nRequirements\\n1. 熟悉 Python 與 API 串接\\n2. 了解 LLM、RAG 或 prompt engineering"
              }
            </script>
          </head>
          <body></body>
        </html>
        """

        connector.populate_job_details(job, html)

        self.assertIn("導入企業內部 AI 工作流", job.work_content_items)
        self.assertIn("與產品及工程團隊合作", job.work_content_items)
        self.assertIn("熟悉 Python 與 API 串接", job.requirement_items)
        self.assertIn("了解 LLM、RAG 或 prompt engineering", job.required_skill_items)


if __name__ == "__main__":
    unittest.main()
