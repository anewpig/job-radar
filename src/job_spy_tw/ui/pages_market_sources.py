"""Source comparison market page."""

from __future__ import annotations

import streamlit as st

from .charts import render_source_role_distribution_chart, render_source_summary_chart
from .common import render_section_header
from .page_context import PageContext


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
