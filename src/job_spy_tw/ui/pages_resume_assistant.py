"""提供履歷匹配與 AI 助理頁面的相容匯出入口。"""

from __future__ import annotations

from .pages_assistant import render_assistant_page
from .pages_resume import render_resume_page

__all__ = [
    "render_assistant_page",
    "render_resume_page",
]
