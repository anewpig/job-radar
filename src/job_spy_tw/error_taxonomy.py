"""Structured application error categories for monitoring and user-safe reporting."""

from __future__ import annotations

from typing import Any


ERROR_KIND_CONNECTOR = "connector_error"
ERROR_KIND_LLM = "llm_error"
ERROR_KIND_RUNTIME = "runtime_error"
ERROR_KIND_AUTH = "auth_error"
ERROR_KIND_NOTIFICATION = "notification_error"
ERROR_KIND_VALIDATION = "validation_error"
ERROR_KIND_UNKNOWN = "unknown_error"


def classify_error(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if any(token in message for token in ("openai", "embedding", "responses", "token")):
        return ERROR_KIND_LLM
    if any(token in message for token in ("smtp", "email", "line", "webhook")):
        return ERROR_KIND_NOTIFICATION
    if any(token in message for token in ("password", "login", "email", "oidc", "reset")):
        return ERROR_KIND_AUTH
    if any(token in message for token in ("crawl", "queue", "runtime", "lease", "worker")):
        return ERROR_KIND_RUNTIME
    if any(token in name for token in ("valueerror", "typeerror", "keyerror")):
        return ERROR_KIND_VALIDATION
    if any(token in message for token in ("connector", "html", "scrape", "http")):
        return ERROR_KIND_CONNECTOR
    return ERROR_KIND_UNKNOWN


def error_metadata(exc: Exception) -> dict[str, Any]:
    return {
        "error_type": type(exc).__name__,
        "error_kind": classify_error(exc),
        "error_message": str(exc)[:240],
    }
