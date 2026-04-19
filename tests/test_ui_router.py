"""Tests for main navigation router helpers."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if "streamlit" not in sys.modules:
    streamlit_stub = types.ModuleType("streamlit")
    streamlit_stub.session_state = {}
    sys.modules["streamlit"] = streamlit_stub

from job_spy_tw.ui.router import build_drawer_items, build_drawer_sections, build_main_tab_items  # noqa: E402


class RouterTests(unittest.TestCase):
    def test_build_main_tab_items_includes_fine_tuning(self) -> None:
        tab_ids = [tab_id for tab_id, _label in build_main_tab_items(unread_notification_count=0)]
        self.assertIn("fine_tuning", tab_ids)

    def test_build_drawer_items_hides_backend_console_when_disabled(self) -> None:
        drawer_ids = [
            tab_id
            for tab_id, _label in build_drawer_items(
                unread_notification_count=0,
                show_backend_console=False,
            )
        ]

        self.assertNotIn("backend_console", drawer_ids)

    def test_build_drawer_items_shows_backend_console_before_export_when_enabled(self) -> None:
        drawer_ids = [
            tab_id
            for tab_id, _label in build_drawer_items(
                unread_notification_count=3,
                show_backend_console=True,
            )
        ]

        self.assertIn("backend_console", drawer_ids)
        self.assertLess(drawer_ids.index("backend_console"), drawer_ids.index("export"))

    def test_build_drawer_sections_follow_expected_group_order(self) -> None:
        sections = build_drawer_sections(
            unread_notification_count=2,
            show_backend_console=False,
        )

        self.assertEqual(
            [section["label"] for section in sections],
            ["工作台", "分析與管理"],
        )
        self.assertEqual(
            [item["tab_id"] for item in sections[0]["items"]],
            ["overview", "assistant", "resume", "tasks", "tracking", "board"],
        )
        self.assertEqual(
            [item["tab_id"] for item in sections[1]["items"]],
            ["sources", "fine_tuning", "notifications", "database", "export"],
        )

    def test_build_drawer_sections_only_show_system_group_when_enabled(self) -> None:
        hidden_sections = build_drawer_sections(
            unread_notification_count=0,
            show_backend_console=False,
        )
        visible_sections = build_drawer_sections(
            unread_notification_count=0,
            show_backend_console=True,
        )

        self.assertNotIn("系統", [section["label"] for section in hidden_sections])
        self.assertEqual(visible_sections[-1]["label"], "系統")
        self.assertEqual(
            [item["tab_id"] for item in visible_sections[-1]["items"]],
            ["backend_console"],
        )


if __name__ == "__main__":
    unittest.main()
