"""Shared chart constants and helpers."""

from __future__ import annotations

QUANTITY_GRADIENT = ["#dbeafe", "#93c5fd", "#2563eb"]
SCORE_GRADIENT = ["#e0f2fe", "#7dd3fc", "#2563eb"]
IMPORTANCE_DOMAIN = ["高", "中高", "中", "低"]
IMPORTANCE_RANGE = ["#16a34a", "#0ea5e9", "#60a5fa", "#cbd5e1"]
SOURCE_ROLE_RANGE = ["#1d4ed8", "#38bdf8", "#34d399", "#f59e0b", "#94a3b8", "#c084fc"]


def truncate_label(text: str, limit: int = 20) -> str:
    """截短過長標籤，避免圖表上的文字難以閱讀。"""
    cleaned = str(text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}..."
