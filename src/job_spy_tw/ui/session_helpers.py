"""跨頁共用的 session/UI helpers。"""

from __future__ import annotations

import streamlit as st

from ..models import MarketSnapshot
from .frames import jobs_to_frame, skills_to_frame, task_insights_to_frame


def assistant_question_batches(
    questions: list[str],
    batch_size: int = 4,
) -> list[list[str]]:
    """把 AI 助理的快捷問題切成固定大小的批次。"""
    cleaned = [str(question).strip() for question in questions if str(question).strip()]
    if not cleaned:
        return [[]]
    return [
        cleaned[index : index + batch_size]
        for index in range(0, len(cleaned), batch_size)
    ]


def render_top_limit_control(
    container,
    *,
    label: str,
    total_count: int,
    key: str,
    default_value: int,
    min_slider_value: int = 8,
    max_slider_value: int = 30,
) -> int:
    """渲染圖表前 N 筆控制器，並在資料太少時自動降級成文字提示。"""
    total_count = max(0, int(total_count))
    if total_count == 0:
        return 0
    if total_count <= min_slider_value:
        container.caption(f"{label}：目前共 {total_count} 項")
        return total_count
    return int(
        container.slider(
            label,
            min_value=min_slider_value,
            max_value=min(max_slider_value, total_count),
            value=min(default_value, total_count),
            step=1,
            key=key,
        )
    )


def set_main_tab(tab_id: str) -> None:
    """排程切換主頁籤，讓導覽元件在下次 rerun 時更新。"""
    st.session_state.main_tab_selection = tab_id
    st.session_state.pending_main_tab_selection = tab_id


def cache_snapshot_views(snapshot: MarketSnapshot) -> None:
    """快取目前快照轉出的 DataFrame 視圖，避免每次 rerun 都重算。"""
    snapshot_key = (
        f"{snapshot.generated_at}|{len(snapshot.jobs)}|"
        f"{len(snapshot.skills)}|{len(snapshot.task_insights)}"
    )
    if st.session_state.get("snapshot_view_cache_key") == snapshot_key:
        return
    st.session_state.snapshot_job_frame = jobs_to_frame(snapshot)
    st.session_state.snapshot_skill_frame = skills_to_frame(snapshot.skills)
    st.session_state.snapshot_task_frame = task_insights_to_frame(snapshot.task_insights)
    st.session_state.snapshot_jobs_by_url = {
        job.url: job for job in snapshot.jobs if job.url
    }
    st.session_state.snapshot_view_cache_key = snapshot_key
