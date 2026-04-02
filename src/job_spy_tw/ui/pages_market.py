from __future__ import annotations

import pandas as pd
import streamlit as st

from .common import _escape, build_chip_row, render_section_header
from .frames import (
    build_export_bundle,
    filter_jobs_frame,
    flatten_job_download_frame,
    resume_matches_to_frame,
    sanitize_export_name,
)
from .page_context import PageContext
from .renderers import render_job_cards
from .charts import (
    render_skill_bubble_chart,
    render_source_role_distribution_chart,
    render_source_summary_chart,
    render_task_insight_bubble_chart,
    render_task_insight_chart,
)
from .session import render_top_limit_control


def render_overview_page(ctx: PageContext) -> None:
    render_section_header("職缺總覽", "", "Overview")
    filter_cols = st.columns(3)
    source_filter = filter_cols[0].multiselect(
        "來源",
        sorted(ctx.job_frame["source"].unique()) if not ctx.job_frame.empty else [],
        key="overview_source_filter",
    )
    role_filter = filter_cols[1].multiselect(
        "匹配角色",
        sorted(ctx.job_frame["matched_role"].unique()) if not ctx.job_frame.empty else [],
        key="overview_role_filter",
    )
    skill_filter = filter_cols[2].multiselect(
        "技能",
        sorted(ctx.skill_frame["skill"].unique()) if not ctx.skill_frame.empty else [],
        key="overview_skill_filter",
    )
    filtered = filter_jobs_frame(
        ctx.job_frame,
        source_filter=source_filter,
        role_filter=role_filter,
        skill_filter=skill_filter,
    )
    if ctx.current_user_is_guest:
        st.caption("登入後可以收藏職缺、建立自己的追蹤中心與投遞看板。")
    render_job_cards(
        filtered,
        jobs_by_url=ctx.jobs_by_url,
        product_store=ctx.product_store,
        favorite_urls=ctx.favorite_urls,
        current_user_id=None if ctx.current_user_is_guest else ctx.current_user_id,
        favorites_enabled=not ctx.current_user_is_guest,
        active_saved_search_id=ctx.active_saved_search.id if ctx.active_saved_search else None,
        active_saved_search_name=ctx.active_saved_search.name if ctx.active_saved_search else "",
    )


