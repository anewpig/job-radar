"""Tests for snapshot storage normalization."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.storage import load_snapshot


class StorageTests(unittest.TestCase):
    def test_load_snapshot_backfills_salary_from_104_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "jobs_latest.json"
            payload = {
                "generated_at": "2026-04-06T00:00:00",
                "queries": ["自動化工程師"],
                "role_targets": [{"name": "自動化工程師", "priority": 1, "keywords": ["PLC"]}],
                "jobs": [
                    {
                        "source": "104",
                        "title": "自動化工程師",
                        "company": "測試公司",
                        "location": "台中市",
                        "url": "https://www.104.com.tw/job/xyz123",
                        "salary": "",
                        "summary": "",
                        "description": "",
                        "posted_at": "",
                        "matched_role": "自動化工程師",
                        "relevance_score": 0.0,
                        "extracted_skills": [],
                        "work_content_items": [],
                        "required_skill_items": [],
                        "requirement_items": [],
                        "detail_sections": {},
                        "tags": [],
                        "metadata": {"salary_low": 45000, "salary_high": 80000},
                    }
                ],
                "skills": [],
                "task_insights": [],
                "errors": [],
            }
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            snapshot = load_snapshot(path)

        assert snapshot is not None
        self.assertEqual(snapshot.jobs[0].salary, "月薪 45,000 - 80,000 元")


if __name__ == "__main__":
    unittest.main()
