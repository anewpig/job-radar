"""Source comparison charts."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from .charts_shared import QUANTITY_GRADIENT, SOURCE_ROLE_RANGE


def render_source_summary_chart(frame: pd.DataFrame) -> None:
    """渲染各來源職缺量與平均相關分數摘要圖。"""
    if frame.empty:
        return

    chart_frame = frame.copy().sort_values("jobs", ascending=False)
    chart_frame["job_label"] = chart_frame["jobs"].map(lambda value: f"{int(value)} 筆")
    chart_frame["score_label"] = chart_frame["avg_relevance"].map(
        lambda value: f"平均 {float(value):.1f}"
    )

    bars = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadiusTopLeft=12, cornerRadiusTopRight=12, size=72)
        .encode(
            x=alt.X(
                "source:N",
                sort=chart_frame["source"].tolist(),
                title=None,
                axis=alt.Axis(labelAngle=0, labelPadding=14),
            ),
            y=alt.Y(
                "jobs:Q",
                title="職缺數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickMinStep=1),
            ),
            color=alt.Color(
                "avg_relevance:Q",
                title="平均相關分數",
                scale=alt.Scale(range=QUANTITY_GRADIENT),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("source:N", title="來源"),
                alt.Tooltip("jobs:Q", title="職缺數"),
                alt.Tooltip("avg_relevance:Q", title="平均相關分數", format=".1f"),
                alt.Tooltip("top_role:N", title="主要角色"),
            ],
        )
    )
    job_labels = (
        alt.Chart(chart_frame)
        .mark_text(
            dy=-12,
            color="#0f172a",
            fontWeight=800,
            fontSize=12,
        )
        .encode(
            x=alt.X("source:N", sort=chart_frame["source"].tolist()),
            y=alt.Y("jobs:Q"),
            text="job_label:N",
        )
    )
    score_labels = (
        alt.Chart(chart_frame)
        .mark_text(
            dy=-30,
            color="#475569",
            fontWeight=700,
            fontSize=11,
        )
        .encode(
            x=alt.X("source:N", sort=chart_frame["source"].tolist()),
            y=alt.Y("jobs:Q"),
            text="score_label:N",
        )
    )

    chart = (
        (bars + job_labels + score_labels)
        .properties(height=360)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#0f172a",
            titleColor="#334155",
            domain=False,
            tickColor="#cbd5e1",
        )
        .configure_legend(
            labelColor="#0f172a",
            titleColor="#334155",
            orient="top",
        )
        .configure(background="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_source_role_distribution_chart(frame: pd.DataFrame) -> None:
    """渲染各來源在不同角色上的堆疊分布圖。"""
    if frame.empty:
        return

    chart_frame = frame.copy()
    role_order = (
        chart_frame.groupby("matched_role")["jobs"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    source_order = (
        chart_frame.groupby("source")["jobs"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    bars = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadiusEnd=8, cornerRadiusTopLeft=8, cornerRadiusBottomLeft=8, size=30)
        .encode(
            x=alt.X(
                "jobs:Q",
                title="職缺數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickMinStep=1),
            ),
            y=alt.Y(
                "source:N",
                sort=source_order,
                title=None,
                axis=alt.Axis(labelLimit=180),
            ),
            color=alt.Color(
                "matched_role:N",
                title="角色",
                sort=role_order,
                scale=alt.Scale(
                    range=SOURCE_ROLE_RANGE
                ),
                legend=alt.Legend(orient="top"),
            ),
            order=alt.Order("jobs:Q", sort="descending"),
            tooltip=[
                alt.Tooltip("source:N", title="來源"),
                alt.Tooltip("matched_role:N", title="角色"),
                alt.Tooltip("jobs:Q", title="職缺數"),
            ],
        )
    )

    chart = (
        bars.properties(height=max(240, min(420, 78 * len(source_order))))
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#0f172a",
            titleColor="#334155",
            domain=False,
            tickColor="#cbd5e1",
        )
        .configure_legend(
            labelColor="#0f172a",
            titleColor="#334155",
            orient="top",
        )
        .configure(background="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)
