"""Tests for the boot loading shell helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui.loading_shell import (  # noqa: E402
    dismiss_boot_loading_overlay,
    render_boot_loading_overlay,
    should_show_boot_loader,
)


class LoadingShellTests(unittest.TestCase):
    def test_should_show_boot_loader_before_first_complete_render(self) -> None:
        self.assertTrue(should_show_boot_loader({}))
        self.assertTrue(should_show_boot_loader({"_boot_loader_complete": False}))

    def test_should_hide_boot_loader_after_first_complete_render(self) -> None:
        self.assertFalse(should_show_boot_loader({"_boot_loader_complete": True}))

    def test_loading_shell_exports_render_helpers(self) -> None:
        self.assertTrue(callable(render_boot_loading_overlay))
        self.assertTrue(callable(dismiss_boot_loading_overlay))


if __name__ == "__main__":
    unittest.main()
