"""Task insight charts."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from .charts_shared import IMPORTANCE_DOMAIN, IMPORTANCE_RANGE, SCORE_GRADIENT, truncate_label


def render_task_insight_chart(frame: pd.DataFrame) -> None:
    """渲染工作內容洞察的橫向長條圖。"""
    if frame.empty:
        return

    chart_frame = frame.head(12).copy()
    chart_frame["item_label"] = chart_frame["item"].apply(truncate_label)
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
    chart_frame["item_label"] = chart_frame["item"].apply(truncate_label)
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
