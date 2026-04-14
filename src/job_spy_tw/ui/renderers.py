"""提供各頁共用 renderer 的相容入口。"""

from __future__ import annotations

from .renderers_assistant import (
    render_assistant_response,
    render_assistant_suggestion_buttons,
)
from .renderers_job_cards import _build_work_preview_items, render_job_cards
from .renderers_resume import render_resume_profile

__all__ = [
    "_build_work_preview_items",
    "render_assistant_response",
    "render_assistant_suggestion_buttons",
    "render_job_cards",
    "render_resume_profile",
]
