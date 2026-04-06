"""Compatibility wrapper exposing market analysis APIs."""

from __future__ import annotations

"""Backward-compatible public entrypoint for market analysis."""

from .market_analysis import JobAnalyzer, ROLE_KEYWORD_PATTERNS, SKILL_TAXONOMY, TASK_TAXONOMY

__all__ = ["JobAnalyzer", "ROLE_KEYWORD_PATTERNS", "SKILL_TAXONOMY", "TASK_TAXONOMY"]
