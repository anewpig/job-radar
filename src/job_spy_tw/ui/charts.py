"""提供分析頁面會使用到的圖表渲染函式。"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

QUANTITY_GRADIENT = ["#dbeafe", "#93c5fd", "#2563eb"]
SCORE_GRADIENT = ["#e0f2fe", "#7dd3fc", "#2563eb"]
IMPORTANCE_DOMAIN = ["高", "中高", "中", "低"]
IMPORTANCE_RANGE = ["#16a34a", "#0ea5e9", "#60a5fa", "#cbd5e1"]
SOURCE_ROLE_RANGE = ["#1d4ed8", "#38bdf8", "#34d399", "#f59e0b", "#94a3b8", "#c084fc"]


def _truncate_label(text: str, limit: int = 20) -> str:
    """截短過長標籤，避免圖表上的文字難以閱讀。"""
    cleaned = str(text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}..."


def render_task_insight_chart(frame: pd.DataFrame) -> None:
    """渲染工作內容洞察的橫向長條圖。"""
    if frame.empty:
        return

    chart_frame = frame.head(12).copy()
    chart_frame["item_label"] = chart_frame["item"].apply(_truncate_label)
    chart_frame = chart_frame.sort_values("score", ascending=True)

    bars = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadius=10, size=28)
        .encode(
            x=alt.X(
                "score:Q",
                title="綜合分數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickCount=6),
            ),
            y=alt.Y(
                "item_label:N",
                sort=chart_frame["item_label"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=240),
            ),
            color=alt.Color(
                "score:Q",
                scale=alt.Scale(range=SCORE_GRADIENT),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("item:N", title="工作內容"),
                alt.Tooltip("score:Q", title="分數", format=".2f"),
                alt.Tooltip("occurrences:Q", title="出現次數"),
                alt.Tooltip("importance:N", title="重要度"),
                alt.Tooltip("sources:N", title="來源"),
            ],
        )
    )

    labels = bars.mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#0f172a",
        fontWeight=700,
    ).encode(text=alt.Text("score:Q", format=".1f"))

    chart = (
        (bars + labels)
        .properties(height=440)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#0f172a",
            titleColor="#334155",
            domain=False,
            tickColor="#cbd5e1",
        )
        .configure(background="#ffffff")
    )
    st.altair_chart(chart, use_container_width=True)


def render_task_insight_bubble_chart(frame: pd.DataFrame) -> None:
    """渲染工作內容洞察的泡泡圖。"""
    if frame.empty:
        return

    chart_frame = frame.head(12).copy()
    chart_frame["item_label"] = chart_frame["item"].apply(_truncate_label)
    chart_frame = chart_frame.sort_values("score", ascending=True)

    bubbles = (
        alt.Chart(chart_frame)
        .mark_circle(opacity=0.82, stroke="#ffffff", strokeWidth=1.5)
        .encode(
            x=alt.X(
                "occurrences:Q",
                title="出現次數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickMinStep=1),
            ),
            y=alt.Y(
                "item_label:N",
                sort=chart_frame["item_label"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=240),
            ),
            size=alt.Size(
                "score:Q",
                title="分數",
                scale=alt.Scale(range=[250, 1800]),
                legend=None,
            ),
            color=alt.Color(
                "importance:N",
                title="重要度",
                scale=alt.Scale(
                    domain=IMPORTANCE_DOMAIN,
                    range=IMPORTANCE_RANGE,
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("item:N", title="工作內容"),
                alt.Tooltip("score:Q", title="分數", format=".2f"),
                alt.Tooltip("occurrences:Q", title="出現次數"),
                alt.Tooltip("importance:N", title="重要度"),
                alt.Tooltip("sources:N", title="來源"),
            ],
        )
    )

    score_labels = (
        alt.Chart(chart_frame)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,
            color="#0f172a",
            fontSize=11,
            fontWeight=700,
        )
        .encode(
            x=alt.X("occurrences:Q"),
            y=alt.Y("item_label:N", sort=chart_frame["item_label"].tolist()),
            text=alt.Text("score:Q", format=".1f"),
        )
    )

    chart = (
        (bubbles + score_labels)
        .properties(height=460)
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


def render_skill_bubble_chart(frame: pd.DataFrame) -> None:
    """渲染技能需求的泡泡圖。"""
    if frame.empty:
        return

    chart_frame = frame.head(14).copy()
    chart_frame["skill_label"] = chart_frame["skill"].apply(_truncate_label)
    chart_frame = chart_frame.sort_values("score", ascending=True)

    bubbles = (
        alt.Chart(chart_frame)
        .mark_circle(opacity=0.84, stroke="#ffffff", strokeWidth=1.5)
        .encode(
            x=alt.X(
                "occurrences:Q",
                title="出現次數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickMinStep=1),
            ),
            y=alt.Y(
                "skill_label:N",
                sort=chart_frame["skill_label"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=240),
            ),
            size=alt.Size(
                "score:Q",
                title="分數",
                scale=alt.Scale(range=[220, 1700]),
                legend=None,
            ),
            color=alt.Color(
                "importance:N",
                title="重要度",
                scale=alt.Scale(
                    domain=IMPORTANCE_DOMAIN,
                    range=IMPORTANCE_RANGE,
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("skill:N", title="技能"),
                alt.Tooltip("category:N", title="分類"),
                alt.Tooltip("score:Q", title="分數", format=".2f"),
                alt.Tooltip("occurrences:Q", title="出現次數"),
                alt.Tooltip("importance:N", title="重要度"),
                alt.Tooltip("sources:N", title="來源"),
            ],
        )
    )

    score_labels = (
        alt.Chart(chart_frame)
        .mark_text(
            align="left",
            baseline="middle",
            dx=10,
            color="#0f172a",
            fontSize=11,
            fontWeight=700,
        )
        .encode(
            x=alt.X("occurrences:Q"),
            y=alt.Y("skill_label:N", sort=chart_frame["skill_label"].tolist()),
            text=alt.Text("score:Q", format=".1f"),
        )
    )

    chart = (
        (bubbles + score_labels)
        .properties(height=500)
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
