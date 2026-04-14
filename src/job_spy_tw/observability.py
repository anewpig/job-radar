"""Shared trace and correlation-id helpers."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from uuid import uuid4


_TRACE_ID: ContextVar[str] = ContextVar("job_radar_trace_id", default="")


def get_trace_id() -> str:
    return _TRACE_ID.get()


def new_trace_id(prefix: str = "trace") -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def set_trace_id(trace_id: str) -> Token[str]:
    return _TRACE_ID.set(str(trace_id or "").strip())


def reset_trace_id(token: Token[str]) -> None:
    _TRACE_ID.reset(token)


@contextmanager
def trace_context(trace_id: str):
    token = set_trace_id(trace_id)
    try:
        yield trace_id
    finally:
        reset_trace_id(token)
