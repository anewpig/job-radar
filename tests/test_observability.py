"""Tests for shared trace-context helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.observability import (  # noqa: E402
    get_trace_id,
    new_trace_id,
    trace_context,
)


class ObservabilityTests(unittest.TestCase):
    def test_new_trace_id_uses_prefix_and_generates_identifier(self) -> None:
        trace_id = new_trace_id("auth")

        self.assertTrue(trace_id.startswith("auth-"))
        self.assertGreater(len(trace_id), len("auth-"))

    def test_trace_context_sets_and_restores_trace_id(self) -> None:
        self.assertEqual(get_trace_id(), "")

        with trace_context("trace-123"):
            self.assertEqual(get_trace_id(), "trace-123")

        self.assertEqual(get_trace_id(), "")


if __name__ == "__main__":
    unittest.main()
