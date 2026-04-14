"""提供追蹤中心頁面的共用操作 helper。"""

from __future__ import annotations

import streamlit as st

from ..models import FavoriteJob, JobListing, SavedSearch
from .page_context import PageContext
from .search import get_committed_search_rows
from .session import set_main_tab


def _apply_saved_search_to_session(
    ctx: PageContext,
    saved_search: SavedSearch,
    *,
    pending_refresh: bool = False,
) -> None:
    rows = saved_search.rows or ctx.default_rows
    st.session_state.search_role_rows = rows
    st.session_state.search_role_widget_refresh = rows
    st.session_state.custom_queries_text = saved_search.custom_queries_text
    st.session_state.crawl_preset_label = saved_search.crawl_preset_label
    st.session_state.active_saved_search_id = saved_search.id
    st.session_state.saved_search_name_input = saved_search.name
    if pending_refresh:
        st.session_state.pending_saved_search_refresh_id = saved_search.id
    set_main_tab("tracking")


def _load_saved_search(ctx: PageContext, saved_search: SavedSearch) -> None:
    _apply_saved_search_to_session(ctx, saved_search)
    st.session_state.favorite_feedback = f"已載入搜尋條件：{saved_search.name}"
    st.rerun()


def _refresh_saved_search(ctx: PageContext, saved_search: SavedSearch) -> None:
    _apply_saved_search_to_session(ctx, saved_search, pending_refresh=True)
    st.rerun()


def _overwrite_saved_search(
    ctx: PageContext,
    saved_search: SavedSearch,
    *,
    edited_name: str,
) -> None:
    snapshot_for_baseline = None
    if (
        st.session_state.snapshot is not None
        and st.session_state.last_crawl_signature == ctx.current_signature
    ):
        snapshot_for_baseline = st.session_state.snapshot
        ctx.product_store.save_search(
            user_id=ctx.current_user_id,
            name=edited_name,
            rows=get_committed_search_rows(
                st.session_state.search_role_rows,
                draft_index=st.session_state.get("search_role_draft_index"),
            ),
            custom_queries_text=st.session_state.custom_queries_text,
            crawl_preset_label=st.session_state.crawl_preset_label,
            snapshot=snapshot_for_baseline,
            search_id=saved_search.id,
        )
    st.session_state.active_saved_search_id = saved_search.id
    set_main_tab("tracking")
    st.session_state.favorite_feedback = f"已覆蓋搜尋條件：{edited_name}"
    st.rerun()


def _delete_saved_search(ctx: PageContext, saved_search: SavedSearch) -> None:
    ctx.product_store.delete_saved_search(saved_search.id, user_id=ctx.current_user_id)
    if st.session_state.active_saved_search_id == saved_search.id:
        st.session_state.active_saved_search_id = None
    set_main_tab("tracking")
    st.session_state.favorite_feedback = f"已刪除搜尋條件：{saved_search.name}"
    st.rerun()


def _mark_all_notifications_read(ctx: PageContext) -> None:
    ctx.product_store.mark_all_notifications_read(user_id=ctx.current_user_id)
    set_main_tab("tracking")
    st.rerun()


def _open_board() -> None:
    set_main_tab("board")
    st.rerun()


def _remove_favorite_shortcut(ctx: PageContext, favorite: FavoriteJob) -> None:
    job = ctx.jobs_by_url.get(favorite.job_url)
    if job is not None:
        ctx.product_store.toggle_favorite(job, user_id=ctx.current_user_id)
    else:
        ctx.product_store.toggle_favorite(
            JobListing(
                source=favorite.source,
                title=favorite.title,
                company=favorite.company,
                location=favorite.location,
                salary=favorite.salary,
                matched_role=favorite.matched_role,
                url=favorite.job_url,
            ),
            user_id=ctx.current_user_id,
        )
    set_main_tab("tracking")
    st.session_state.favorite_feedback = f"已取消收藏：{favorite.title}"
    st.rerun()
