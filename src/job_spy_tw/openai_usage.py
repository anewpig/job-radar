"""Helpers for normalizing OpenAI usage metadata across responses and embeddings."""

from __future__ import annotations

from typing import Any


def extract_openai_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")

    if usage is None:
        return _empty_usage()

    input_tokens = _coerce_usage_value(
        getattr(usage, "input_tokens", None),
        _mapping_get(usage, "input_tokens"),
        getattr(usage, "prompt_tokens", None),
        _mapping_get(usage, "prompt_tokens"),
    )
    output_tokens = _coerce_usage_value(
        getattr(usage, "output_tokens", None),
        _mapping_get(usage, "output_tokens"),
        getattr(usage, "completion_tokens", None),
        _mapping_get(usage, "completion_tokens"),
    )
    total_tokens = _coerce_usage_value(
        getattr(usage, "total_tokens", None),
        _mapping_get(usage, "total_tokens"),
        input_tokens + output_tokens,
    )
    cached_input_tokens = _coerce_usage_value(
        getattr(getattr(usage, "input_token_details", None), "cached_tokens", None),
        _mapping_get(_mapping_get(usage, "input_token_details"), "cached_tokens"),
    )
    return {
        "requests": 1,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
    }


def merge_openai_usage(*usages: dict[str, int] | None) -> dict[str, int]:
    merged = _empty_usage()
    for usage in usages:
        if not usage:
            continue
        for key in merged:
            merged[key] += int(usage.get(key, 0) or 0)
    return merged


def _empty_usage() -> dict[str, int]:
    return {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_input_tokens": 0,
    }


def _mapping_get(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        if key is None:
            return value
        return value.get(key)
    return None


def _coerce_usage_value(*candidates: Any) -> int:
    for candidate in candidates:
        if candidate in (None, ""):
            continue
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return 0
