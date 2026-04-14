"""Tests for backend status CLI behavior."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.backend_status import main  # noqa: E402


class BackendStatusCliTests(unittest.TestCase):
    def test_main_returns_non_zero_in_strict_mode_when_issues_present(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        output = io.StringIO()
        with (
            patch.dict(os.environ, {"JOB_SPY_CRAWL_EXECUTION_MODE": "worker"}, clear=False),
            patch.object(
                sys,
                "argv",
                ["backend_status", "--base-dir", str(base_dir), "--strict"],
            ),
            redirect_stdout(output),
        ):
            exit_code = main()

        self.assertEqual(exit_code, 1)
        self.assertIn("Issues:", output.getvalue())

    def test_main_returns_zero_in_non_strict_mode(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        output = io.StringIO()
        with (
            patch.object(
                sys,
                "argv",
                ["backend_status", "--base-dir", str(base_dir)],
            ),
            redirect_stdout(output),
        ):
            exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertIn("Build:", output.getvalue())
        self.assertIn("Backend status:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
