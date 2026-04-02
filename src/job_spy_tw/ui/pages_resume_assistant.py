from __future__ import annotations

import streamlit as st

from ..models import ResumeJobMatch, ResumeProfile
from ..resume_analysis import (
    ResumeAnalysisService,
    extract_resume_text,
    mask_personal_items,
    mask_personal_text,
    summarize_match_gaps,
)
from .common import _escape, _format_ranked_terms, build_chip_row, render_section_header
from .frames import resume_matches_to_frame
from .page_context import PageContext
from .renderers import (
    render_assistant_response,
    render_assistant_suggestion_buttons,
    render_resume_profile,
)
from .resources import get_rag_assistant
from .search import (
    build_context_request_response,
    build_manual_assistant_profile,
    format_openai_error,
    needs_personal_context,
)
from .session import assistant_question_batches, set_main_tab

SUGGESTED_ASSISTANT_QUESTIONS = [
    "可以優先學習的技能有哪些？",
    "我還需補足哪些技能？",
    "目前工作薪資區間大概是多少？",
    "這些職缺常見的工作內容是什麼？",
    "這次搜尋最常出現的職缺方向有哪些？",
    "目前哪些技能最常被放在必備條件？",
    "哪些職缺最適合轉職者先嘗試？",
    "如果我是新鮮人，建議先補哪些能力？",
    "哪幾種工作內容最值得我先熟悉？",
    "不同平台的職缺差異在哪裡？",
    "目前最值得優先投遞的職缺有哪些？",
    "我的履歷目前最接近哪些類型的工作？",
    "如果想提高面試率，應該先補什麼？",
    "哪些技能需求正在反覆出現？",
    "這些職缺通常會希望我做哪些事情？",
    "目前市場對這類職缺最重視什麼條件？",
]


