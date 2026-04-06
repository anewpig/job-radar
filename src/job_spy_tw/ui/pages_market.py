"""提供職缺總覽、分析頁與匯出頁面的渲染函式。"""

from __future__ import annotations

from math import ceil

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
)
from .session import render_top_limit_control


def _build_pagination_tokens(total_pages: int, current_page: int) -> list[int | str]:
    """建立帶省略號的精簡分頁序列。"""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))
    if current_page <= 4:
        return [1, 2, 3, 4, 5, "...", total_pages]
    if current_page >= total_pages - 3:
        return [1, "...", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
    return [1, "...", current_page - 1, current_page, current_page + 1, "...", total_pages]


def _queue_overview_scroll_to_top() -> None:
    """在下一輪 rerun 後把視窗捲回職缺總覽卡片頂部。"""
    st.session_state.overview_scroll_to_top = True


def _render_overview_scroll_script() -> None:
    """若本輪需要自動捲動，就把視窗對齊到 overview 卡片頂部。"""
    if not st.session_state.pop("overview_scroll_to_top", False):
        return
    with st.container(key="overview-scroll-shell"):
        components.html(
            """
<script>
const scrollToOverviewTop = () => {
  const target = window.parent.document.getElementById("overview-top-anchor");
  if (!target) {
    window.setTimeout(scrollToOverviewTop, 120);
    return;
  }
  target.scrollIntoView({ behavior: "auto", block: "start" });
};
scrollToOverviewTop();
</script>
            """,
            height=0,
            width=0,
        )


def render_overview_page(ctx: PageContext) -> None:
    """渲染職缺總覽頁，包括篩選器、卡片列表與分頁。"""
    st.markdown('<div id="overview-top-anchor"></div>', unsafe_allow_html=True)
    _render_overview_scroll_script()
    with st.container(border=True, key="overview-shell"):
        pass
        st.markdown(
            f"""
<div class="section-shell overview-intro">
  <div class="overview-intro-main">
    <div class="section-kicker">{_escape("Overview")}</div>
    <div class="section-title">{_escape("職缺總覽")}</div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="overview-body"):
            with st.container(border=True, key="overview-filter-shell"):
                pass
                filter_cols = st.columns(3, gap="medium")
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
            filter_signature = "|".join(
                [
                    ctx.snapshot.generated_at,
                    ",".join(sorted(source_filter)),
                    ",".join(sorted(role_filter)),
                    ",".join(sorted(skill_filter)),
                    str(len(filtered)),
                ]
            )
            if st.session_state.get("overview_filter_signature") != filter_signature:
                st.session_state.overview_filter_signature = filter_signature
                st.session_state.overview_page = 1

            # 分頁必須在篩選之後計算，才能保證每一頁都只包含篩選後的結果。
            page_size = 10
            total_jobs = len(filtered)
            total_pages = max(1, ceil(total_jobs / page_size)) if total_jobs else 1
            current_page = int(st.session_state.get("overview_page", 1))
            current_page = max(1, min(current_page, total_pages))
            st.session_state.overview_page = current_page
            start_index = (current_page - 1) * page_size
            end_index = start_index + page_size
            visible_frame = filtered.iloc[start_index:end_index]
            summary_labels = [f"共 {total_jobs} 筆職缺", f"第 {current_page} / {total_pages} 頁"]
            if not filtered.empty:
                shown_start = start_index + 1
                shown_end = min(end_index, total_jobs)
                summary_labels.append(f"顯示 {shown_start}-{shown_end}")
            else:
                summary_labels.append("目前沒有符合條件的職缺")
            st.markdown(
                f"""
<div class="overview-filter-meta">
  <div class="chip-row">{build_chip_row(summary_labels, tone="soft", limit=4)}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
            render_job_cards(
                visible_frame,
                jobs_by_url=ctx.jobs_by_url,
                product_store=ctx.product_store,
                favorite_urls=ctx.favorite_urls,
                current_user_id=None if ctx.current_user_is_guest else ctx.current_user_id,
                favorites_enabled=not ctx.current_user_is_guest,
                active_saved_search_id=ctx.active_saved_search.id if ctx.active_saved_search else None,
                active_saved_search_name=ctx.active_saved_search.name if ctx.active_saved_search else "",
                details_pending=ctx.crawl_phase == "finalizing",
            )
            if total_jobs > page_size:
                # 分頁控制固定放在列表底部，避免切頁時把上方篩選器位置打亂。
                pagination_tokens = _build_pagination_tokens(total_pages, current_page)
                with st.container(key="overview-pagination-shell"):
                    outer_cols = st.columns([1.4, 3.2, 1.4], gap="small")
                    with outer_cols[1]:
                        inner_widths = [0.7] * (len(pagination_tokens) + 2)
                        pagination_cols = st.columns(inner_widths, gap="small")
                        with pagination_cols[0]:
                            if st.button(
                                "‹",
                                key="overview_prev_page",
                                use_container_width=True,
                                disabled=current_page <= 1,
                                type="secondary",
                            ):
                                st.session_state.overview_page = max(1, current_page - 1)
                                _queue_overview_scroll_to_top()
                                st.rerun()
                        for index, token in enumerate(pagination_tokens, start=1):
                            with pagination_cols[index]:
                                if token == "...":
                                    st.markdown("<div class='overview-pagination-ellipsis'>...</div>", unsafe_allow_html=True)
                                else:
                                    is_current = int(token) == current_page
                                    if st.button(
                                        str(token),
                                        key=f"overview-page-{token}",
                                        use_container_width=True,
                                        type="primary" if is_current else "secondary",
                                    ):
                                        if not is_current:
                                            st.session_state.overview_page = int(token)
                                            _queue_overview_scroll_to_top()
                                            st.rerun()
                        with pagination_cols[-1]:
                            if st.button(
                                "›",
                                key="overview_next_page",
                                use_container_width=True,
                                disabled=current_page >= total_pages,
                                type="secondary",
                            ):
                                st.session_state.overview_page = min(total_pages, current_page + 1)
                                _queue_overview_scroll_to_top()
                                st.rerun()


def _render_tasks_section(ctx: PageContext) -> None:
    """渲染工作內容統計區塊。"""
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
    pass
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">工作內容摘要</div>
  <div class="summary-card-text">{_escape(task_summary_text)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    filter_cols = st.columns([1.0], gap="medium")
    top_task_limit = render_top_limit_control(
        filter_cols[0],
        label="顯示前幾項",
        total_count=len(ctx.task_frame),
        key="task_top_limit",
        default_value=12,
    )
    filtered_task_frame = ctx.task_frame.copy()
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
    else:
        render_task_insight_bubble_chart(filtered_task_frame)
    with st.expander("查看工作內容明細表"):
        st.dataframe(
            filtered_task_frame if not filtered_task_frame.empty else ctx.task_frame,
            use_container_width=True,
            hide_index=True,
        )


def _render_skills_section(ctx: PageContext) -> None:
    """渲染技能地圖區塊。"""
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
    pass
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
        render_skill_bubble_chart(filtered_skill_frame)
    with st.expander("查看技能明細表"):
        st.dataframe(
            filtered_skill_frame if not filtered_skill_frame.empty else ctx.skill_frame,
            use_container_width=True,
            hide_index=True,
        )


def render_tasks_page(ctx: PageContext) -> None:
    """渲染合併後的工作內容統計與技能地圖頁。"""
    render_section_header(
        "工作內容 / 技能",
        "把工作內容統計與技能地圖集中在同一頁面，先看任務需求，再看技能熱點。",
        "Task + Skill Insight",
    )
    if ctx.crawl_phase == "finalizing":
        st.info("正在補完整分析，工作內容統計與技能地圖完成後會顯示在這裡。")
        return

    st.markdown("### 工作內容統計")
    st.caption("從職缺原文裡把最常出現的工作內容拉出來，先看任務熱點與優先順序。")
    _render_tasks_section(ctx)

    st.divider()

    st.markdown("### 技能地圖")
    st.caption("集中觀察市場最常要求的技能，補強方向可以直接對照這一區。")
    _render_skills_section(ctx)


def render_skills_page(ctx: PageContext) -> None:
    """保留舊技能地圖路由的相容入口。"""
    render_tasks_page(ctx)


def render_sources_page(ctx: PageContext) -> None:
    """渲染來源比較頁。"""
    render_section_header(
        "來源比較",
        "同時比較各平台職缺量與角色分布，快速看哪個來源更適合你現在的搜尋方向。",
        "Source Compare",
    )
    if ctx.crawl_phase == "finalizing":
        st.info("正在補完整分析，來源比較完成後會顯示在這裡。")
        return
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
        preview_tabs = st.tabs(["來源 × 角色", "職缺明細"])
        with preview_tabs[0]:
            st.dataframe(
                source_role_counts.sort_values(["source", "jobs"], ascending=[True, False]),
                use_container_width=True,
                hide_index=True,
            )
        with preview_tabs[1]:
            st.dataframe(
                ctx.job_frame[
                    ["source", "matched_role", "title", "company", "relevance_score"]
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_export_page(ctx: PageContext) -> None:
    """渲染目前快照的匯出操作與預覽表格。"""
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

    with st.container(border=True, key="export-shell"):
        pass
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
