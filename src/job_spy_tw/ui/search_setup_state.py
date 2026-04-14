"""搜尋設定表單的狀態物件與搜尋列操作 helpers。"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from ..crawl_tuning import CrawlPreset
from ..search_keyword_recommender import (
    autofill_role_keyword_rows,
    normalize_search_role_rows,
)
from .search import (
    _default_search_row,
    _next_search_priority,
    _search_widget_key,
    split_search_rows_for_ui,
)


@dataclass(frozen=True, slots=True)
class SearchSetupState:
    """封裝本輪搜尋設定渲染後回傳的控制狀態。"""

    run_crawl: bool
    crawl_preset: CrawlPreset
    custom_queries: str
    force_refresh: bool


def read_single_row_widget(index: int) -> dict[str, object]:
    """讀取單一搜尋列的 widget 狀態。"""
    return {
        "enabled": True,
        "priority": int(st.session_state.get(_search_widget_key(index, "priority"), index + 1) or (index + 1)),
        "role": str(st.session_state.get(_search_widget_key(index, "role"), "")).strip(),
        "keywords": str(st.session_state.get(_search_widget_key(index, "keywords"), "")).strip(),
    }


def prepare_search_rows_for_ui(rows: list[dict]) -> list[dict]:
    """把搜尋列整理成「已加入 rows + 最後一列可編輯 draft」的型態。"""
    committed_rows, draft_row = split_search_rows_for_ui(
        rows,
        draft_index=st.session_state.get("search_role_draft_index"),
    )
    return committed_rows + [draft_row]


def sync_search_row_widgets(rows: list[dict]) -> None:
    """把整理後的搜尋列同步回 session widget 狀態。"""
    st.session_state.search_role_rows = rows
    st.session_state.search_role_draft_index = max(0, len(rows) - 1)
    for index, row in enumerate(rows):
        for field, fallback in _default_search_row().items():
            st.session_state[_search_widget_key(index, field)] = row.get(field, fallback)


def replace_search_rows(rows: list[dict]) -> None:
    """把搜尋列寫回 session 並在下一輪重新同步 widget。"""
    updated_rows = normalize_search_role_rows(rows) or [_default_search_row()]
    st.session_state.search_role_rows = updated_rows
    st.session_state.search_role_draft_index = max(0, len(updated_rows) - 1)
    st.session_state.search_role_widget_refresh = updated_rows
    st.rerun()


def commit_current_draft(*, draft_index: int, committed_rows: list[dict]) -> None:
    """把目前編輯中的搜尋列收進已加入清單，並補一列新的 draft。"""
    draft_row = normalize_search_role_rows([read_single_row_widget(draft_index)])[0]
    if not str(draft_row.get("role", "")).strip():
        return
    committed = normalize_search_role_rows(committed_rows)
    draft_row["priority"] = _next_search_priority(committed)
    updated_rows = committed + [draft_row]
    next_draft = _default_search_row()
    next_draft["priority"] = _next_search_priority(updated_rows)
    updated_rows.append(next_draft)
    st.session_state.search_role_rows = updated_rows
    st.session_state.search_role_draft_index = len(updated_rows) - 1
    st.session_state.search_role_widget_refresh = updated_rows
    st.rerun()


def remove_committed_role(*, remove_row_index: int, committed_rows: list[dict], draft_index: int) -> None:
    """移除指定 tag，並保留目前正在編輯的 draft。"""
    current_draft = normalize_search_role_rows([read_single_row_widget(draft_index)])[0]
    remaining_rows = [row for index, row in enumerate(committed_rows) if index != remove_row_index]
    replace_search_rows(remaining_rows + [current_draft])


def edit_committed_role(*, edit_row_index: int, committed_rows: list[dict], draft_index: int) -> None:
    """把已加入 tag 載回編輯列，原本 draft 若有內容則先收回 tag 區。"""
    current_draft = normalize_search_role_rows([read_single_row_widget(draft_index)])[0]
    remaining_rows = [row for index, row in enumerate(committed_rows) if index != edit_row_index]
    if row_has_content(current_draft):
        current_draft["priority"] = _next_search_priority(remaining_rows)
        remaining_rows.append(current_draft)
    row_to_edit = normalize_search_role_rows([committed_rows[edit_row_index]])[0]
    row_to_edit["priority"] = _next_search_priority(remaining_rows)
    replace_search_rows(remaining_rows + [row_to_edit])


def sync_autofill(
    previous_role_rows: list[dict],
    committed_rows: list[dict],
    draft_index: int,
    keyword_recommender: object,
) -> None:
    """讀取目前輸入值、補齊推薦關鍵字，並顯示自動補齊提示。"""
    edited_roles = normalize_search_role_rows(committed_rows + [read_single_row_widget(draft_index)])
    normalized_roles, autofilled = autofill_role_keyword_rows(
        edited_roles,
        previous_role_rows,
        keyword_recommender,
    )
    st.session_state.search_role_rows = normalized_roles
    st.session_state.search_role_draft_index = max(0, len(normalized_roles) - 1)
    if autofilled:
        st.session_state.search_role_autofilled_notice = True
        st.session_state.search_role_widget_refresh = normalized_roles
        st.rerun()
    if st.session_state.search_role_autofilled_notice:
        st.session_state.search_role_autofilled_notice = False


def row_has_content(row: dict) -> bool:
    """判斷某列是否已經有可視為一組搜尋條件的內容。"""
    return bool(str(row.get("role", "")).strip() or str(row.get("keywords", "")).strip())
