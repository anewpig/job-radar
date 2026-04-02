from __future__ import annotations

"""Backward-compatible public entrypoint for runtime settings."""

from .settings import Settings, load_settings

__all__ = ["Settings", "load_settings"]
