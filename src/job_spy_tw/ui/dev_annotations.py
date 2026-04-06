"""提供開發階段用的 UI 標註與層級說明 helper。"""

from __future__ import annotations

import html

import streamlit as st

DEV_CARD_ANNOTATIONS_ENABLED = True

DevNamedItem = tuple[str, str]


def _escape(text: object) -> str:
    """把標註內容轉成可安全嵌入 HTML 的文字。"""
    return html.escape(str(text))


def _normalize_items(items: list[str] | None) -> list[str]:
    """整理純文字列表，移除空值並保留原順序。"""
    if not items:
        return []
    normalized: list[str] = []
    for item in items:
        cleaned = str(item).strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _normalize_named_items(items: list[DevNamedItem] | None) -> list[DevNamedItem]:
    """整理帶名稱與說明的列表。"""
    if not items:
        return []
    normalized: list[DevNamedItem] = []
    for name, description in items:
        cleaned_name = str(name).strip()
        cleaned_description = str(description).strip()
        if cleaned_name and cleaned_description:
            normalized.append((cleaned_name, cleaned_description))
    return normalized


def _render_code_list(items: list[str]) -> str:
    """把純文字 key 列表渲染成 code list。"""
    return "".join(f"<li><code>{_escape(item)}</code></li>" for item in items)


def _render_named_list(items: list[DevNamedItem]) -> str:
    """把帶說明的文字節點列表渲染成兩欄清單。"""
    return "".join(
        (
            "<li class=\"dev-card-annotation-details__named-item\">"
            f"<code>{_escape(name)}</code>"
            f"<span>{_escape(description)}</span>"
            "</li>"
        )
        for name, description in items
    )


def _render_note_list(items: list[str]) -> str:
    """把補充說明列表渲染成簡單文字清單。"""
    return "".join(f"<li>{_escape(item)}</li>" for item in items)


def render_dev_card_annotation(
    name: str,
    *,
    element_id: str,
    description: str = "",
    layers: list[str] | None = None,
    text_nodes: list[DevNamedItem] | None = None,
    notes: list[str] | None = None,
    show_popover: bool = False,
    popover_key: str | None = None,
    compact: bool = False,
) -> None:
    """在開發階段渲染卡片名稱標註，必要時補上層級與文字節點說明。"""
    if not DEV_CARD_ANNOTATIONS_ENABLED:
        return

    normalized_layers = _normalize_items(layers)
    normalized_text_nodes = _normalize_named_items(text_nodes)
    normalized_notes = _normalize_items(notes)

    shell_classes = ["dev-card-annotation-shell"]
    if compact:
        shell_classes.append("dev-card-annotation-shell--compact")
    row_classes = ["dev-card-annotation-row"]
    if compact:
        row_classes.append("dev-card-annotation-row--compact")

    pill_markup = (
        "<div class=\"dev-card-annotation-left\">"
        f"<span class=\"dev-card-annotation__pill\">開發標註 · {_escape(name)}</span>"
        f"<span class=\"dev-card-annotation__id\">{_escape(element_id)}</span>"
        "</div>"
    )

    if not show_popover:
        st.markdown(
            (
                f"<div class=\"{' '.join(shell_classes)}\">"
                f"<div class=\"{' '.join(row_classes)}\">"
                f"{pill_markup}"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        return

    popover_key = popover_key or element_id.replace(" ", "-")
    detail_sections: list[str] = [
        f"<div class=\"dev-card-annotation-details__title\">{_escape(name)}</div>",
        (
            "<div class=\"dev-card-annotation-details__meta\">"
            "識別 key："
            f"<code>{_escape(element_id)}</code>"
            "</div>"
        ),
    ]
    if description:
        detail_sections.append(
            f"<div class=\"dev-card-annotation-details__copy\">{_escape(description)}</div>"
        )
    if normalized_layers:
        detail_sections.append(
            "<div class=\"dev-card-annotation-details__section-title\">子區塊 / 層級</div>"
            f"<ul class=\"dev-card-annotation-details__list\">{_render_code_list(normalized_layers)}</ul>"
        )
    if normalized_text_nodes:
        detail_sections.append(
            "<div class=\"dev-card-annotation-details__section-title\">文字節點 / tag</div>"
            f"<ul class=\"dev-card-annotation-details__list dev-card-annotation-details__list--named\">{_render_named_list(normalized_text_nodes)}</ul>"
        )
    if normalized_notes:
        detail_sections.append(
            "<div class=\"dev-card-annotation-details__section-title\">補充說明</div>"
            f"<ul class=\"dev-card-annotation-details__list\">{_render_note_list(normalized_notes)}</ul>"
        )

    details_markup = (
        f"<details class=\"dev-card-annotation-details\" id=\"dev-annotation-{_escape(popover_key)}\">"
        "<summary class=\"dev-card-annotation-details__summary\">層級與文字資訊</summary>"
        "<div class=\"dev-card-annotation-details__panel\">"
        f"{''.join(detail_sections)}"
        "</div>"
        "</details>"
    )
    st.markdown(
        (
            f"<div class=\"{' '.join(shell_classes)}\">"
            f"<div class=\"{' '.join(row_classes)}\">"
            f"{pill_markup}"
            f"{details_markup}"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
