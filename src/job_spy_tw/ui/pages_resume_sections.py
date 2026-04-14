"""提供履歷匹配頁面的表單與結果 render helper。"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from ..models import ResumeJobMatch, ResumeProfile
from ..resume_analysis import summarize_match_gaps
from .common import _escape, _format_ranked_terms, build_chip_row
from .dev_annotations import render_dev_card_annotation
from .frames import resume_matches_to_frame
from .page_context import PageContext
from .renderers import render_resume_profile


@dataclass(slots=True)
class ResumeFormState:
    uploaded_resume: object | None
    pasted_resume_text: str
    use_llm: bool
    collect_resume_profile: bool
    analyze_resume: bool


def _render_resume_form(ctx: PageContext) -> ResumeFormState:
    render_dev_card_annotation(
        "履歷上傳表單",
        element_id="resume_match_form",
        description="上傳履歷、貼文字與送出分析的主要表單。",
        layers=[
            "uploaded_resume",
            "pasted_resume_text",
            "use_llm",
            "collect_resume_profile",
            "analyze_resume",
        ],
        text_nodes=[
            ("上傳履歷檔", "檔案上傳欄位標籤。"),
            ("或直接貼上履歷文字", "文字貼上區標籤。"),
            ("使用 LLM 擷取履歷重點", "分析方式 checkbox。"),
            ("同意保存匿名化履歷分析資料到資料庫", "資料保存 checkbox。"),
        ],
        show_popover=True,
        popover_key="resume_match_form",
    )
    with st.form("resume_match_form"):
        uploaded_resume = st.file_uploader(
            "上傳履歷檔",
            type=["txt", "md", "pdf", "docx"],
            help="支援 TXT / MD。PDF、DOCX 需要對應解析套件；如果暫時沒有，也可以直接貼文字。",
        )
        pasted_resume_text = st.text_area(
            "或直接貼上履歷文字",
            height=220,
            placeholder="把履歷內容貼在這裡，系統會自動整理技能、工作內容與匹配 prompt。",
        )
        use_llm = st.checkbox(
            "使用 LLM 擷取履歷重點",
            value=bool(ctx.settings.openai_api_key),
            help="如果已設定 OPENAI_API_KEY，系統會用 LLM 做更細的履歷摘要；否則會自動改用規則分析。",
        )
        collect_resume_profile = st.checkbox(
            "同意保存匿名化履歷分析資料到資料庫",
            value=False,
            help="只會保存匿名化後的履歷分析結果，不會預設收集。",
        )
        analyze_resume = st.form_submit_button(
            "分析履歷並比對職缺",
            type="primary",
            use_container_width=True,
        )
    return ResumeFormState(
        uploaded_resume=uploaded_resume,
        pasted_resume_text=pasted_resume_text,
        use_llm=use_llm,
        collect_resume_profile=collect_resume_profile,
        analyze_resume=analyze_resume,
    )


def _render_resume_empty_state() -> None:
    st.info("上傳履歷後，這裡會顯示自動擷取的技能、匹配 prompt 與最相近的職缺。")


def _render_resume_results(
    *,
    resume_profile: ResumeProfile,
    resume_matches: list[ResumeJobMatch],
) -> None:
    render_resume_profile(resume_profile)
    match_frame = resume_matches_to_frame(resume_matches)
    gap_summary = summarize_match_gaps(resume_matches)
    if match_frame.empty:
        st.info("目前沒有可比對的職缺資料。")
        return

    _render_resume_summary_cards(match_frame, gap_summary)
    filtered_matches = _render_resume_filters(match_frame)
    _render_resume_match_cards(filtered_matches)
    _render_resume_match_table(filtered_matches)


def _render_resume_summary_cards(match_frame, gap_summary: dict[str, list[str]]) -> None:
    top_match_row = match_frame.sort_values("overall_score", ascending=False).iloc[0]
    strong_match_count = int((match_frame["overall_score"] >= 75).sum())
    watch_match_count = int((match_frame["overall_score"] >= 60).sum())
    average_market_fit = float(match_frame["market_fit_score"].mean())
    resume_summary_text = (
        f"目前最適合先投遞的是 {top_match_row['title']}，"
        f"來自 {top_match_row['company']}；如果想優先補強，可以先看下方缺口分析。"
    )
    render_dev_card_annotation(
        "履歷匹配摘要卡",
        element_id="resume-match-summary-card",
        description="本次履歷匹配結果的總結卡。",
        layers=[
            "summary-card",
            "match metrics row",
        ],
        text_nodes=[
            ("info-card-title", "摘要卡標題。"),
            ("summary-card-text", "摘要說明文字。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="resume-match-summary-card",
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">履歷匹配摘要</div>
  <div class="summary-card-text">{_escape(resume_summary_text)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    match_metrics = st.columns(4, gap="medium")
    match_metrics[0].metric("可優先投遞", strong_match_count)
    match_metrics[1].metric("值得追蹤", watch_match_count)
    match_metrics[2].metric("平均職缺相似度", f"{average_market_fit:.1f}")
    match_metrics[3].metric("最高個人匹配度", f"{float(top_match_row['overall_score']):.1f}")
    render_dev_card_annotation(
        "履歷缺口分析卡",
        element_id="resume-gap-summary-card",
        description="列出已命中與待補強技能 / 工作內容的分析卡。",
        layers=[
            "strength_skills",
            "strength_tasks",
            "gap_skills",
            "gap_tasks",
        ],
        text_nodes=[
            ("info-card-title", "分析卡段落標題。"),
            ("summary-card-text", "分析卡導引段落。"),
            ("ui-chip ui-chip--accent", "已命中技能 tag。"),
            ("ui-chip ui-chip--soft", "已命中工作內容 tag。"),
            ("ui-chip ui-chip--warm", "待補強項目 tag。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="resume-gap-summary-card",
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">匹配原因與缺口分析</div>
  <div class="summary-card-text">先看你的強項與目前市場最常缺的能力，再決定要優先補哪些技能。</div>
  <div class="info-card-title" style="margin-top:0.95rem;">已命中技能</div>
  <div class="chip-row" style="margin-top:0.7rem;">{_format_ranked_terms(gap_summary["strength_skills"], "accent")}</div>
  <div class="info-card-title" style="margin-top:0.95rem;">已命中工作內容</div>
  <div class="chip-row" style="margin-top:0.7rem;">{_format_ranked_terms(gap_summary["strength_tasks"], "soft")}</div>
  <div class="info-card-title" style="margin-top:0.95rem;">建議優先補強技能</div>
  <div class="chip-row" style="margin-top:0.7rem;">{_format_ranked_terms(gap_summary["gap_skills"], "warm")}</div>
  <div class="info-card-title" style="margin-top:0.95rem;">建議補強工作內容</div>
  <div class="chip-row" style="margin-top:0.7rem;">{_format_ranked_terms(gap_summary["gap_tasks"], "warm")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_resume_filters(match_frame):
    filter_cols = st.columns([0.9, 1.1, 1.1], gap="medium")
    min_score = filter_cols[0].slider(
        "最低個人匹配度",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        key="resume_min_score_filter",
    )
    source_options = sorted(match_frame["source"].dropna().unique().tolist())
    selected_match_sources = filter_cols[1].multiselect(
        "來源",
        source_options,
        default=[],
        key="resume_source_filter",
    )
    role_options = sorted(match_frame["matched_role"].dropna().unique().tolist())
    selected_match_roles = filter_cols[2].multiselect(
        "匹配角色",
        role_options,
        default=[],
        key="resume_role_filter",
    )
    filtered_matches = match_frame[match_frame["overall_score"] >= min_score].copy()
    if selected_match_sources:
        filtered_matches = filtered_matches[
            filtered_matches["source"].isin(selected_match_sources)
        ]
    if selected_match_roles:
        filtered_matches = filtered_matches[
            filtered_matches["matched_role"].isin(selected_match_roles)
        ]
    return filtered_matches.sort_values(
        ["overall_score", "market_fit_score"],
        ascending=False,
    )


def _render_resume_match_cards(filtered_matches) -> None:
    st.markdown("**優先投遞建議**")
    st.caption(
        "個人匹配度 = 職稱相近度 15 + 技能語意 30 + 工作內容語意 25 + "
        "精確命中 20 + 關鍵字 / 領域 10。職缺相似度則是不含精確命中的市場相似度。"
    )
    if filtered_matches.empty:
        st.info("目前篩選條件下沒有符合的履歷匹配職缺。")
        return

    for index, row in enumerate(filtered_matches.head(10).to_dict(orient="records"), start=1):
        meta_labels = [
            row["source"],
            row["matched_role"] or "未標記角色",
            f"個人匹配度 {row['overall_score']:.1f}",
            f"職缺相似度 {row['market_fit_score']:.1f}",
        ]
        render_dev_card_annotation(
            "履歷推薦職缺卡",
            element_id=f"resume-match-card-{index}",
            description="履歷匹配頁中的單張推薦職缺卡。",
            layers=[
                "surface-card",
                "reason chips",
                "gap chips",
                "score expander",
            ],
            text_nodes=[
                ("job-card-title", "職缺標題。"),
                ("job-card-company", "公司名稱。"),
                ("ui-chip ui-chip--soft", "來源 / 分數 tag。"),
                ("ui-chip ui-chip--accent", "命中原因 tag。"),
                ("ui-chip ui-chip--warm", "補強建議 tag。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"resume-match-card-{index}",
        )
        st.markdown(
            f"""
