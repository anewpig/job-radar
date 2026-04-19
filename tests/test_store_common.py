"""Tests for store-layer common normalization helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.store.common import build_signature, signature_payload  # noqa: E402


class StoreCommonTests(unittest.TestCase):
    def test_signature_payload_defaults_none_text_inputs(self) -> None:
        payload = signature_payload(
            [
                {
                    "enabled": True,
                    "priority": 1,
                    "role": None,
                    "keywords": None,
                }
            ],
            None,
            None,
        )

        self.assertEqual(payload["crawl_preset_label"], "快速")
        self.assertEqual(payload["custom_queries"], [])
        self.assertEqual(
            payload["rows"],
            [
                {
                    "enabled": True,
                    "priority": 1,
                    "role": "",
                    "keywords": "",
                }
            ],
        )

    def test_build_signature_is_stable_when_crawl_preset_is_none(self) -> None:
        signature = build_signature(
            [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": ""}],
            "",
            None,
        )

        self.assertIn('"crawl_preset_label": "快速"', signature)


if __name__ == "__main__":
    unittest.main()