def render_resume_page(ctx: PageContext) -> None:
    render_section_header(
        "履歷匹配",
        "上傳履歷後，系統會整理重點技能、偏好工作內容，並用雙分數幫你看哪些職缺更適合投遞。",
        "Resume Match",
    )
    if ctx.current_user_is_guest:
        st.caption("目前是訪客模式。分析結果會留在這次使用期間；登入後可把履歷摘要保存到自己的帳號。")
    else:
        st.caption("目前登入中。重新分析後，新的履歷摘要會自動覆蓋並保存到你的帳號。")
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

    if analyze_resume:
        resume_chunks: list[str] = []
        notes: list[str] = []
        source_name = "手動貼上的履歷文字"
        uploaded_file_name = ""

        if uploaded_resume is not None:
            uploaded_file_name = uploaded_resume.name
            extracted_text, file_notes = extract_resume_text(
                uploaded_resume.name,
                uploaded_resume.getvalue(),
            )
            if extracted_text:
                resume_chunks.append(extracted_text)
                source_name = uploaded_resume.name
            notes.extend(file_notes)

        if pasted_resume_text.strip():
            resume_chunks.append(pasted_resume_text.strip())

        resume_text = "\n\n".join(chunk for chunk in resume_chunks if chunk.strip())
        if not resume_text:
            if uploaded_file_name:
                st.error(f"已收到檔案：{uploaded_file_name}，但目前沒有成功擷取出可分析文字。")
                for note in notes or ["這份檔案目前沒有抽出文字內容，請改貼文字或確認 PDF 內有可選取文字層。"]:
                    st.warning(note)
            else:
                st.warning("請先上傳履歷檔或貼上履歷文字。")
        else:
            resume_status = st.status("正在分析履歷並比對職缺...", expanded=True)
            try:
                resume_status.write("1. 擷取履歷文字與整理輸入內容")
                service = ResumeAnalysisService(
                    role_targets=ctx.snapshot.role_targets,
                    openai_api_key=ctx.settings.openai_api_key,
                    openai_base_url=ctx.settings.openai_base_url,
                    llm_model=ctx.settings.resume_llm_model,
                    title_model=ctx.settings.title_similarity_model,
                    embedding_model=ctx.settings.embedding_model,
                    cache_dir=ctx.settings.cache_dir,
                )
                resume_status.write("2. 擷取履歷重點與技能")
                profile = service.build_profile(
                    text=resume_text,
                    source_name=source_name,
                    use_llm=use_llm,
                )
                profile.notes = list(dict.fromkeys(notes + profile.notes))
                resume_status.write("3. 比對職缺與計算匹配分數")
                matches = service.match_jobs(profile, ctx.snapshot.jobs)
                st.session_state.resume_profile = profile
                st.session_state.resume_matches = matches
                st.session_state.resume_notes = notes
                resume_status.write("4. 保存本次分析結果")
                if not ctx.current_user_is_guest:
                    ctx.product_store.save_resume_profile(
                        user_id=ctx.current_user_id,
                        profile=profile,
                    )
                if collect_resume_profile:
                    ctx.user_data_store.save_profile(
                        profile=profile,
                        source_type="resume_upload",
                    )
                    st.success("已將匿名化履歷分析資料保存到資料庫。")
                resume_status.update(label="履歷分析完成", state="complete", expanded=False)
            except Exception:
                resume_status.update(label="履歷分析失敗", state="error", expanded=True)
                raise

    resume_profile: ResumeProfile | None = st.session_state.resume_profile
    resume_matches: list[ResumeJobMatch] = st.session_state.resume_matches

    if resume_profile is None:
        st.info("上傳履歷後，這裡會顯示自動擷取的技能、匹配 prompt 與最相近的職缺。")
        return

    render_resume_profile(resume_profile)
    match_frame = resume_matches_to_frame(resume_matches)
    gap_summary = summarize_match_gaps(resume_matches)
    if match_frame.empty:
        st.info("目前沒有可比對的職缺資料。")
        return

    top_match_row = match_frame.sort_values("overall_score", ascending=False).iloc[0]
    strong_match_count = int((match_frame["overall_score"] >= 75).sum())
    watch_match_count = int((match_frame["overall_score"] >= 60).sum())
    average_market_fit = float(match_frame["market_fit_score"].mean())
    resume_summary_text = (
        f"目前最適合先投遞的是 {top_match_row['title']}，"
        f"來自 {top_match_row['company']}；如果想優先補強，可以先看下方缺口分析。"
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
    filtered_matches = filtered_matches.sort_values(
        ["overall_score", "market_fit_score"],
        ascending=False,
    )

    st.markdown("**優先投遞建議**")
    st.caption(
        "個人匹配度 = 職稱相近度 15 + 技能語意 30 + 工作內容語意 25 + "
        "精確命中 20 + 關鍵字 / 領域 10。職缺相似度則是不含精確命中的市場相似度。"
    )
    if filtered_matches.empty:
        st.info("目前篩選條件下沒有符合的履歷匹配職缺。")
    else:
        for row in filtered_matches.head(10).to_dict(orient="records"):
            meta_labels = [
                row["source"],
                row["matched_role"] or "未標記角色",
                f"個人匹配度 {row['overall_score']:.1f}",
                f"職缺相似度 {row['market_fit_score']:.1f}",
            ]
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


def render_assistant_page(ctx: PageContext) -> None:
    render_section_header(
        "AI 助理",
        "直接詢問市場技能缺口、工作內容與薪資資訊，也能依照履歷或基本資料產生個人化回答。",
        "Assistant",
    )
    if not ctx.settings.openai_api_key:
        st.markdown(
            """
<div class="summary-card">
  <div class="info-card-title">AI 助理尚未啟用</div>
  <div class="summary-card-text">設定好 OpenAI API key 後，這裡就能根據目前的職缺快照回答技能缺口、工作內容、薪資區間，也能幫你產生簡短求職報告。</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.info("請先設定 `OPENAI_API_KEY`，才能使用 OpenAI + RAG 客服與簡報。")
        return

    assistant = get_rag_assistant(
        api_key=ctx.settings.openai_api_key,
        answer_model=ctx.settings.assistant_model,
        embedding_model=ctx.settings.embedding_model,
        base_url=ctx.settings.openai_base_url,
        cache_dir=str(ctx.settings.cache_dir),
    )
    resume_context_profile: ResumeProfile | None = st.session_state.resume_profile
    manual_context_profile: ResumeProfile | None = st.session_state.assistant_profile
    assistant_profile: ResumeProfile | None = (
        resume_context_profile or manual_context_profile
    )
    assistant_chips = []
    if assistant_profile is not None:
        assistant_chips.extend(mask_personal_items(assistant_profile.target_roles[:3]))
        assistant_chips.extend(mask_personal_items(assistant_profile.core_skills[:3]))
    else:
        assistant_chips.append("目前以市場資料為主")
    st.markdown(
        f"<div class='chip-row' style='margin:0.2rem 0 0.85rem;'>{build_chip_row(assistant_chips, tone='soft', limit=6)}</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        left_col, right_col = st.columns([1.02, 1.25], gap="large")
        with left_col:
            st.markdown("**個人化背景**")
            if resume_context_profile is not None:
                st.caption("目前已載入履歷，AI 助理會優先依照履歷內容回答。")
                st.markdown(
                    mask_personal_text(resume_context_profile.summary or "已載入履歷摘要。")
                )
            else:
                if manual_context_profile is not None:
                    st.caption("目前已載入求職基本資料。你也可以重新填寫或清除。")
                    st.markdown(
                        mask_personal_text(
                            manual_context_profile.summary or "已載入求職基本資料。"
                        )
                    )
                    clear_profile_cols = st.columns([1.3, 1], gap="medium")
                    if clear_profile_cols[1].button(
                        "清除基本資料",
                        key="assistant-clear-profile",
                        use_container_width=True,
                    ):
                        st.session_state.assistant_profile = None
                        set_main_tab("assistant")
                        st.session_state.favorite_feedback = "已清除 AI 助理的求職基本資料。"
                        st.rerun()
                with st.expander(
                    "填寫或更新求職基本資料",
                    expanded=manual_context_profile is None,
                ):
                    with st.form("assistant_profile_form"):
                        target_roles_text = st.text_area(
                            "目標職缺",
                            placeholder="例如：AI應用工程師、AI工程師",
                            height=100,
                        )
                        experience_level = st.selectbox(
                            "年資",
                            ["", "新鮮人 / 轉職中", "1-3 年", "3-5 年", "5 年以上"],
                        )
                        locations_text = st.text_area(
                            "希望工作地點",
                            placeholder="例如：台北市、新竹市、遠端",
                            height=80,
                        )
                        skills_text = st.text_area(
                            "目前技能",
                            placeholder="例如：Python、LLM、RAG、Docker",
                            height=100,
                        )
                        collect_assistant_profile = st.checkbox(
                            "同意保存求職基本資料到資料庫",
                            value=False,
                            help="只會保存你填寫的基本資料與系統整理後的摘要。",
                        )
                        save_profile = st.form_submit_button(
                            "儲存基本資料",
                            use_container_width=True,
                        )

                    if save_profile:
                        updated_profile = build_manual_assistant_profile(
                            target_roles_text=target_roles_text,
                            experience_level=experience_level,
                            locations_text=locations_text,
                            skills_text=skills_text,
                        )
                        st.session_state.assistant_profile = updated_profile
                        if collect_assistant_profile:
                            ctx.user_data_store.save_profile(
                                profile=updated_profile,
                                source_type="assistant_profile",
                            )
                        set_main_tab("assistant")
                        st.session_state.favorite_feedback = (
                            "已儲存基本資料，AI 助理之後會用這份資料做個人化回答。"
                        )
                        st.rerun()

        with right_col:
            question_batches = assistant_question_batches(
                SUGGESTED_ASSISTANT_QUESTIONS,
                batch_size=4,
            )
            batch_count = max(1, len(question_batches))
            current_batch_index = int(st.session_state.assistant_suggestion_page) % batch_count
            suggestion_header_cols = st.columns([1.6, 1], gap="medium")
            suggestion_header_cols[0].markdown("**快速提問**")
            suggestion_header_cols[0].caption("每次提供 4 題常見問題，也可以換一批看看。")
            if suggestion_header_cols[1].button(
                "換一批問題",
                key="assistant-next-question-batch",
                use_container_width=True,
            ):
                current_batch_index = (current_batch_index + 1) % batch_count
                st.session_state.assistant_suggestion_page = current_batch_index
                set_main_tab("assistant")
            selected_question = render_assistant_suggestion_buttons(
                question_batches[current_batch_index]
            )
            if selected_question:
                st.session_state.assistant_question_draft = selected_question
                st.session_state.assistant_question_input = selected_question

            with st.form("assistant_form"):
                assistant_question = st.text_area(
                    "詢問客服",
                    key="assistant_question_input",
                    height=120,
                    placeholder="例如：可以優先學習的技能有哪些？",
                )
                col_left, col_right = st.columns(2)
                ask_assistant = col_left.form_submit_button(
                    "送出問題",
                    use_container_width=True,
                )
                generate_report_in_form = col_right.form_submit_button(
                    "產生求職報告",
                    use_container_width=True,
                )

            if ask_assistant:
                question = assistant_question.strip()
                if not question:
                    st.warning("請先輸入問題。")
                else:
                    st.session_state.assistant_question_draft = question
                    if assistant_profile is None and needs_personal_context(question):
                        history = st.session_state.assistant_history
                        history.insert(0, build_context_request_response(question))
                        st.session_state.assistant_history = history[:6]
                    else:
                        try:
                            answer_status = st.status("正在整理回答...", expanded=True)
                            answer_status.write("1. 檢索相關職缺、技能與市場資料")
                            answer_status.write("2. 生成回答與整理引用來源")
                            answer = assistant.answer_question(
                                question=question,
                                snapshot=ctx.snapshot,
                                resume_profile=assistant_profile,
                            )
                            history = st.session_state.assistant_history
                            history.insert(0, answer)
                            st.session_state.assistant_history = history[:6]
                            answer_status.update(
                                label="回答完成",
                                state="complete",
                                expanded=False,
                            )
                        except Exception as exc:  # noqa: BLE001
                            try:
                                answer_status.update(
                                    label="回答失敗",
                                    state="error",
                                    expanded=True,
                                )
                            except Exception:
                                pass
                            st.error(format_openai_error(exc))

            if generate_report_in_form:
                if assistant_profile is None:
                    st.session_state.assistant_report = build_context_request_response(
                        "請產生求職報告"
                    )
                else:
                    try:
                        report_status = st.status("正在產生求職報告...", expanded=True)
                        report_status.write("1. 彙整市場快照與個人背景")
                        report_status.write("2. 生成報告摘要與重點建議")
                        st.session_state.assistant_report = assistant.generate_report(
                            snapshot=ctx.snapshot,
                            resume_profile=assistant_profile,
                        )
                        report_status.update(
                            label="求職報告已產生",
                            state="complete",
                            expanded=False,
                        )
                    except Exception as exc:  # noqa: BLE001
                        try:
                            report_status.update(
                                label="求職報告產生失敗",
                                state="error",
                                expanded=True,
                            )
                        except Exception:
                            pass
                        st.error(format_openai_error(exc))

    action_cols = st.columns([1.4, 1.1, 1.1, 1.4], gap="medium")
    clear_history = action_cols[1].button(
        "清除問答紀錄",
        key="assistant-clear-history",
        use_container_width=True,
        disabled=not st.session_state.assistant_history,
    )
    clear_report = action_cols[2].button(
        "清除求職報告",
        key="assistant-clear-report",
        use_container_width=True,
        disabled=st.session_state.assistant_report is None,
    )
    if clear_history:
        st.session_state.assistant_history = []
        set_main_tab("assistant")
        st.rerun()
    if clear_report:
        st.session_state.assistant_report = None
        set_main_tab("assistant")
        st.rerun()

    if st.session_state.assistant_report is not None:
        render_assistant_response("求職報告", st.session_state.assistant_report)

    if st.session_state.assistant_history:
        st.markdown("**問答紀錄**")
        for index, answer in enumerate(st.session_state.assistant_history, start=1):
            with st.container(border=True):
                st.markdown(f"**Q{index}. {answer.question}**")
                render_assistant_response("回答", answer)
    else:
        st.info("這裡可以直接問技能、缺口、薪資區間、工作內容，或先產生一份簡短報告。")
