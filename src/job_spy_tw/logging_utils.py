"""Logging helpers for backend services."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .observability import get_trace_id


_LOGGING_CONFIGURED = False


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_formatter(log_format: str) -> logging.Formatter:
    if log_format == "json":
        return JsonFormatter()
    return logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(trace_id)s | %(message)s")


def configure_logging(*, service_name: str, data_dir: Path | None = None) -> logging.Logger:
    global _LOGGING_CONFIGURED

    logger = logging.getLogger(service_name)
    if _LOGGING_CONFIGURED:
        return logger

    level_name = os.getenv("JOB_SPY_LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    log_dir_value = os.getenv("JOB_SPY_LOG_DIR", "").strip()
    if log_dir_value:
        log_dir = Path(log_dir_value).expanduser()
    elif data_dir is not None:
        log_dir = Path(data_dir).expanduser() / "logs"
    else:
        log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = int(os.getenv("JOB_SPY_LOG_MAX_BYTES", "5000000"))
    backup_count = int(os.getenv("JOB_SPY_LOG_BACKUP_COUNT", "7"))
    enable_console = _parse_bool(os.getenv("JOB_SPY_LOG_CONSOLE"), True)
    log_format = os.getenv("JOB_SPY_LOG_FORMAT", "text").strip().lower()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    formatter = _build_formatter(log_format)
    trace_filter = TraceIdFilter()

    handler_name = f"job-radar-file:{service_name}"
    if not any(getattr(handler, "name", "") == handler_name for handler in root_logger.handlers):
        file_handler = RotatingFileHandler(
            log_dir / f"{service_name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.name = handler_name
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        root_logger.addHandler(file_handler)

    if enable_console and not any(getattr(handler, "name", "") == "job-radar-console" for handler in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.name = "job-radar-console"
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(trace_filter)
        root_logger.addHandler(console_handler)

    _LOGGING_CONFIGURED = True
    return logger
