"""Tests for UI render helper fallbacks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui.renderers import _build_work_preview_items


class UIRendererTests(unittest.TestCase):
    def test_build_work_preview_items_falls_back_for_1111_inline_numbering(self) -> None:
        row = {
            "source": "1111",
            "work_content_items": [],
            "detail_sections": {
                "work_content": "1、AI深度學習研究及開發 2、LLM與VLM相關功能研究與開發",
            },
            "description": "",
        }

        items = _build_work_preview_items(row)

        self.assertEqual(
            items,
            [
                "AI深度學習研究及開發",
                "LLM與VLM相關功能研究與開發",
            ],
        )

    def test_build_work_preview_items_falls_back_for_cake_html_description(self) -> None:
        row = {
            "source": "Cake",
            "work_content_items": [],
            "detail_sections": {"work_content": ""},
            "description": (
                "&lt;p&gt;【工作內容】&lt;br&gt;"
                "● 參與 AI 服務的設計、開發與優化。&lt;br&gt;"
                "● 協助評估技術方案與可行性。&lt;/p&gt;"
            ),
        }

        items = _build_work_preview_items(row)

        self.assertEqual(
            items,
            [
                "參與 AI 服務的設計、開發與優化。",
                "協助評估技術方案與可行性。",
            ],
        )


if __name__ == "__main__":
    unittest.main()
