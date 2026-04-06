"""Tests for main navigation router helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui.router import build_drawer_items  # noqa: E402


class RouterTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
