"""Contract schema registry for application boundaries."""

from __future__ import annotations

from .schemas import SCHEMA_REGISTRY


def list_schemas() -> list[str]:
    return sorted(SCHEMA_REGISTRY.keys())


def get_schema(name: str) -> dict[str, object]:
    return SCHEMA_REGISTRY[name]
