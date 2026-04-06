"""Compatibility wrapper exposing notification delivery services."""

from __future__ import annotations

"""Backward-compatible public entrypoint for notification delivery."""

from .notifications import NotificationService

__all__ = ["NotificationService"]
