"""Explicit schema/version registry for runtime reporting and releases."""

from __future__ import annotations

from typing import Any

from .models import (
    ASSISTANT_RESPONSE_SCHEMA_VERSION,
    MARKET_SNAPSHOT_SCHEMA_VERSION,
    RESUME_PROFILE_SCHEMA_VERSION,
)


PRODUCT_STATE_SCHEMA_VERSION = "product_state.v3"
QUERY_RUNTIME_SCHEMA_VERSION = "query_runtime.v2"
MARKET_HISTORY_SCHEMA_VERSION = "market_history.v1"
AUTH_SCHEMA_VERSION = "auth.v2"
AUDIT_SCHEMA_VERSION = "audit.v1"
PROMPT_REGISTRY_VERSION = "prompt_registry.v1"


def schema_version_registry() -> dict[str, Any]:
    return {
        "product_state": PRODUCT_STATE_SCHEMA_VERSION,
        "query_runtime": QUERY_RUNTIME_SCHEMA_VERSION,
        "market_history": MARKET_HISTORY_SCHEMA_VERSION,
        "auth": AUTH_SCHEMA_VERSION,
        "audit": AUDIT_SCHEMA_VERSION,
        "market_snapshot": MARKET_SNAPSHOT_SCHEMA_VERSION,
        "assistant_response": ASSISTANT_RESPONSE_SCHEMA_VERSION,
        "resume_profile": RESUME_PROFILE_SCHEMA_VERSION,
        "prompt_registry": PROMPT_REGISTRY_VERSION,
    }
