"""Tests for backend logging helpers."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw import logging_utils  # noqa: E402
from job_spy_tw.observability import trace_context  # noqa: E402


class LoggingUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_logger = logging.getLogger()
        self.original_handlers = list(self.root_logger.handlers)
        self.original_level = self.root_logger.level
        self._reset_job_radar_handlers()
        logging_utils._LOGGING_CONFIGURED = False

    def tearDown(self) -> None:
        self._reset_job_radar_handlers()
        for handler in self.original_handlers:
            if handler not in self.root_logger.handlers:
                self.root_logger.addHandler(handler)
        self.root_logger.setLevel(self.original_level)
        logging_utils._LOGGING_CONFIGURED = False

    def _reset_job_radar_handlers(self) -> None:
        for handler in list(self.root_logger.handlers):
            name = getattr(handler, "name", "")
            if name.startswith("job-radar-"):
                self.root_logger.removeHandler(handler)
                try:
                    handler.close()
                except Exception:
                    pass

    def test_configure_logging_writes_json_log_with_trace_id(self) -> None:
        data_dir = Path(tempfile.mkdtemp())
        with mock.patch.dict(
            os.environ,
            {
                "JOB_SPY_LOG_FORMAT": "json",
                "JOB_SPY_LOG_CONSOLE": "0",
            },
            clear=False,
        ):
            logger = logging_utils.configure_logging(
                service_name="worker-test",
                data_dir=data_dir,
            )
            with trace_context("trace-xyz"):
                logger.info("hello json log")
            for handler in self.root_logger.handlers:
                if getattr(handler, "name", "").startswith("job-radar-file:"):
                    handler.flush()

        log_path = data_dir / "logs" / "worker-test.log"
        payload = json.loads(log_path.read_text(encoding="utf-8").strip())

        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "worker-test")
        self.assertEqual(payload["message"], "hello json log")
        self.assertEqual(payload["trace_id"], "trace-xyz")

    def test_configure_logging_does_not_duplicate_handlers_on_second_call(self) -> None:
        data_dir = Path(tempfile.mkdtemp())
        with mock.patch.dict(
            os.environ,
            {
                "JOB_SPY_LOG_FORMAT": "text",
                "JOB_SPY_LOG_CONSOLE": "0",
            },
            clear=False,
        ):
            first = logging_utils.configure_logging(
                service_name="dup-test",
                data_dir=data_dir,
            )
            handler_names_after_first = [
                getattr(handler, "name", "")
                for handler in self.root_logger.handlers
                if getattr(handler, "name", "").startswith("job-radar-")
            ]
            second = logging_utils.configure_logging(
                service_name="dup-test",
                data_dir=data_dir,
            )
            handler_names_after_second = [
                getattr(handler, "name", "")
                for handler in self.root_logger.handlers
                if getattr(handler, "name", "").startswith("job-radar-")
            ]

        self.assertIs(first, second)
        self.assertEqual(handler_names_after_first, handler_names_after_second)
        self.assertEqual(handler_names_after_second.count("job-radar-file:dup-test"), 1)


if __name__ == "__main__":
    unittest.main()
