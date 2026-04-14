"""Export/download market page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .common import _escape
from .dev_annotations import render_dev_card_annotation
from .frames import (
    build_export_bundle,
    filter_jobs_frame,
    flatten_job_download_frame,
    resume_matches_to_frame,
    sanitize_export_name,
)
from .page_context import PageContext


def render_export_page(ctx: PageContext) -> None:
    """渲染目前快照的匯出操作與預覽表格。"""
    current_filtered_frame = filter_jobs_frame(
        ctx.job_frame,
        source_filter=st.session_state.get("overview_source_filter", []),
        role_filter=st.session_state.get("overview_role_filter", []),
        skill_filter=st.session_state.get("overview_skill_filter", []),
        sort_mode=st.session_state.get("overview_sort_mode", "relevance"),
    )
    full_download_frame = flatten_job_download_frame(ctx.job_frame)
    filtered_download_frame = flatten_job_download_frame(current_filtered_frame)
    resume_match_frame = (
        resume_matches_to_frame(st.session_state.resume_matches)
        if st.session_state.resume_matches
        else pd.DataFrame()
    )
    export_base_name = sanitize_export_name(
        f"{ctx.current_search_name}_{ctx.snapshot.generated_at.replace(':', '').replace('-', '').replace('T', '_')}",
        fallback="job_radar_export",
    )
    export_metadata = {
        "generated_at": ctx.snapshot.generated_at,
        "queries": ctx.snapshot.queries,
        "search_name": ctx.current_search_name,
        "crawl_preset_label": st.session_state.crawl_preset_label,
        "filters": {
            "source": st.session_state.get("overview_source_filter", []),
            "matched_role": st.session_state.get("overview_role_filter", []),
            "skill": st.session_state.get("overview_skill_filter", []),
            "sort_mode": st.session_state.get("overview_sort_mode", "relevance"),
        },
        "counts": {
            "jobs_full": int(len(ctx.job_frame)),
            "jobs_filtered": int(len(current_filtered_frame)),
            "skills": int(len(ctx.skill_frame)),
            "tasks": int(len(ctx.task_frame)),
            "resume_matches": int(len(resume_match_frame)),
        },
    }
    bundle_bytes = build_export_bundle(
        full_jobs_frame=ctx.job_frame,
        filtered_jobs_frame=current_filtered_frame,
        skill_frame=ctx.skill_frame,
        task_frame=ctx.task_frame,
        resume_match_frame=resume_match_frame if not resume_match_frame.empty else None,
        metadata=export_metadata,
    )

    summary_cols = st.columns(4)
    summary_cols[0].metric("完整職缺", len(ctx.job_frame))
    summary_cols[1].metric("目前篩選結果", len(current_filtered_frame))
    summary_cols[2].metric("技能統計", len(ctx.skill_frame))
    summary_cols[3].metric("工作內容統計", len(ctx.task_frame))

    has_active_filters = any(
        [
            st.session_state.get("overview_source_filter", []),
            st.session_state.get("overview_role_filter", []),
            st.session_state.get("overview_skill_filter", []),
        ]
    )
    current_results_label = (
        f"下載目前畫面結果（{len(current_filtered_frame)} 筆）"
        if has_active_filters
        else f"下載目前畫面結果（全部 {len(current_filtered_frame)} 筆）"
    )

    with st.container(border=True, key="export-shell"):
        render_dev_card_annotation(
            "下載資料頁主卡",
            element_id="export-shell",
            description="資料匯出頁的外層卡片，包含常用下載、更多格式與預覽。",
            layers=[
                "export-body",
                "primary download buttons",
                "extra download formats",
                "preview tabs",
            ],
            text_nodes=[
                ("section-kicker", "頁首小標。"),
                ("section-title", "頁面主標題。"),
                ("section-desc", "頁面說明文字。"),
                ("download_button label", "下載按鈕文字。"),
            ],
            show_popover=True,
            popover_key="export-shell",
        )
        st.markdown(
            f"""
<div class="section-shell export-intro">
  <div class="section-kicker">{_escape("Export")}</div>
  <div class="section-title">{_escape("下載資料")}</div>
  <div class="section-desc">{_escape("把目前快照、技能統計與履歷匹配結果帶走，後續要整理報表或匯入其他系統都方便。")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="export-body"):
            st.markdown("**常用下載**")
            st.caption(
                "先下載目前正在看的結果，或直接帶走完整資料包。ZIP 內會包含職缺、技能、工作內容與內部描述檔。"
            )
            primary_download_cols = st.columns(2, gap="large")
            primary_download_cols[0].download_button(
                current_results_label,
                data=filtered_download_frame.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{export_base_name}_jobs_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
            primary_download_cols[1].download_button(
                "下載完整資料包 ZIP",
                data=bundle_bytes,
                file_name=f"{export_base_name}_bundle.zip",
                mime="application/zip",
                use_container_width=True,
            )

            with st.expander("更多下載格式", expanded=False):
                st.caption("適合做報表、交叉分析，或匯入其他系統再利用。")
                extra_download_cols = st.columns(4)
                extra_download_cols[0].download_button(
                    f"全部職缺 CSV（{len(ctx.job_frame)} 筆）",
                    data=full_download_frame.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{export_base_name}_jobs_full.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                extra_download_cols[1].download_button(
                    f"技能統計 CSV（{len(ctx.skill_frame)} 筆）",
                    data=ctx.skill_frame.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{export_base_name}_skills.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                extra_download_cols[2].download_button(
                    f"工作內容 CSV（{len(ctx.task_frame)} 筆）",
                    data=ctx.task_frame.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"{export_base_name}_tasks.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                if not resume_match_frame.empty:
                    extra_download_cols[3].download_button(
                        f"履歷匹配 CSV（{len(resume_match_frame)} 筆）",
                        data=resume_match_frame.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"{export_base_name}_resume_matches.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            with st.expander("查看下載前資料預覽", expanded=False):
                st.caption("預設先看前 20 筆，避免整頁預覽太重。")
                preview_tabs = st.tabs(["目前畫面結果", "全部職缺", "技能統計", "工作內容統計"])
                with preview_tabs[0]:
                    st.dataframe(
                        filtered_download_frame.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )
                with preview_tabs[1]:
                    st.dataframe(
                        full_download_frame.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )
                with preview_tabs[2]:
                    st.dataframe(
                        ctx.skill_frame.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )
                with preview_tabs[3]:
                    st.dataframe(
                        ctx.task_frame.head(20),
                        use_container_width=True,
                        hide_index=True,
                    )
