"""Tests for persistent assistant vector index."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.assistant.vector_index import PersistentANNIndex  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot  # noqa: E402
from job_spy_tw.storage import save_snapshot  # noqa: E402


def _fake_embed_texts(texts: list[str]) -> dict[str, list[float]]:
    vectors: dict[str, list[float]] = {}
    for text in texts:
        lowered = text.lower()
        checksum = sum(ord(char) for char in lowered)
        vectors[text] = [
            2.0 if "d4000" in lowered else 0.0,
            1.8 if "genaiot" in lowered else 0.0,
            1.5 if any(token in lowered for token in ("工作內容", "內容", "做什麼", "負責")) else 0.0,
            1.3 if any(token in lowered for token in ("技能", "python", "plc")) else 0.0,
            1.2 if any(token in lowered for token in ("薪資", "salary")) else 0.0,
            (checksum % 97) / 97.0,
            (checksum % 53) / 53.0,
            (checksum % 29) / 29.0,
        ]
    return vectors


class PersistentVectorIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = MarketSnapshot(
            generated_at="2026-04-09T20:00:00",
            queries=["自動化工程師"],
            role_targets=[],
            jobs=[
                JobListing(
                    source="104",
                    title="D4000 自動化工程師",
                    company="富邦媒體科技股份有限公司(富邦momo)",
                    location="台北市",
                    url="https://example.com/jobs/d4000",
                    summary="負責內部數據生產力平台開發與維護。",
                    salary="月薪 70,000 - 90,000",
                    matched_role="自動化工程師",
                    extracted_skills=["Python", "AWS", "API Design"],
                    required_skill_items=["Python", "AWS", "API Design"],
                    work_content_items=[
                        "協助內部數據生產力平台的開發與維護",
                        "支援跨團隊專案推進",
                    ],
                )
            ],
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_runtime_snapshot_persists_and_survives_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "assistant_vector_index.sqlite3"
            index = PersistentANNIndex(
                db_path=db_path,
                embedding_model="local-test",
            )
            indexed = index.sync_runtime_snapshot(
                snapshot=self.snapshot,
                embed_texts=_fake_embed_texts,
            )
            self.assertGreater(indexed, 0)

            first_results = index.search(
                question="D4000 自動化工程師 這個職缺主要在做什麼？",
                embed_texts=_fake_embed_texts,
                top_k=3,
            )
            self.assertTrue(first_results)
            self.assertIn("D4000 自動化工程師", first_results[0].label)

            reopened = PersistentANNIndex(
                db_path=db_path,
                embedding_model="local-test",
            )
            second_results = reopened.search(
                question="D4000 自動化工程師 這個職缺主要在做什麼？",
                embed_texts=_fake_embed_texts,
                top_k=3,
            )
            self.assertTrue(second_results)
            self.assertEqual(second_results[0].label, first_results[0].label)

    def test_snapshot_file_sync_is_searchable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir)
            snapshot_path = data_root / "jobs_latest.json"
            save_snapshot(self.snapshot, snapshot_path)

            index = PersistentANNIndex(
                db_path=data_root / "assistant_vector_index.sqlite3",
                embedding_model="local-test",
            )
            indexed = index.sync_snapshot_file(
                snapshot_path=snapshot_path,
                embed_texts=_fake_embed_texts,
            )
            self.assertGreater(indexed, 0)

            results = index.search(
                question="這個職缺需要哪些技能？ D4000 自動化工程師",
                embed_texts=_fake_embed_texts,
                top_k=5,
            )
            self.assertTrue(results)
            self.assertTrue(any("D4000 自動化工程師" in chunk.label for chunk in results))


if __name__ == "__main__":
    unittest.main()
