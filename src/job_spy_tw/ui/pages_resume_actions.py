"""提供履歷匹配頁面的分析操作 helper。"""

from __future__ import annotations

from time import perf_counter

import streamlit as st

from ..application.resume import ResumeApplication, ResumeConfig
from ..error_taxonomy import ERROR_KIND_LLM, error_metadata
from ..observability import new_trace_id, trace_context
from ..resume_analysis import extract_resume_text
from .assistant_actions import (
    record_ai_monitoring_event,
    request_metrics_metadata,
    usage_metadata,
)
from .page_context import PageContext


def _analyze_resume_submission(
    ctx: PageContext,
    *,
    uploaded_resume,
    pasted_resume_text: str,
    use_llm: bool,
    collect_resume_profile: bool,
) -> None:
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
        return

    resume_status = st.status("正在分析履歷並比對職缺...", expanded=True)
    source_kind = "upload" if uploaded_resume is not None else "manual"
    end_to_end_started_at = perf_counter()
    trace_id = new_trace_id("resume")
    try:
        resume_status.write("1. 擷取履歷文字與整理輸入內容")
        service = ResumeApplication.from_config(
            ResumeConfig(
                role_targets=ctx.snapshot.role_targets,
                openai_api_key=ctx.settings.openai_api_key,
                openai_base_url=ctx.settings.openai_base_url,
                llm_model=ctx.settings.resume_llm_model,
                title_model=ctx.settings.title_similarity_model,
                embedding_model=ctx.settings.embedding_model,
                cache_dir=ctx.settings.cache_dir,
            )
        )
        resume_status.write("2. 擷取履歷重點與技能")
        build_profile_started_at = perf_counter()
        try:
            with trace_context(trace_id):
                profile = service.build_profile(
                    text=resume_text,
                    source_name=source_name,
                    use_llm=use_llm,
                )
        except Exception as exc:
            record_ai_monitoring_event(
                ctx=ctx,
                event_type="resume.build_profile",
                status="error",
                latency_ms=round((perf_counter() - build_profile_started_at) * 1000, 3),
                model_name=ctx.settings.resume_llm_model if use_llm else "rule_based",
                metadata={
                    "trace_id": trace_id,
                    "text_chars": len(resume_text),
                    "source_kind": source_kind,
                    "use_llm_requested": use_llm,
                    **error_metadata(
                        exc,
                        default_kind=ERROR_KIND_LLM if use_llm else None,
                        metadata={"operation": "resume.build_profile"},
                    ),
                },
            )
            raise
        profile.notes = list(dict.fromkeys(notes + profile.notes))
        build_profile_metrics = getattr(service, "last_build_profile_metrics", None)
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="resume.build_profile",
            status="success",
            latency_ms=round((perf_counter() - build_profile_started_at) * 1000, 3),
            model_name=ctx.settings.resume_llm_model if use_llm else "rule_based",
            metadata={
                "trace_id": trace_id,
                "text_chars": len(resume_text),
                "source_kind": source_kind,
                "use_llm_requested": use_llm,
                "extraction_method": profile.extraction_method,
                "target_roles_count": len(profile.target_roles),
                "core_skills_count": len(profile.core_skills),
                "notes_count": len(profile.notes),
                **request_metrics_metadata(build_profile_metrics),
                **usage_metadata(getattr(service, "last_build_profile_usage", None)),
            },
        )
        resume_status.write("3. 比對職缺與計算匹配分數")
        match_jobs_started_at = perf_counter()
        try:
            with trace_context(trace_id):
                matches = service.match_jobs(profile=profile, jobs=ctx.snapshot.jobs)
        except Exception as exc:
            record_ai_monitoring_event(
                ctx=ctx,
                event_type="resume.match_jobs",
                status="error",
                latency_ms=round((perf_counter() - match_jobs_started_at) * 1000, 3),
                model_name=ctx.settings.title_similarity_model,
                metadata={
                    "trace_id": trace_id,
                    "jobs_considered": len(ctx.snapshot.jobs),
                    "use_llm_requested": use_llm,
                    **error_metadata(
                        exc,
                        default_kind=ERROR_KIND_LLM if use_llm else None,
                        metadata={"operation": "resume.match_jobs"},
                    ),
                },
            )
            raise
        top_match = matches[0] if matches else None
        match_jobs_metrics = getattr(service, "last_match_jobs_metrics", None)
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="resume.match_jobs",
            status="success",
            latency_ms=round((perf_counter() - match_jobs_started_at) * 1000, 3),
            model_name=ctx.settings.title_similarity_model,
            metadata={
                "trace_id": trace_id,
                "jobs_considered": len(ctx.snapshot.jobs),
                "matches_count": len(matches),
                "use_llm_requested": use_llm,
                "top_score": round(float(top_match.overall_score), 3) if top_match else 0.0,
                "top_scoring_method": top_match.scoring_method if top_match else "",
                **request_metrics_metadata(match_jobs_metrics),
                **usage_metadata(getattr(service, "last_match_jobs_usage", None)),
            },
        )
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
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="resume.analyze_resume",
            status="success",
            latency_ms=round((perf_counter() - end_to_end_started_at) * 1000, 3),
            model_name=ctx.settings.resume_llm_model if use_llm else "rule_based",
            metadata={
                "trace_id": trace_id,
                "text_chars": len(resume_text),
                "source_kind": source_kind,
                "use_llm_requested": use_llm,
                "matches_count": len(matches),
                "snapshot_jobs": len(ctx.snapshot.jobs),
                **request_metrics_metadata(build_profile_metrics),
                **request_metrics_metadata(match_jobs_metrics),
                **usage_metadata(
                    {
                        key: int(getattr(service, "last_build_profile_usage", {}).get(key, 0) or 0)
                        + int(getattr(service, "last_match_jobs_usage", {}).get(key, 0) or 0)
                        for key in (
                            "requests",
                            "input_tokens",
                            "output_tokens",
                            "total_tokens",
                            "cached_input_tokens",
                        )
                    }
                ),
            },
        )
        resume_status.update(label="履歷分析完成", state="complete", expanded=False)
    except Exception as exc:
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="resume.analyze_resume",
            status="error",
            latency_ms=round((perf_counter() - end_to_end_started_at) * 1000, 3),
            model_name=ctx.settings.resume_llm_model if use_llm else "rule_based",
            metadata={
                "trace_id": trace_id,
                "text_chars": len(resume_text),
                "source_kind": source_kind,
                "use_llm_requested": use_llm,
                "snapshot_jobs": len(ctx.snapshot.jobs),
                **error_metadata(
                    exc,
                    default_kind=ERROR_KIND_LLM if use_llm else None,
                    metadata={"operation": "resume.analyze_resume"},
                ),
            },
        )
        resume_status.update(label="履歷分析失敗", state="error", expanded=True)
        raise
