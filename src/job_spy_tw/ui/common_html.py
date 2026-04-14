"""Shared HTML/text helpers."""

from __future__ import annotations

import html


def _escape(text: object) -> str:
    """把任意文字轉成可安全嵌入 HTML 的內容。"""
    return html.escape(str(text))


def _escape_multiline(text: object) -> str:
    """轉義文字並保留換行，方便直接輸出到 HTML 片段。"""
    return _escape(text).replace("\n", "<br>")


def build_chip_row(
    items: list[str],
    *,
    empty_text: str = "未設定",
    tone: str = "accent",
    limit: int | None = None,
) -> str:
    """把字串清單渲染成一排扁平的 HTML chip。"""
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if limit is not None:
        cleaned = cleaned[:limit]
    if not cleaned:
        return f'<span class="ui-chip empty-chip">{_escape(empty_text)}</span>'
    tone_class = {
        "accent": "ui-chip ui-chip--accent",
        "soft": "ui-chip ui-chip--soft",
        "warm": "ui-chip ui-chip--warm",
    }.get(tone, "ui-chip")
    return "".join(
        f'<span class="{tone_class}">{_escape(item)}</span>' for item in cleaned
    )


def build_html_list(items: list[str], *, empty_text: str, limit: int) -> str:
    """把資料渲染成簡單的 HTML 清單，並處理空狀態。"""
    cleaned = [str(item).strip() for item in items if str(item).strip()][:limit]
    if not cleaned:
        return f'<li class="empty-chip">{_escape(empty_text)}</li>'
    return "".join(f"<li>{_escape(item)}</li>" for item in cleaned)


def mask_identifier(value: str, *, prefix: int = 3, suffix: int = 3) -> str:
    """遮罩使用者識別字串，只保留少量前後綴。"""
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= prefix + suffix:
        return cleaned[:1] + "***"
    return f"{cleaned[:prefix]}***{cleaned[-suffix:]}"


def _format_ranked_terms(items: list[tuple[str, int]], tone: str) -> str:
    """把排序後的詞項整理成保留次數標記的 chip 列。"""
    if not items:
        return build_chip_row([], tone=tone)
    labels = [f"{label} ×{count}" for label, count in items]
    return build_chip_row(labels, tone=tone, limit=8)
