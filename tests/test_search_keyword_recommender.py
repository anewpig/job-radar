"""Tests for search keyword recommender behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.search_keyword_recommender import (  # noqa: E402
    RoleKeywordRecommender,
    autofill_role_keyword_rows,
)


class SearchKeywordRecommenderTests(unittest.TestCase):
    def test_recommender_suggests_piano_teacher_keywords(self) -> None:
        recommender = RoleKeywordRecommender()
        keywords = recommender.suggest_keywords("鋼琴老師")
        self.assertIn("古典鋼琴", keywords)
        self.assertIn("流行鋼琴", keywords)
        self.assertIn("Yamaha", keywords)
        self.assertIn("課程設計", keywords)

    def test_autofill_fills_keywords_for_new_role(self) -> None:
        recommender = RoleKeywordRecommender()
        rows, changed = autofill_role_keyword_rows(
            [{"enabled": True, "priority": 1, "role": "鋼琴老師", "keywords": ""}],
            [],
            recommender,
        )
        self.assertTrue(changed)
        self.assertIn("古典鋼琴", rows[0]["keywords"])
        self.assertTrue(rows[0]["enabled"])

    def test_autofill_replaces_previous_auto_keywords_on_role_change(self) -> None:
        recommender = RoleKeywordRecommender()
        previous_rows = [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": recommender.suggest_keywords_text("AI工程師")}]
        rows, changed = autofill_role_keyword_rows(
            [{"enabled": True, "priority": 1, "role": "產品經理", "keywords": previous_rows[0]["keywords"]}],
            previous_rows,
            recommender,
        )
        self.assertTrue(changed)
        self.assertIn("Roadmap", rows[0]["keywords"])

    def test_autofill_keeps_manual_keywords(self) -> None:
        recommender = RoleKeywordRecommender()
        previous_rows = [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "NLP, PyTorch"}]
        rows, changed = autofill_role_keyword_rows(
            [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "NLP, PyTorch"}],
            previous_rows,
            recommender,
        )
        self.assertFalse(changed)
        self.assertEqual(rows[0]["keywords"], "NLP, PyTorch")


if __name__ == "__main__":
    unittest.main()
