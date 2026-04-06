"""Tests for structured job detail parsing helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.detail_parsing import split_structured_items


class DetailParsingTests(unittest.TestCase):
    def test_split_structured_items_keeps_numbered_prefix_blocks(self) -> None:
        text = (
            "1.企業 AI 應用導入與推行\n"
            "規劃並推動企業內部 AI 專案\n"
            "2.需求分析與跨部門協作\n"
            "蒐集並分析業務單位需求"
        )

        items = split_structured_items(text)

        self.assertEqual(
            items,
            [
                "企業 AI 應用導入與推行：規劃並推動企業內部 AI 專案",
                "需求分析與跨部門協作：蒐集並分析業務單位需求",
            ],
        )

    def test_split_structured_items_extracts_inline_numbered_items(self) -> None:
        text = "1.調查AI產業趨勢與供應商方案、產品發展現況 2.與AI方案商合作進行產品整合 3.依產品規格執行研發與優化"

        items = split_structured_items(text)

        self.assertEqual(
            items,
            [
                "調查AI產業趨勢與供應商方案、產品發展現況",
                "與AI方案商合作進行產品整合",
                "依產品規格執行研發與優化",
            ],
        )

    def test_split_structured_items_extracts_inline_fullwidth_numbered_items(self) -> None:
        text = "1、AI深度學習研究及開發 2、LLM與VLM相關功能研究與開發"

        items = split_structured_items(text)

        self.assertEqual(
            items,
            [
                "AI深度學習研究及開發",
                "LLM與VLM相關功能研究與開發",
            ],
        )

    def test_split_structured_items_unescapes_html_lists(self) -> None:
        text = (
            "&lt;p&gt;【工作內容】&lt;br&gt;"
            "● 參與 AI 服務的設計、開發與優化。&lt;br&gt;"
            "● 協助評估技術方案與可行性。&lt;/p&gt;"
        )

        items = split_structured_items(text)

        self.assertEqual(
            items,
            [
                "參與 AI 服務的設計、開發與優化。",
                "協助評估技術方案與可行性。",
            ],
        )


if __name__ == "__main__":
    unittest.main()
