"""提供投遞看板頁面的共用操作 helper。"""

from __future__ import annotations

import streamlit as st

from ..models import FavoriteJob
from .page_context import PageContext
from .session import set_main_tab


def _update_board_card(
    ctx: PageContext,
    favorite: FavoriteJob,
    *,
    next_status: str,
    next_notes: str,
    application_date: str,
    interview_date: str,
    interview_notes: str,
) -> None:
    ctx.product_store.update_favorite(
        user_id=ctx.current_user_id,
        job_url=favorite.job_url,
        application_status=next_status,
        notes=next_notes,
        application_date=application_date,
        interview_date=interview_date,
        interview_notes=interview_notes,
    )
    set_main_tab("board")
    st.session_state.favorite_feedback = f"已更新投遞狀態：{favorite.title}"
    st.rerun()


def _delete_board_card(ctx: PageContext, favorite: FavoriteJob) -> None:
    ctx.product_store.delete_favorite(
        favorite.job_url,
        user_id=ctx.current_user_id,
    )
    set_main_tab("board")
    st.session_state.favorite_feedback = f"已刪除卡片：{favorite.title}"
    st.rerun()