<div class="surface-card">
  <div class="job-card-title">{_escape(row["title"])}</div>
  <div class="job-card-company">{_escape(row["company"])}</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(meta_labels, tone="soft", limit=4)}</div>
  <div class="job-card-summary">{_escape(row["fit_summary"] or "這筆職缺主要來自整體文字相似度。")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        reason_chips = []
        if row["matched_skills"]:
            reason_chips.append(f"技能命中 {row['matched_skills']}")
        if row["matched_tasks"]:
            reason_chips.append(f"工作內容命中 {row['matched_tasks']}")
        if row["matched_keywords"]:
            reason_chips.append(f"關鍵字命中 {row['matched_keywords']}")
        if reason_chips:
            st.markdown(
                f"<div class='chip-row' style='margin-top:-0.15rem;margin-bottom:0.45rem;'>{build_chip_row(reason_chips, tone='accent', limit=3)}</div>",
                unsafe_allow_html=True,
            )
        gap_chips = []
        if row["missing_skills"]:
            gap_chips.append(f"建議補強 {row['missing_skills']}")
        if row["missing_tasks"]:
            gap_chips.append(f"可再補強 {row['missing_tasks']}")
        if gap_chips:
            st.markdown(
                f"<div class='chip-row' style='margin-bottom:0.45rem;'>{build_chip_row(gap_chips, tone='warm', limit=2)}</div>",
                unsafe_allow_html=True,
            )
        with st.expander("查看分數與原因", expanded=False):
            score_cols = st.columns(5, gap="medium")
            score_cols[0].metric("個人匹配度", f"{float(row['overall_score']):.1f}")
            score_cols[1].metric("職缺相似度", f"{float(row['market_fit_score']):.1f}")
            score_cols[2].metric("技能語意", f"{float(row['skill_score']):.1f}")
            score_cols[3].metric("工作語意", f"{float(row['task_score']):.1f}")
            score_cols[4].metric("精確命中", f"{float(row['exact_match_score']):.1f}")
            if row["title_reason"]:
                st.caption(f"職稱判斷：{row['title_reason']}")
            if row["reasons"]:
                st.caption(f"推薦原因：{row['reasons']}")
            st.markdown(f"[查看職缺原文]({row['url']})")
        st.divider()


def _render_resume_match_table(filtered_matches) -> None:
    with st.expander("查看履歷匹配明細表", expanded=False):
        st.dataframe(
            filtered_matches,
            use_container_width=True,
            hide_index=True,
            column_config={
                "overall_score": st.column_config.NumberColumn("個人匹配度", format="%.2f"),
                "market_fit_score": st.column_config.NumberColumn("職缺相似度", format="%.2f"),
                "role_score": st.column_config.NumberColumn("職稱相近度分", format="%.2f"),
                "skill_score": st.column_config.NumberColumn("技能語意", format="%.2f"),
                "task_score": st.column_config.NumberColumn("工作語意", format="%.2f"),
                "exact_match_score": st.column_config.NumberColumn("精確命中", format="%.2f"),
                "keyword_score": st.column_config.NumberColumn("關鍵字 / 領域", format="%.2f"),
                "title_similarity": st.column_config.NumberColumn("職稱相近度%", format="%.2f"),
                "semantic_similarity": st.column_config.NumberColumn("語意相似度%", format="%.2f"),
                "title_reason": st.column_config.TextColumn("職稱判斷"),
                "fit_summary": st.column_config.TextColumn("匹配摘要"),
                "url": st.column_config.LinkColumn("職缺連結"),
            },
        )
