"""Skill charts."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from .charts_shared import IMPORTANCE_DOMAIN, IMPORTANCE_RANGE, truncate_label


def render_skill_bubble_chart(frame: pd.DataFrame) -> None:
    """渲染技能需求的泡泡圖。"""
    if frame.empty:
        return

    chart_frame = frame.head(14).copy()
    chart_frame["skill_label"] = chart_frame["skill"].apply(truncate_label)
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
