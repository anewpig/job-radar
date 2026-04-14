"""Tasks and skills pages for market insights."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

from .charts import render_skill_bubble_chart, render_task_insight_bubble_chart
from .common import _escape, build_chip_row
from .dev_annotations import render_dev_card_annotation
from .page_context import PageContext
from .session import render_top_limit_control


def _render_market_report_heading(title: str, description: str) -> None:
    """渲染置中的區塊標題與說明。"""
    st.markdown(
        f"""
<div class="market-report-heading">
  <div class="market-report-heading-title">{_escape(title)}</div>
  <div class="market-report-heading-copy">{_escape(description)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_tasks_intro() -> None:
    """渲染工作內容 / 技能頁首，沿用職缺總覽的 intro 語言。"""
    st.markdown(
        f"""
<div class="section-shell tasks-intro">
  <div class="tasks-intro-main">
    <div class="section-kicker">{_escape("Task + Skill Insight")}</div>
    <div class="section-title">{_escape("工作內容 / 技能")}</div>
    <div class="section-desc">{_escape("把工作內容統計與技能地圖集中在同一頁面，先看任務需求，再看技能熱點。")}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _normalize_scalar(value: object, fallback: str) -> str:
    """把值整理成穩定可顯示的字串。"""
    if value is None:
        return fallback
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return fallback
    except TypeError:
        pass
    text = str(value).strip()
    return text or fallback


def _normalize_items(value: object) -> list[str]:
    """把 job frame 內的 list-like 欄位整理成乾淨字串清單。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        try:
            if pd.isna(value):  # type: ignore[arg-type]
                return []
        except TypeError:
            pass
        text = str(value).strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, (list, tuple, set)):
                    raw_items = list(parsed)
                else:
                    raw_items = [text]
            except (ValueError, SyntaxError):
                raw_items = [text]
        else:
            normalized_text = text.replace("|", "、").replace(",", "、")
            raw_items = [part.strip() for part in normalized_text.split("、")]

    items: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        cleaned = str(item).strip()
        if not cleaned or cleaned.lower() == "nan" or cleaned in seen:
            continue
        seen.add(cleaned)
        items.append(cleaned)
    return items


def _join_top_labels(counter: Counter[str], limit: int = 3, fallback: str = "—") -> str:
    """把計數器整理成前幾名標籤文字。"""
    if not counter:
        return fallback
    return "、".join(label for label, _ in counter.most_common(limit))


def _join_titles(titles: list[str], fallback: str = "—") -> str:
    """把代表職缺整理成精簡可讀的字串。"""
    if not titles:
        return fallback
    return " | ".join(titles[:2])


def _build_group_comparison_frame(job_frame: pd.DataFrame, group_column: str, group_label: str) -> pd.DataFrame:
    """建立來源 / 職缺類型比較表。"""
    if job_frame.empty:
        return pd.DataFrame(
            columns=[group_label, "職缺數", "Top 工作內容", "Top 技能", "代表職缺"]
        )

    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "count": 0,
            "tasks": Counter(),
            "skills": Counter(),
            "jobs": [],
        }
    )

    for _, row in job_frame.iterrows():
        group_name = _normalize_scalar(row.get(group_column), "未分類")
        title = _normalize_scalar(row.get("title"), "未命名職缺")
        tasks = _normalize_items(row.get("work_content_items"))
        skills = _normalize_items(row.get("required_skill_items"))
        slot = grouped[group_name]
        slot["count"] = int(slot["count"]) + 1
        cast_tasks: Counter[str] = slot["tasks"]  # type: ignore[assignment]
        cast_skills: Counter[str] = slot["skills"]  # type: ignore[assignment]
        cast_tasks.update(tasks)
        cast_skills.update(skills)
        cast_jobs: list[str] = slot["jobs"]  # type: ignore[assignment]
        if title not in cast_jobs and len(cast_jobs) < 3:
            cast_jobs.append(title)

    rows: list[dict[str, object]] = []
    for group_name, slot in grouped.items():
        task_counter: Counter[str] = slot["tasks"]  # type: ignore[assignment]
        skill_counter: Counter[str] = slot["skills"]  # type: ignore[assignment]
        rows.append(
            {
                group_label: group_name,
                "職缺數": int(slot["count"]),
                "Top 工作內容": _join_top_labels(task_counter),
                "Top 技能": _join_top_labels(skill_counter),
                "代表職缺": _join_titles(slot["jobs"]),  # type: ignore[arg-type]
                "_top_signal": max(
                    task_counter.most_common(1)[0][1] if task_counter else 0,
                    skill_counter.most_common(1)[0][1] if skill_counter else 0,
                ),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[group_label, "職缺數", "Top 工作內容", "Top 技能", "代表職缺"]
        )
    return (
        frame.sort_values(["職缺數", "_top_signal", group_label], ascending=[False, False, True])
        .drop(columns="_top_signal")
        .reset_index(drop=True)
    )


def _build_task_skill_crosswalk_frame(job_frame: pd.DataFrame) -> pd.DataFrame:
    """建立工作內容 × 技能對照表。"""
    if job_frame.empty:
        return pd.DataFrame(
            columns=["工作內容", "最常一起出現的技能", "關聯次數", "代表職缺", "來源"]
        )

    task_skill_counter: dict[str, Counter[str]] = defaultdict(Counter)
    task_occurrences: Counter[str] = Counter()
    task_sources: dict[str, Counter[str]] = defaultdict(Counter)
    task_jobs: dict[str, list[str]] = defaultdict(list)

    for _, row in job_frame.iterrows():
        title = _normalize_scalar(row.get("title"), "未命名職缺")
        source = _normalize_scalar(row.get("source"), "未知來源")
        tasks = _normalize_items(row.get("work_content_items"))
        skills = _normalize_items(row.get("required_skill_items"))
        if not tasks or not skills:
            continue

        for task in tasks:
            task_occurrences[task] += 1
            task_sources[task][source] += 1
            if title not in task_jobs[task] and len(task_jobs[task]) < 3:
                task_jobs[task].append(title)
            for skill in skills:
                task_skill_counter[task][skill] += 1

    rows: list[dict[str, object]] = []
    for task, skill_counter in task_skill_counter.items():
        rows.append(
            {
                "工作內容": task,
                "最常一起出現的技能": _join_top_labels(skill_counter, limit=3),
                "關聯次數": int(sum(skill_counter.values())),
                "代表職缺": _join_titles(task_jobs.get(task, [])),
                "來源": _join_top_labels(task_sources.get(task, Counter()), limit=2),
                "_task_occurrences": int(task_occurrences.get(task, 0)),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=["工作內容", "最常一起出現的技能", "關聯次數", "代表職缺", "來源"]
        )
    return (
        frame.sort_values(
            ["關聯次數", "_task_occurrences", "工作內容"],
            ascending=[False, False, True],
        )
        .drop(columns="_task_occurrences")
        .reset_index(drop=True)
    )


def _build_skill_priority_frame(skill_frame: pd.DataFrame) -> pd.DataFrame:
    """建立最值得補強技能表。"""
    if skill_frame.empty:
        return pd.DataFrame(
            columns=["技能", "技能類別", "重要度", "需求次數", "代表職缺", "來源"]
        )

    frame = skill_frame.copy()
    frame = frame.sort_values(["score", "occurrences"], ascending=[False, False]).reset_index(drop=True)
    if "sample_jobs" in frame.columns:
        frame["sample_jobs"] = frame["sample_jobs"].apply(
            lambda value: _join_titles([item.strip() for item in str(value).split("|") if item.strip()])
        )
    if "sources" in frame.columns:
        frame["sources"] = frame["sources"].apply(
            lambda value: _join_top_labels(Counter(_normalize_items(value)), limit=2)
        )
    frame = frame.rename(
        columns={
            "skill": "技能",
            "category": "技能類別",
            "importance": "重要度",
            "occurrences": "需求次數",
            "sample_jobs": "代表職缺",
            "sources": "來源",
        }
    )
    return frame[["技能", "技能類別", "重要度", "需求次數", "代表職缺", "來源"]]


def _render_report_table(
    title: str,
    description: str,
    data_frame: pd.DataFrame,
    key: str,
    empty_text: str,
) -> None:
    """用共用樣式渲染決策型報表。"""
    with st.container(border=True, key=key):
        st.markdown(
            f"""
<div class="report-card-head">
  <div class="report-card-title">{_escape(title)}</div>
  <div class="report-card-copy">{_escape(description)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        if data_frame.empty:
            st.info(empty_text)
        else:
            st.dataframe(data_frame, use_container_width=True, hide_index=True)


def _render_group_comparison_reports(ctx: PageContext) -> None:
    """渲染來源 / 職缺類型比較表。"""
    source_frame = _build_group_comparison_frame(ctx.job_frame, "source", "來源")
    role_frame = _build_group_comparison_frame(ctx.job_frame, "matched_role", "職缺類型")
    source_tab, role_tab = st.tabs(["來源比較", "職缺類型比較"])
    with source_tab:
        _render_report_table(
            "來源比較表",
            "先看不同平台主要在要哪些工作內容與技能。",
            source_frame,
            key="market-report-source-compare",
            empty_text="目前沒有足夠的來源資料可供比較。",
        )
    with role_tab:
        _render_report_table(
            "職缺類型比較表",
            "快速比較不同對應職缺最常搭配的任務與技能。",
            role_frame,
            key="market-report-role-compare",
            empty_text="目前沒有足夠的職缺類型資料可供比較。",
        )


def _render_tasks_section(ctx: PageContext) -> None:
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
    render_dev_card_annotation(
        "工作內容摘要卡",
        element_id="task-summary-card",
        description="工作內容統計區上方的摘要與導引卡片。",
        layers=[
            "summary-card",
            "task_top_limit",
            "task insight chart",
        ],
        text_nodes=[
            ("info-card-title", "摘要卡主標文字。"),
            ("summary-card-text", "摘要說明段落。"),
            ("ui-chip ui-chip--warm", "工作內容焦點 tag。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="task-summary-card",
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
    task_crosswalk_frame = _build_task_skill_crosswalk_frame(ctx.job_frame).head(top_task_limit)
    _render_report_table(
        "工作內容 × 技能對照表",
        "把工作內容和常一起出現的技能放在一起看，較快抓到實際準備方向。",
        task_crosswalk_frame,
        key="market-report-task-crosswalk",
        empty_text="目前沒有足夠的工作內容與技能關聯資料可供對照。",
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
    render_dev_card_annotation(
        "技能摘要卡",
        element_id="skill-summary-card",
        description="技能地圖區上方的摘要與篩選引導卡片。",
        layers=[
            "summary-card",
            "skill_category_filter",
            "skill_importance_filter",
            "skill_top_limit",
            "skill bubble chart",
        ],
        text_nodes=[
            ("info-card-title", "摘要卡主標文字。"),
            ("summary-card-text", "摘要說明段落。"),
            ("ui-chip ui-chip--warm", "技能焦點 tag。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="skill-summary-card",
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
    _render_report_table(
        "最值得補強技能表",
        "先看高分且高需求的技能，再決定下一步補強順序。",
        _build_skill_priority_frame(filtered_skill_frame),
        key="market-report-skill-priority",
        empty_text="目前篩選條件下沒有符合的技能。",
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
    _render_tasks_intro()
    if ctx.crawl_phase == "finalizing":
        st.info("正在補完整分析，工作內容統計與技能地圖完成後會顯示在這裡。")
        return

    _render_market_report_heading(
        "來源 / 職缺類型比較",
        "先從來源與職缺類型切入，快速看市場到底在要哪些工作內容與技能。",
    )
    _render_group_comparison_reports(ctx)

    _render_market_report_heading(
        "工作內容統計",
        "從職缺原文裡把最常出現的工作內容拉出來，先看任務熱點與優先順序。",
    )
    _render_tasks_section(ctx)

    st.divider()

    _render_market_report_heading(
        "技能地圖",
        "集中觀察市場最常要求的技能，補強方向可以直接對照這一區。",
    )
    _render_skills_section(ctx)


def render_skills_page(ctx: PageContext) -> None:
    """保留舊技能地圖路由的相容入口。"""
    render_tasks_page(ctx)