def render_tasks_page(ctx: PageContext) -> None:
    render_section_header(
        "工作內容統計",
        "從職缺原文裡把最常出現的工作內容拉出來，你可以切換排名圖或氣泡圖觀察需求熱點。",
        "Task Insight",
    )
    if ctx.task_frame.empty:
        st.info("目前沒有足夠的工作內容條目可供統計。")
        return

    top_task_labels = (
        ctx.task_frame.sort_values("score", ascending=False)["item"].head(3).tolist()
    )
    high_task_count = int((ctx.task_frame["importance"] == "高").sum())
    task_summary_text = (
        f"目前最常出現的工作內容是 {', '.join(top_task_labels)}，"
        f"其中高重要度主題共有 {high_task_count} 項。"
        if top_task_labels
        else "目前已整理出職缺常見工作內容。"
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">工作內容摘要</div>
  <div class="summary-card-text">{_escape(task_summary_text)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    filter_cols = st.columns([1.0, 0.9, 1.0], gap="medium")
    task_importance_options = sorted(
        value
        for value in ctx.task_frame["importance"].dropna().unique().tolist()
        if str(value).strip()
    )
    selected_task_importance = filter_cols[0].multiselect(
        "重要度",
        task_importance_options,
        default=[],
        key="task_importance_filter",
    )
    top_task_limit = render_top_limit_control(
        filter_cols[1],
        label="顯示前幾項",
        total_count=len(ctx.task_frame),
        key="task_top_limit",
        default_value=12,
    )
    chart_style = st.radio(
        "圖表樣式",
        options=["排名圖", "氣泡圖"],
        horizontal=True,
        key="task_chart_style",
    )
    filtered_task_frame = ctx.task_frame.copy()
    if selected_task_importance:
        filtered_task_frame = filtered_task_frame[
            filtered_task_frame["importance"].isin(selected_task_importance)
        ]
    filtered_task_frame = filtered_task_frame.sort_values("score", ascending=False).head(
        top_task_limit
    )
    focus_task_labels = filtered_task_frame["item"].head(5).tolist()
    st.markdown(
        f"<div class='chip-row'>{build_chip_row([f'可優先關注 {label}' for label in focus_task_labels], tone='warm', limit=5, empty_text='目前沒有符合條件的工作內容')}</div>",
        unsafe_allow_html=True,
    )
    if filtered_task_frame.empty:
        st.info("目前篩選條件下沒有符合的工作內容主題。")
    elif chart_style == "氣泡圖":
        st.caption("氣泡越大代表分數越高，越靠右代表出現次數越多。")
        render_task_insight_bubble_chart(filtered_task_frame)
    else:
        st.caption("前 12 名工作內容主題，顏色越深代表整體分數越高。")
        render_task_insight_chart(filtered_task_frame)
    with st.expander("查看工作內容明細表"):
        st.dataframe(
            filtered_task_frame if not filtered_task_frame.empty else ctx.task_frame,
            use_container_width=True,
            hide_index=True,
        )


def render_skills_page(ctx: PageContext) -> None:
    render_section_header(
        "技能地圖",
        "這裡會集中看市場最常要求的技能，氣泡越大代表綜合權重越高。",
        "Skill Map",
    )
    if ctx.skill_frame.empty:
        st.info("目前沒有足夠的技能資料可供統計。")
        return

    top_skill_labels = (
        ctx.skill_frame.sort_values("score", ascending=False)["skill"].head(3).tolist()
    )
    high_importance_count = int((ctx.skill_frame["importance"] == "高").sum())
    category_options = sorted(
        value
        for value in ctx.skill_frame["category"].dropna().unique().tolist()
        if str(value).strip()
    )
    importance_options = sorted(
        value
        for value in ctx.skill_frame["importance"].dropna().unique().tolist()
        if str(value).strip()
    )
    summary_text = (
        f"目前最值得先關注的技能是 {', '.join(top_skill_labels)}，"
        f"其中高重要度技能共有 {high_importance_count} 項。"
        if top_skill_labels
        else "目前已整理出市場常見技能，你可以先從高分項目開始看。"
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">技能摘要</div>
  <div class="summary-card-text">{_escape(summary_text)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    filter_cols = st.columns([1.05, 1.0, 0.95], gap="medium")
    selected_skill_categories = filter_cols[0].multiselect(
        "技能分類",
        category_options,
        default=[],
        key="skill_category_filter",
    )
    selected_skill_importance = filter_cols[1].multiselect(
        "重要度",
        importance_options,
        default=[],
        key="skill_importance_filter",
    )
    top_skill_limit = render_top_limit_control(
        filter_cols[2],
        label="顯示前幾項",
        total_count=len(ctx.skill_frame),
        key="skill_top_limit",
        default_value=14,
    )
    filtered_skill_frame = ctx.skill_frame.copy()
    if selected_skill_categories:
        filtered_skill_frame = filtered_skill_frame[
            filtered_skill_frame["category"].isin(selected_skill_categories)
        ]
    if selected_skill_importance:
        filtered_skill_frame = filtered_skill_frame[
            filtered_skill_frame["importance"].isin(selected_skill_importance)
        ]
    filtered_skill_frame = filtered_skill_frame.sort_values("score", ascending=False).head(
        top_skill_limit
    )
    learning_labels = filtered_skill_frame["skill"].head(5).tolist()
    st.markdown(
        f"<div class='chip-row'>{build_chip_row([f'可優先補強 {label}' for label in learning_labels], tone='warm', limit=5, empty_text='目前沒有符合條件的技能')}</div>",
        unsafe_allow_html=True,
    )
    if filtered_skill_frame.empty:
        st.info("目前篩選條件下沒有符合的技能。")
    else:
        st.caption("氣泡越大代表分數越高，越靠右代表出現次數越多。")
        render_skill_bubble_chart(filtered_skill_frame)
    with st.expander("查看技能明細表"):
        st.dataframe(
            filtered_skill_frame if not filtered_skill_frame.empty else ctx.skill_frame,
            use_container_width=True,
            hide_index=True,
        )


def render_sources_page(ctx: PageContext) -> None:
    render_section_header(
        "來源比較",
        "同時比較各平台職缺量與角色分布，快速看哪個來源更適合你現在的搜尋方向。",
        "Source Compare",
    )
    if ctx.job_frame.empty:
        st.info("目前沒有可比較的資料。")
        return

    source_role_frame = ctx.job_frame.copy()
    source_role_frame["matched_role"] = source_role_frame["matched_role"].fillna("").replace(
        "", "未標記角色"
    )
    top_role_limit = min(6, max(3, source_role_frame["matched_role"].nunique()))
    top_roles = (
        source_role_frame.groupby("matched_role")
        .size()
        .sort_values(ascending=False)
        .head(top_role_limit)
        .index.tolist()
    )
    source_role_frame["matched_role"] = source_role_frame["matched_role"].apply(
        lambda value: value if value in top_roles else "其他角色"
    )
    source_summary = (
        source_role_frame.groupby("source")
        .agg(
            jobs=("source", "size"),
            avg_relevance=("relevance_score", "mean"),
        )
        .reset_index()
    )
    top_role_by_source = (
        source_role_frame.groupby(["source", "matched_role"])
        .size()
        .reset_index(name="jobs")
        .sort_values(["source", "jobs"], ascending=[True, False])
        .drop_duplicates("source")
        .rename(columns={"matched_role": "top_role"})
    )
    source_summary = source_summary.merge(
        top_role_by_source[["source", "top_role"]],
        on="source",
        how="left",
    )
    source_role_counts = (
        source_role_frame.groupby(["source", "matched_role"])
        .size()
        .reset_index(name="jobs")
    )
    strongest_source_row = source_summary.sort_values(
        ["jobs", "avg_relevance"],
        ascending=False,
    ).iloc[0]
    strongest_source = str(strongest_source_row["source"])
    strongest_source_jobs = int(strongest_source_row["jobs"])
    strongest_source_role = str(strongest_source_row["top_role"] or "未標記角色")
    source_summary_text = (
        f"這次搜尋中，{strongest_source} 的職缺量最多，共 {strongest_source_jobs} 筆，"
        f"而且主要集中在 {strongest_source_role}。"
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">來源摘要</div>
  <div class="summary-card-text">{_escape(source_summary_text)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    summary_metrics = st.columns(3, gap="medium")
    summary_metrics[0].metric("來源數", int(source_summary["source"].nunique()))
    summary_metrics[1].metric("最多職缺來源", strongest_source)
    summary_metrics[2].metric(
        "最高平均相關分數",
        source_summary.sort_values("avg_relevance", ascending=False).iloc[0]["source"],
    )
    st.caption("各來源職缺數與平均相關分數")
    render_source_summary_chart(source_summary)
    st.caption("各來源角色分布")
    render_source_role_distribution_chart(source_role_counts)
    with st.expander("查看來源比較明細表"):
        preview_tabs = st.tabs(["來源摘要", "來源 × 角色", "職缺明細"])
        with preview_tabs[0]:
            st.dataframe(
                source_summary.sort_values("jobs", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        with preview_tabs[1]:
            st.dataframe(
                source_role_counts.sort_values(["source", "jobs"], ascending=[True, False]),
                use_container_width=True,
                hide_index=True,
            )
        with preview_tabs[2]:
            st.dataframe(
                ctx.job_frame[
                    ["source", "matched_role", "title", "company", "relevance_score"]
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_export_page(ctx: PageContext) -> None:
    render_section_header(
        "下載資料",
        "把目前快照、技能統計與履歷匹配結果帶走，後續要整理報表或匯入其他系統都方便。",
        "Export",
    )
    current_filtered_frame = filter_jobs_frame(
        ctx.job_frame,
        source_filter=st.session_state.get("overview_source_filter", []),
        role_filter=st.session_state.get("overview_role_filter", []),
        skill_filter=st.session_state.get("overview_skill_filter", []),
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

    with st.container(border=True):
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
