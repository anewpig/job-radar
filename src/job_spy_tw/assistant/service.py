"""Assistant helpers for service."""
#把「市場資料 + 履歷資料 + 使用者問題」串起來，先檢索，再丟給 LLM 生成答案，最後包裝成結構化回傳結果。
from __future__ import annotations

import json
import re
import time
import sqlite3
from pathlib import Path
from typing import Any, Literal

from ..models import AssistantCitation, AssistantResponse, MarketSnapshot, ResumeProfile #結構化回傳
from ..openai_usage import extract_openai_usage, merge_openai_usage
from ..resume_analysis import mask_personal_text #個資遮罩
from ..salary_prediction import (
    SALARY_ESTIMATE_DISPLAY_CONFIDENCE,
    SALARY_EVIDENCE_LIMIT,
    SalaryEstimator,
    find_specific_salary_job,
    format_salary_estimate_label,
    load_salary_estimator,
)
from ..utils import ensure_directory, normalize_text #如果資料夾不存在就建立，存在就直接回傳，用在 cache directory 初始化
from .chunks import build_chunks #chunking
from .external_search import (
    DuckDuckGoHTMLSearchClient,
    ExternalSearchClient,
    build_external_search_chunks,
)
from .models import KnowledgeChunk
from ..prompt_versions import (
    CHUNKING_POLICY_VERSION,
    PERSISTENT_INDEX_VERSION,
    RETRIEVAL_POLICY_VERSION,
    answer_prompt_version,
    normalize_prompt_variant,
)
from .prompts import build_answer_prompt
from .retrieval import (
    EmbeddingRetriever,
    _classify_question_intents,
    _collect_signals,
    _question_prefers_aggregate_salary,
    _question_prefers_specific_job,
    stable_hash,
) #把問題和知識片段都轉成 embedding，然後用 cosine similarity 找最相關 chunks
from .vector_index import PersistentANNIndex, RUNTIME_SOURCE_REF

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+#./_-]{2,}|[\u4e00-\u9fff]{2,}")
STOP_TERMS = {
    "目前", "這批", "哪些", "什麼", "可以", "需要", "以及", "目前市場", "目前職缺", "目前這批",
    "重點", "常見", "整理", "答案", "相關", "問題", "內容", "技能", "工作", "職缺", "市場",
    "目前快照", "已根據", "已引用", "下一步", "限制", "結論",
}
COMPARISON_SECTION_LABELS = {
    "技能": "技能差異",
    "技能需求": "技能差異",
    "工作內容": "工作內容",
    "內容": "工作內容",
    "薪資": "薪資揭露",
    "待遇": "薪資揭露",
    "適合對象": "適合對象",
    "適合人選": "適合對象",
    "風險": "風險",
    "限制": "風險",
}
GUIDANCE_SECTION_LABELS = {
    "市場需求": "市場需求",
    "市場重點": "市場需求",
    "目前缺口": "目前缺口",
    "缺口": "目前缺口",
    "優先補強": "優先補強",
    "先補": "優先補強",
    "投遞建議": "投遞建議",
    "建議方向": "投遞建議",
    "風險": "提醒",
    "限制": "提醒",
}
MARKET_SECTION_LABELS = {
    "市場分布": "市場分布",
    "分布": "市場分布",
    "核心技能": "核心技能",
    "技能重點": "核心技能",
    "薪資樣態": "薪資樣態",
    "薪資": "薪資樣態",
    "工作內容": "工作內容",
    "內容重點": "工作內容",
    "趨勢提醒": "趨勢提醒",
    "提醒": "趨勢提醒",
    "限制": "趨勢提醒",
}
AGGREGATE_HINTS = (
    "目前",
    "常見",
    "重點",
    "主要",
    "最多",
    "集中",
    "分布",
    "優先",
    "值得",
)
COMPARISON_SOURCE_TYPES = {
    "job-summary",
    "job-salary",
    "job-skills",
    "job-work-content",
}
COMPARISON_RETRIEVAL_PRIORITY = {
    "job-summary": 4,
    "job-skills": 3,
    "job-work-content": 2,
    "job-salary": 1,
}
IMPORTANCE_RANK = {
    "高": 3.0,
    "中高": 2.5,
    "中": 2.0,
    "低": 1.0,
}

#安全載入 OpenAI 客戶端，如果沒有安裝套件或沒有提供 API key 就會在初始化時拋出錯誤
try: 
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None


AnswerMode = Literal["market_summary", "personalized_guidance", "job_comparison", "general_chat"]
CAREER_TOPIC_HINTS = (
    "求職",
    "職缺",
    "履歷",
    "面試",
    "面試率",
    "投遞",
    "轉職",
    "薪資",
    "月薪",
    "年薪",
    "offer",
    "錄取",
    "職涯",
    "職位",
    "職務",
    "職稱",
    "工作內容",
    "工作機會",
    "雇主",
    "徵才",
    "104",
    "1111",
    "linkedin",
    "cake",
    "jd",
    "job description",
    "市場",
)
ROLE_TOPIC_HINTS = (
    "工程師",
    "產品經理",
    "pm",
    "經理",
    "分析師",
    "科學家",
    "設計師",
    "顧問",
    "專員",
    "developer",
    "manager",
)
ROLE_QUESTION_HINTS = (
    "差異",
    "比較",
    "適合",
    "技能",
    "能力",
    "薪資",
    "面試",
    "要求",
    "工作內容",
    "做什麼",
    "怎麼選",
    "哪個",
    "職涯",
)
FOLLOW_UP_HINTS = (
    "能力",
    "哪些",
    "還需要",
    "下一步",
    "怎麼補",
    "怎麼做",
    "怎麼準備",
    "要補",
)
CONTEXT_DEPENDENT_HINTS = (
    "那",
    "那如果",
    "那這個",
    "那另一個",
    "那還",
    "那薪資",
    "那地點",
    "那工作內容",
    "那履歷",
    "另外",
    "再來",
    "再問",
    "換成",
    "改成",
    "這個",
    "這樣",
    "前者",
    "後者",
)
TEMPORAL_RETRIEVAL_HINTS = (
    "目前",
    "最近",
    "現在",
    "近期",
    "近況",
    "最新",
    "當前",
    "趨勢",
    "這幾天",
    "這陣子",
    "今年",
    "本月",
    "本週",
    "這批",
)
DIRECT_CHAT_SKIP_HINTS = (
    "加油",
    "笑話",
    "晚安",
    "早安",
    "午安",
    "翻譯",
    "寫一句",
    "寫一段",
    "寫文案",
    "取名",
    "情書",
    "詩",
    "祝福",
    "閒聊",
)
RESUME_ONLY_HINTS = (
    "履歷",
    "簡歷",
    "履歷表",
    "自傳",
    "履歷內容",
    "履歷格式",
    "履歷撰寫",
    "履歷修改",
    "履歷優化",
    "履歷建議",
    "文字潤飾",
    "錯字",
)
MARKET_RETRIEVAL_HINTS = (
    "市場",
    "職缺",
    "工作內容",
    "薪資",
    "技能需求",
    "技能缺口",
    "趨勢",
    "分布",
    "熱門",
    "公司",
    "職稱",
    "角色",
    "投遞",
    "面試",
    "104",
    "1111",
    "linkedin",
    "cake",
)
DEFAULT_ANSWER_TEMPERATURE = 0.2
GENERAL_CHAT_TEMPERATURE = 0.55
PERSISTENT_INDEX_SYNC_INTERVAL_SECONDS = 900
PERSISTENT_INDEX_CANDIDATE_FLOOR = 32
CHUNK_CACHE_MAX_ENTRIES = 6


def normalize_latency_profile(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"fast", "balanced"}:
        return normalized
    return "fast"


def _select_prompt_variant(*, base_variant: str, latency_profile: str) -> str:
    if normalize_latency_profile(latency_profile) == "fast":
        return "compact_qa"
    return normalize_prompt_variant(base_variant)


#面向求職市場分析的 RAG 助理
class JobMarketRAGAssistant:
    def __init__( #初始化整個助理
        self,
        api_key: str,
        answer_model: str,
        embedding_model: str,
        base_url: str = "",
        cache_dir: Path | None = None,
        general_chat_model: str = "",
        prompt_variant: str = "control",
        latency_profile: str = "fast",
        client: Any | None = None,
        persistent_index_sync_interval_seconds: int = PERSISTENT_INDEX_SYNC_INTERVAL_SECONDS,
        persistent_index_enabled: bool = True,
        persistent_index_sources: tuple[str, ...] = ("snapshot_file",),
        persistent_index_max_snapshots: int = 1,
        persistent_index_max_history_rows: int = 500,
        external_search_enabled: bool = False,
        external_search_provider: str = "duckduckgo",
        external_search_max_results: int = 3,
        external_search_timeout_seconds: float = 4.0,
        external_search_cache_ttl_seconds: int = 900,
        external_search_client: ExternalSearchClient | None = None,
        salary_prediction_enabled: bool = True,
        salary_prediction_model_path: Path | None = None,
        salary_estimator: SalaryEstimator | None = None,
    ) -> None:
        if OpenAI is None and client is None: #檢查 OpenAI 套件或 client 是否存在
            raise RuntimeError("OpenAI 套件不可用，無法啟用 RAG 助理。")
        if client is None and not api_key: #檢查 API key
            raise RuntimeError("沒有提供 OPENAI_API_KEY。")

        #如果有提供 client 就用提供的，沒有就用 OpenAI 並帶入 API key 和 base URL
        if client is not None:
            self.client = client
        else:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)

        #保存模型設定和 cache directory，並初始化檢索器
        self.answer_model = answer_model
        self.general_chat_model = general_chat_model.strip() or answer_model
        self.prompt_variant = normalize_prompt_variant(prompt_variant)
        self.latency_profile = normalize_latency_profile(latency_profile)
        self.embedding_model = embedding_model
        self.persistent_index_sync_interval_seconds = max(
            60,
            int(persistent_index_sync_interval_seconds),
        )
        self.persistent_index_enabled = bool(persistent_index_enabled)
        self.persistent_index_sources = tuple(
            source.strip().lower()
            for source in persistent_index_sources
            if str(source).strip()
        )
        self.persistent_index_max_snapshots = max(
            0,
            int(persistent_index_max_snapshots),
        )
        self.persistent_index_max_history_rows = max(
            0,
            int(persistent_index_max_history_rows),
        )
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.embedding_cache_dir = (
            ensure_directory(self.cache_dir / "rag_embeddings")
            if self.cache_dir
            else None
        )
        self.external_search_enabled = bool(external_search_enabled)
        self.external_search_provider = (
            str(external_search_provider or "duckduckgo").strip().lower() or "duckduckgo"
        )
        self.external_search_max_results = max(0, int(external_search_max_results))
        self.external_search_timeout_seconds = max(
            1.0,
            float(external_search_timeout_seconds),
        )
        self.external_search_cache_ttl_seconds = max(
            0,
            int(external_search_cache_ttl_seconds),
        )
        self.external_search_client = external_search_client
        if (
            self.external_search_enabled
            and self.external_search_client is None
            and self.external_search_provider == "duckduckgo"
            and self.cache_dir is not None
            and self.external_search_max_results > 0
        ):
            self.external_search_client = DuckDuckGoHTMLSearchClient(
                cache_dir=self.cache_dir / "external_search",
                timeout_seconds=self.external_search_timeout_seconds,
                max_results=self.external_search_max_results,
                cache_ttl_seconds=self.external_search_cache_ttl_seconds,
            )
        self.persistent_index = (
            PersistentANNIndex(
                db_path=self.cache_dir.parent / "assistant_vector_index.sqlite3",
                embedding_model=self.embedding_model,
            )
            if self.cache_dir and self.persistent_index_enabled
            else None
        )
        self._last_persistent_index_sync_at = 0.0
        #初始化檢索器，帶入 client、embedding model 和 cache directory
        self.retriever = EmbeddingRetriever(
            client=self.client,
            embedding_model=self.embedding_model,
            cache_dir=self.embedding_cache_dir,
        )
        self.last_usage = merge_openai_usage()
        self.last_request_metrics: dict[str, Any] = {}
        self._chunk_cache: dict[str, list[KnowledgeChunk]] = {}
        self._last_runtime_snapshot_hash = ""
        self._last_chunk_cache_hit = False
        self._last_merge_stats: dict[str, Any] = {}
        self._last_external_search_stats: dict[str, Any] = {}
        self.salary_prediction_enabled = bool(salary_prediction_enabled)
        self.salary_prediction_model_path = Path(salary_prediction_model_path).expanduser() if salary_prediction_model_path else None
        self.salary_estimator = (
            salary_estimator
            if salary_estimator is not None
            else load_salary_estimator(
                self.salary_prediction_model_path,
                enabled=self.salary_prediction_enabled,
            )
        )

    #回答問題的主流程   
    def answer_question(
        self,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None = None,
        conversation_context: list[AssistantResponse] | None = None,
        top_k: int = 8,
        latency_profile: str | None = None,
    ) -> AssistantResponse:
        self.last_usage = merge_openai_usage()
        effective_latency_profile = normalize_latency_profile(
            latency_profile or self.latency_profile
        )
        answer_mode = self.classify_answer_mode(
            question=question,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
        )
        question_signals = _collect_signals(question)
        question_intents = _classify_question_intents(question, question_signals)
        use_market_retrieval = _should_use_market_retrieval(
            question=question,
            answer_mode=answer_mode,
            conversation_context=conversation_context,
        )
        top_k = _select_top_k(
            answer_mode=answer_mode,
            question=question,
            requested_top_k=top_k,
            latency_profile=effective_latency_profile,
        )
        self._last_merge_stats = {}
        self._last_external_search_stats = {}
        chunks = self._build_chunks(snapshot=snapshot, resume_profile=resume_profile) if use_market_retrieval else []
        retrieval_query = (
            _build_retrieval_query(
                question=question,
                conversation_context=conversation_context,
                answer_mode=answer_mode,
            )
            if use_market_retrieval
            else question[:420]
        )
        chunks = (
            self._merge_retrieval_chunks(
                base_chunks=chunks,
                snapshot=snapshot,
                retrieval_query=retrieval_query,
                top_k=top_k,
            )
            if use_market_retrieval
            else chunks
        )
        external_chunks = []
        if use_market_retrieval:
            external_chunks = self._build_external_search_chunks(
                question=question,
                answer_mode=answer_mode,
            )
            if external_chunks:
                chunks = [*external_chunks, *chunks]
        retrieved = self._retrieve(question=retrieval_query, chunks=chunks, top_k=top_k) if use_market_retrieval else []
        if answer_mode == "job_comparison":
            retrieved = _ensure_comparison_coverage(
                question=question,
                all_chunks=chunks,
                retrieved=retrieved,
                top_k=top_k,
            )
        prompt = self._build_answer_prompt( #建立回答 prompt
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
            answer_mode=answer_mode,
            chunks=retrieved,
            latency_profile=effective_latency_profile,
        )
        selected_prompt_variant = _select_prompt_variant(
            base_variant=self.prompt_variant,
            latency_profile=effective_latency_profile,
        )
        selected_model = self._select_answer_model(answer_mode=answer_mode)
        max_output_tokens = _select_answer_max_output_tokens(
            answer_mode=answer_mode,
            latency_profile=effective_latency_profile,
        )
        response = self.client.responses.create( #呼叫 LLM 生成回答
            model=selected_model,
            temperature=_select_answer_temperature(answer_mode=answer_mode),
            max_output_tokens=max_output_tokens,
            input=prompt,
        )
        self.last_usage = merge_openai_usage(
            self.retriever.last_usage,
            extract_openai_usage(response),
        )
        self.last_request_metrics = {
            "answer_mode": answer_mode,
            "selected_model": selected_model,
            "latency_profile": effective_latency_profile,
            "used_market_retrieval": bool(use_market_retrieval),
            "chunk_cache_hit": bool(self._last_chunk_cache_hit),
            "top_k": int(top_k),
            "max_output_tokens": max_output_tokens,
            "prompt_version": answer_prompt_version(selected_prompt_variant),
            "prompt_variant": selected_prompt_variant,
            "retrieval_policy_version": RETRIEVAL_POLICY_VERSION,
            "chunking_policy_version": CHUNKING_POLICY_VERSION,
            "persistent_index_version": PERSISTENT_INDEX_VERSION,
            "question_intents": sorted(question_intents),
            **self._last_merge_stats,
            **self._last_external_search_stats,
            **getattr(self.retriever, "last_stats", {}),
        }
        answer_text = getattr(response, "output_text", "").strip() #取出回答文字
        structured_answer = _parse_structured_answer(answer_text)
        citation_chunks = _select_citation_chunks(
            question=question,
            retrieved=retrieved,
            all_chunks=chunks,
        )
        citations = [ #建立 citations
            AssistantCitation(
                label=chunk.label,
                url=chunk.url,
                snippet=_build_citation_snippet(
                    question=question,
                    chunk=chunk,
                    answer_summary=structured_answer["summary"],
                    answer_key_points=structured_answer["key_points"],
                ),
                source_type=chunk.source_type,
            )
            for chunk in citation_chunks
        ]
        (
            structured_answer,
            citations,
            salary_prediction_metadata,
        ) = self._augment_salary_answer(
            question=question,
            snapshot=snapshot,
            question_intents=question_intents,
            structured_answer=structured_answer,
            citations=citations,
        )
        self.last_request_metrics.update(salary_prediction_metadata)
        market_sections = (
            _build_market_sections(
                key_points=structured_answer["key_points"],
                limitations=structured_answer["limitations"],
            )
            if answer_mode == "market_summary"
            else []
        )
        guidance_sections = (
            _build_guidance_sections(
                key_points=structured_answer["key_points"],
                limitations=structured_answer["limitations"],
            )
            if answer_mode == "personalized_guidance"
            else []
        )
        comparison_sections = (
            _build_comparison_sections(
                key_points=structured_answer["key_points"],
                limitations=structured_answer["limitations"],
            )
            if answer_mode == "job_comparison"
            else []
        )
        if answer_mode == "general_chat":
            notes = [
                "回答模式：general_chat",
                f"已檢索 {len(retrieved)} 個知識片段",
            ]
            external_count = int(
                self._last_external_search_stats.get("external_search_result_count") or 0
            )
            if external_count > 0:
                notes.append(
                    f"外部查詢：{self.external_search_provider} {external_count} 筆"
                )
            elif self.external_search_enabled:
                notes.append("外部查詢：未取得可用結果")
            if salary_prediction_metadata.get("salary_prediction_used"):
                notes.append("具體職缺薪資：已加入 AI 區間預估與相似職缺證據")
            notes.extend(
                [
                    f"資料快照時間：{snapshot.generated_at}",
                    "general_chat 目前會一律補充市場檢索內容，回答會參考當前快照脈絡。",
                ]
            )
        else:
            notes = [ #建立 retrieval notes
                f"回答模式：{answer_mode}",
                f"已檢索 {len(retrieved)} 個知識片段",
                f"資料快照時間：{snapshot.generated_at}",
            ]
            if salary_prediction_metadata.get("salary_prediction_used"):
                notes.append("具體職缺薪資：已加入 AI 區間預估與相似職缺證據")
        return AssistantResponse( #回傳 AssistantResponse
            question=question,
            answer=structured_answer["answer"],
            summary=structured_answer["summary"],
            key_points=structured_answer["key_points"],
            limitations=structured_answer["limitations"],
            next_step=structured_answer["next_step"],
            answer_mode=answer_mode,
            market_sections=market_sections,
            guidance_sections=guidance_sections,
            comparison_sections=comparison_sections,
            citations=citations,
            retrieval_notes=notes,
            used_chunks=len(retrieved),
            model=selected_model,
            retrieval_model=self.embedding_model,
        )

    def classify_answer_mode(
        self,
        *,
        question: str,
        resume_profile: ResumeProfile | None = None,
        conversation_context: list[AssistantResponse] | None = None,
    ) -> AnswerMode:
        return _classify_answer_mode(
            question=question,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
        )

    def generate_report( #快速生成求職報告
        self,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None = None,
    ) -> AssistantResponse:
        report_question = ( #固定報告問題
            "請產出一份簡短求職報告，至少涵蓋："
            "1. 可以優先學習的技能 "
            "2. 還需補足的技能 "
            "3. 工作薪資區間 "
            "4. 常見工作內容 "
            "5. 履歷與市場的匹配建議"
        )
        return self.answer_question( #呼叫 answer_question
            question=report_question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            top_k=8,
            latency_profile="balanced",
        )

    def _augment_salary_answer(
        self,
        *,
        question: str,
        snapshot: MarketSnapshot,
        question_intents: set[str],
        structured_answer: dict[str, Any],
        citations: list[AssistantCitation],
    ) -> tuple[dict[str, Any], list[AssistantCitation], dict[str, Any]]:
        metadata: dict[str, Any] = {
            "salary_prediction_used": False,
            "salary_prediction_confidence": 0.0,
            "salary_prediction_model_version": getattr(
                self.salary_estimator,
                "model_version",
                "",
            ),
            "salary_prediction_fallback_reason": "",
            "salary_prediction_evidence_count": 0,
        }
        if "salary" not in question_intents:
            metadata["salary_prediction_fallback_reason"] = "not_salary_question"
            return structured_answer, citations, metadata
        if _is_aggregate_salary_question(question):
            metadata["salary_prediction_fallback_reason"] = "aggregate_salary_question"
            return structured_answer, citations, metadata

        target_job = find_specific_salary_job(question, snapshot.jobs)
        if target_job is None:
            metadata["salary_prediction_fallback_reason"] = "target_job_not_found"
            return structured_answer, citations, metadata
        if target_job.salary.strip():
            metadata["salary_prediction_fallback_reason"] = "has_actual_salary"
            return structured_answer, citations, metadata

        estimate = self.salary_estimator.estimate_job(target_job)
        metadata.update(
            {
                "salary_prediction_confidence": float(estimate.confidence or 0.0),
                "salary_prediction_model_version": estimate.model_version
                or metadata["salary_prediction_model_version"],
                "salary_prediction_fallback_reason": estimate.fallback_reason,
                "salary_prediction_evidence_count": len(estimate.evidence_job_urls),
            }
        )
        if estimate.fallback_reason or float(estimate.confidence or 0.0) < SALARY_ESTIMATE_DISPLAY_CONFIDENCE:
            return structured_answer, citations, metadata

        salary_label = format_salary_estimate_label(estimate)
        estimate_sentence = (
            f"若以目前相似職缺推估，這份「{target_job.title}」職缺的 {salary_label}。"
            " 這是根據相似揭露薪資職缺與文字特徵推估的區間，不能取代雇主實際公告。"
        )
        answer_body = str(structured_answer.get("answer") or "").strip()
        structured_answer["answer"] = (
            f"{estimate_sentence}\n\n{answer_body}"
            if answer_body
            else estimate_sentence
        )
        structured_answer["key_points"] = [
            f"{salary_label}（依 {len(estimate.evidence_job_urls)} 筆相似職缺推估）",
            *list(structured_answer.get("key_points") or []),
        ]
        limitations = list(structured_answer.get("limitations") or [])
        salary_limitation = "AI 預估薪資只適用於未揭露薪資的具體職缺，實際 offer 仍以雇主面談結果為準。"
        if salary_limitation not in limitations:
            limitations.append(salary_limitation)
        structured_answer["limitations"] = limitations

        evidence_citations = self._build_salary_estimate_citations(estimate)
        merged_citations = _merge_assistant_citations(citations, evidence_citations, limit=5)
        metadata["salary_prediction_used"] = True
        metadata["salary_prediction_fallback_reason"] = ""
        return structured_answer, merged_citations, metadata

    def _build_salary_estimate_citations(
        self,
        estimate,
    ) -> list[AssistantCitation]:
        evidence_rows = self.salary_estimator.evidence_rows(estimate.evidence_job_urls)
        citations: list[AssistantCitation] = []
        for row in evidence_rows[:SALARY_EVIDENCE_LIMIT]:
            salary_text = str(row.get("salary") or "").strip()
            if not salary_text:
                low_value = int(row.get("monthly_salary_low") or 0)
                high_value = int(row.get("monthly_salary_high") or 0)
                if low_value > 0 and high_value > 0:
                    if low_value == high_value:
                        salary_text = f"月薪 {low_value:,}"
                    else:
                        salary_text = f"月薪 {low_value:,}-{high_value:,}"
            citations.append(
                AssistantCitation(
                    label=f"{row.get('title') or '相似職缺'} @ {row.get('company') or '未知公司'}",
                    url=str(row.get("url") or ""),
                    snippet=(
                        f"相似職缺揭露薪資：{salary_text or '未提供'}；"
                        f"來源：{row.get('source') or '未知'}；"
                        f"地點：{row.get('location') or '未提供'}"
                    ),
                    source_type="salary-estimate-evidence",
                )
            )
        return citations

    #包裝轉呼叫
    def _build_chunks(
        self,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None,
    ):
        cache_key = _build_chunk_cache_key(
            snapshot=snapshot,
            resume_profile=resume_profile,
        )
        cached = self._chunk_cache.get(cache_key)
        if cached is not None:
            self._last_chunk_cache_hit = True
            return cached
        self._last_chunk_cache_hit = False
        chunks = build_chunks(snapshot=snapshot, resume_profile=resume_profile)
        self._chunk_cache[cache_key] = chunks
        while len(self._chunk_cache) > CHUNK_CACHE_MAX_ENTRIES:
            oldest_key = next(iter(self._chunk_cache))
            self._chunk_cache.pop(oldest_key, None)
        return chunks

    def _retrieve(
        self,
        question: str,
        chunks,
        top_k: int,
    ):
        return self.retriever.retrieve(question=question, chunks=chunks, top_k=top_k)

    def _build_external_search_chunks(
        self,
        *,
        question: str,
        answer_mode: AnswerMode,
    ) -> list[KnowledgeChunk]:
        if (
            answer_mode != "general_chat"
            or not self.external_search_enabled
            or self.external_search_client is None
            or self.external_search_max_results <= 0
        ):
            self._last_external_search_stats = {
                "external_search_enabled": bool(self.external_search_enabled),
                "external_search_provider": self.external_search_provider,
                "external_search_result_count": 0,
            }
            return []
        try:
            results = self.external_search_client.search(query=question)
        except Exception as exc:  # noqa: BLE001
            self._last_external_search_stats = {
                "external_search_enabled": True,
                "external_search_provider": self.external_search_provider,
                "external_search_result_count": 0,
                "external_search_error": type(exc).__name__,
            }
            return []
        chunks = build_external_search_chunks(
            query=question,
            results=results,
        )
        self._last_external_search_stats = {
            "external_search_enabled": True,
            "external_search_provider": self.external_search_provider,
            "external_search_result_count": len(chunks),
        }
        return chunks

    def _merge_retrieval_chunks(
        self,
        *,
        base_chunks,
        snapshot: MarketSnapshot,
        retrieval_query: str,
        top_k: int,
    ):
        embed_texts = getattr(self.retriever, "_embed_texts", None)
        if self.persistent_index is None or embed_texts is None:
            return base_chunks

        try:
            runtime_snapshot_hash = _build_runtime_snapshot_hash(snapshot)
            runtime_sync_performed = False
            if runtime_snapshot_hash != self._last_runtime_snapshot_hash:
                self.persistent_index.sync_runtime_snapshot(
                    snapshot=snapshot,
                    embed_texts=embed_texts,
                )
                self._last_runtime_snapshot_hash = runtime_snapshot_hash
                runtime_sync_performed = True
            persistent_sync_performed = self._sync_persistent_sources_if_due(embed_texts=embed_texts)
            ann_candidates = self.persistent_index.search(
                question=retrieval_query,
                embed_texts=embed_texts,
                top_k=max(PERSISTENT_INDEX_CANDIDATE_FLOOR, top_k * 5),
                exclude_source_refs={RUNTIME_SOURCE_REF},
            )
        except sqlite3.OperationalError as exc:
            if "database is locked" in str(exc).lower():
                return base_chunks
            raise
        if not ann_candidates:
            self._last_merge_stats = {
                "persistent_index_enabled": True,
                "persistent_index_runtime_sync": runtime_sync_performed,
                "persistent_index_source_sync": persistent_sync_performed,
                "persistent_ann_candidates": 0,
                "merged_chunk_count": len(base_chunks),
            }
            return base_chunks

        deduped = list(base_chunks)
        seen = {
            (chunk.source_type, chunk.label, chunk.text, chunk.url)
            for chunk in deduped
        }
        for chunk in ann_candidates:
            key = (chunk.source_type, chunk.label, chunk.text, chunk.url)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(chunk)
        self._last_merge_stats = {
            "persistent_index_enabled": True,
            "persistent_index_runtime_sync": runtime_sync_performed,
            "persistent_index_source_sync": persistent_sync_performed,
            "persistent_ann_candidates": len(ann_candidates),
            "merged_chunk_count": len(deduped),
        }
        return deduped

    def _sync_persistent_sources_if_due(self, *, embed_texts) -> bool:
        if (
            self.persistent_index is None
            or self.cache_dir is None
            or not self.persistent_index_enabled
        ):
            return False
        now = time.monotonic()
        if now - self._last_persistent_index_sync_at < self.persistent_index_sync_interval_seconds:
            return False

        data_dir = self.cache_dir.parent
        sources = set(self.persistent_index_sources)
        if "snapshot_file" in sources:
            self.persistent_index.sync_snapshot_file(
                snapshot_path=data_dir / "jobs_latest.json",
                embed_texts=embed_texts,
            )
        if "snapshot_store" in sources:
            self.persistent_index.sync_snapshot_store(
                snapshot_store_dir=data_dir / "snapshots",
                embed_texts=embed_texts,
                max_snapshots=self.persistent_index_max_snapshots,
            )
        if "market_history" in sources:
            self.persistent_index.sync_market_history(
                history_db_path=data_dir / "market_history.sqlite3",
                embed_texts=embed_texts,
                max_rows=self.persistent_index_max_history_rows,
            )
        self._last_persistent_index_sync_at = now
        return True

    def _build_answer_prompt(
        self,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None,
        conversation_context: list[AssistantResponse] | None,
        answer_mode: AnswerMode,
        chunks,
        latency_profile: str | None = None,
    ) -> str:
        effective_latency_profile = normalize_latency_profile(
            latency_profile or self.latency_profile
        )
        return build_answer_prompt(
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
            answer_mode=answer_mode,
            chunks=chunks,
            prompt_variant=_select_prompt_variant(
                base_variant=self.prompt_variant,
                latency_profile=effective_latency_profile,
            ),
        )

    def _select_answer_model(self, *, answer_mode: AnswerMode) -> str:
        if answer_mode == "general_chat" and self.general_chat_model.strip():
            return self.general_chat_model
        return self.answer_model


def _build_retrieval_query(
    *,
    question: str,
    conversation_context: list[AssistantResponse] | None,
    answer_mode: AnswerMode,
    max_turns: int = 2,
) -> str:
    mode_hint = {
        "market_summary": "回答模式 市場摘要",
        "personalized_guidance": "回答模式 個人化建議",
        "job_comparison": "回答模式 職缺比較",
        "general_chat": "回答模式 一般對話",
    }[answer_mode]
    base_query = f"{question}\n{mode_hint}"
    if not conversation_context:
        return base_query[:420]

    history_segments: list[str] = []
    for turn in conversation_context[:max_turns]:
        question_text = normalize_text(turn.question)
        if not question_text:
            continue
        answer_terms: list[str] = []
        if turn.summary.strip():
            answer_terms.append(normalize_text(turn.summary))
        if turn.key_points:
            answer_terms.extend(
                normalize_text(point)
                for point in turn.key_points[:1]
                if normalize_text(point)
            )
        if not answer_terms and turn.answer.strip():
            answer_terms.append(normalize_text(turn.answer)[:90])
        merged_terms = " / ".join(part for part in answer_terms if part)
        segment = f"上一輪問題 {question_text}"
        if merged_terms:
            segment += f"；上一輪回答 {merged_terms}"
        history_segments.append(segment)

    if not history_segments:
        return base_query[:420]
    retrieval_query = f"{base_query}\n最近上下文：{' | '.join(history_segments)}"
    return retrieval_query[:420]


def _select_top_k(
    *,
    answer_mode: AnswerMode,
    question: str,
    requested_top_k: int,
    latency_profile: str = "fast",
) -> int:
    effective_profile = normalize_latency_profile(latency_profile)
    min_top_k = 2 if effective_profile == "fast" else 4
    if requested_top_k != 8:
        return max(min_top_k, requested_top_k)

    question_signals = _collect_signals(question)
    intents = _classify_question_intents(question, question_signals)
    if _question_prefers_specific_job(question):
        if intents & {"work_content", "skill_gap", "salary"}:
            return 5

    routed_top_k = (
        {
            "market_summary": 4,
            "personalized_guidance": 4,
            "job_comparison": 6,
            "general_chat": 2,
        }
        if effective_profile == "fast"
        else {
            "market_summary": 6,
            "personalized_guidance": 4,
            "job_comparison": 10,
            "general_chat": 4,
        }
    )[answer_mode]
    return max(min_top_k, routed_top_k)


def _select_answer_temperature(*, answer_mode: AnswerMode) -> float:
    return GENERAL_CHAT_TEMPERATURE if answer_mode == "general_chat" else DEFAULT_ANSWER_TEMPERATURE


def _select_answer_max_output_tokens(
    *,
    answer_mode: AnswerMode,
    latency_profile: str = "fast",
) -> int:
    effective_profile = normalize_latency_profile(latency_profile)
    if effective_profile == "fast":
        return {
            "market_summary": 300,
            "personalized_guidance": 320,
            "job_comparison": 380,
            "general_chat": 220,
        }[answer_mode]
    return {
        "market_summary": 420,
        "personalized_guidance": 440,
        "job_comparison": 520,
        "general_chat": 320,
    }[answer_mode]


def _build_runtime_snapshot_hash(snapshot: MarketSnapshot) -> str:
    return stable_hash(
        {
            "generated_at": snapshot.generated_at,
            "queries": snapshot.queries,
            "job_urls": [job.url for job in snapshot.jobs],
            "job_posted_at": [job.posted_at for job in snapshot.jobs],
            "skills_count": len(snapshot.skills),
            "task_insights_count": len(snapshot.task_insights),
        }
    )


def _build_chunk_cache_key(
    *,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> str:
    return stable_hash(
        {
            "snapshot": _build_runtime_snapshot_hash(snapshot),
            "resume_roles": resume_profile.target_roles if resume_profile else [],
            "resume_core_skills": resume_profile.core_skills if resume_profile else [],
            "resume_tool_skills": resume_profile.tool_skills if resume_profile else [],
            "resume_summary": normalize_text(resume_profile.summary)[:240] if resume_profile else "",
        }
    )


def _should_use_market_retrieval(
    *,
    question: str,
    answer_mode: AnswerMode,
    conversation_context: list[AssistantResponse] | None,
) -> bool:
    normalized = normalize_text(question).lower()
    if answer_mode == "general_chat":
        return True
    if answer_mode == "personalized_guidance":
        if any(hint in normalized for hint in RESUME_ONLY_HINTS) and not any(
            hint in normalized for hint in MARKET_RETRIEVAL_HINTS
        ):
            return False
        return True
    return True


def _looks_job_related_question(
    *,
    normalized_question: str,
    resume_profile: ResumeProfile | None,
    personalized_hints: tuple[str, ...],
) -> bool:
    if any(hint in normalized_question for hint in CAREER_TOPIC_HINTS):
        return True
    if resume_profile is not None and any(hint in normalized_question for hint in personalized_hints):
        return True
    has_role_hint = any(hint in normalized_question for hint in ROLE_TOPIC_HINTS)
    has_role_question_hint = any(hint in normalized_question for hint in ROLE_QUESTION_HINTS)
    return has_role_hint and has_role_question_hint


def _looks_job_related_conversation(
    conversation_context: list[AssistantResponse] | None,
) -> bool:
    if not conversation_context:
        return False

    recent_segments: list[str] = []
    for turn in conversation_context[:3]:
        recent_segments.extend(
            [
                normalize_text(turn.question),
                normalize_text(turn.summary),
                *(normalize_text(point) for point in turn.key_points[:2]),
            ]
        )
    merged = " ".join(segment for segment in recent_segments if segment).lower()
    if not merged:
        return False
    if any(hint in merged for hint in CAREER_TOPIC_HINTS):
        return True
    return any(hint in merged for hint in ROLE_TOPIC_HINTS)


def _question_depends_on_job_context(normalized_question: str) -> bool:
    if not normalized_question:
        return False

    follow_up_signal = any(hint in normalized_question for hint in CONTEXT_DEPENDENT_HINTS)
    if not follow_up_signal:
        return False

    question_signals = (
        any(hint in normalized_question for hint in CAREER_TOPIC_HINTS)
        or any(hint in normalized_question for hint in ROLE_TOPIC_HINTS)
        or any(hint in normalized_question for hint in ROLE_QUESTION_HINTS)
        or any(hint in normalized_question for hint in FOLLOW_UP_HINTS)
        or any(hint in normalized_question for hint in TEMPORAL_RETRIEVAL_HINTS)
    )
    if question_signals:
        return True

    stripped = normalized_question.strip("？?。！!，,；;：: ")
    return len(stripped) <= 10 and stripped.endswith("呢")


def _classify_answer_mode(
    *,
    question: str,
    resume_profile: ResumeProfile | None,
    conversation_context: list[AssistantResponse] | None = None,
) -> AnswerMode:
    normalized = normalize_text(question).lower()
    comparison_hints = (
        "比較",
        "差異",
        "哪個比較",
        "哪個更適合",
        "差別",
        "相比",
        "versus",
        "vs",
    )
    personalized_hints = (
        "我",
        "我的",
        "適合我",
        "適合投",
        "履歷",
        "面試率",
        "轉職",
        "補足",
        "先補",
        "優先學習",
        "下一步",
    )

    conversation_job_related = _looks_job_related_conversation(conversation_context)
    question_depends_on_job_context = _question_depends_on_job_context(normalized)
    job_related = _looks_job_related_question(
        normalized_question=normalized,
        resume_profile=resume_profile,
        personalized_hints=personalized_hints,
    ) or (conversation_job_related and question_depends_on_job_context)

    if any(hint in normalized for hint in comparison_hints) and job_related:
        return "job_comparison"
    if (
        resume_profile is not None
        and conversation_job_related
        and any(hint in normalized for hint in FOLLOW_UP_HINTS)
    ):
        return "personalized_guidance"
    if resume_profile is not None and any(hint in normalized for hint in personalized_hints):
        return "personalized_guidance"
    if job_related:
        return "market_summary"
    return "general_chat"


def _strip_json_fence(raw_text: str) -> str:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


def _render_structured_answer(
    *,
    summary: str,
    key_points: list[str],
    limitations: list[str],
    next_step: str,
) -> str:
    sections: list[str] = []
    if summary:
        sections.append(summary)
    if key_points:
        rendered_points = "；".join(point.strip().rstrip("。；") for point in key_points if point.strip())
        if rendered_points:
            sections.append(f"另外，{rendered_points}。")
    if limitations:
        rendered_limits = "；".join(item.strip().rstrip("。；") for item in limitations if item.strip())
        if rendered_limits:
            sections.append(f"需要留意的是，{rendered_limits}。")
    if next_step:
        next_step_text = next_step.strip()
        if next_step_text:
            if next_step_text.startswith(("建議", "可以", "先", "若")):
                sections.append(next_step_text if next_step_text.endswith(("。", "！", "？")) else f"{next_step_text}。")
            else:
                sections.append(f"如果要往下做，可以從 {next_step_text.rstrip('。')} 開始。")
    return "\n\n".join(sections).strip() or "目前沒有足夠資訊可回答這個問題。"


def _parse_structured_answer(raw_text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(raw_text)
    try:
        payload = json.loads(cleaned) if cleaned else {}
    except json.JSONDecodeError:
        payload = {}

    if isinstance(payload, dict) and payload:
        answer = str(payload.get("answer", "")).strip()
        summary = str(payload.get("summary", "")).strip()
        key_points = _normalize_string_list(payload.get("key_points"))
        limitations = _normalize_string_list(payload.get("limitations"))
        next_step = str(payload.get("next_step", "")).strip()
        if not answer:
            answer = _render_structured_answer(
                summary=summary,
                key_points=key_points,
                limitations=limitations,
                next_step=next_step,
            )
        return {
            "summary": summary,
            "key_points": key_points,
            "limitations": limitations,
            "next_step": next_step,
            "answer": answer,
        }

    plain_text = cleaned or "目前沒有足夠資訊可回答這個問題。"
    lines = [line.strip() for line in plain_text.splitlines() if line.strip()]
    summary = lines[0] if lines else plain_text
    key_points = [
        line.lstrip("-• ").strip()
        for line in lines[1:]
        if line.startswith(("-", "•"))
    ]
    return {
        "summary": summary,
        "key_points": key_points,
        "limitations": [],
        "next_step": "",
        "answer": plain_text,
    }


def _candidate_terms(question: str, answer_summary: str, answer_key_points: list[str]) -> list[str]:
    pooled = "\n".join(filter(None, [question, answer_summary, *answer_key_points]))
    ordered: list[str] = []
    seen: set[str] = set()
    for token in TOKEN_PATTERN.findall(normalize_text(pooled)):
        term = token.strip()
        lowered = term.lower()
        if not term or lowered in seen or term in STOP_TERMS:
            continue
        seen.add(lowered)
        ordered.append(term)
    return ordered


def _split_labeled_point(point: str) -> tuple[str, str]:
    text = str(point).strip()
    for separator in ("：", ":"):
        if separator in text:
            label, value = text.split(separator, 1)
            return label.strip(), value.strip()
    return "", text


def _normalize_comparison_label(label: str) -> str:
    normalized = normalize_text(label)
    return COMPARISON_SECTION_LABELS.get(normalized, "主要差異")


def _normalize_guidance_label(label: str) -> str:
    normalized = normalize_text(label)
    return GUIDANCE_SECTION_LABELS.get(normalized, "建議重點")


def _normalize_market_label(label: str) -> str:
    normalized = normalize_text(label)
    return MARKET_SECTION_LABELS.get(normalized, "市場重點")


def _build_labeled_sections(
    *,
    key_points: list[str],
    limitations: list[str],
    label_normalizer,
    limitation_label: str,
) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for point in key_points:
        label, value = _split_labeled_point(point)
        rendered_value = value or str(point).strip()
        if not rendered_value:
            continue
        sections.append(
            {
                "label": label_normalizer(label),
                "value": rendered_value,
            }
        )
    for item in limitations:
        rendered_value = str(item).strip()
        if not rendered_value:
            continue
        sections.append(
            {
                "label": limitation_label,
                "value": rendered_value,
            }
        )
    return sections


def _build_market_sections(
    *,
    key_points: list[str],
    limitations: list[str],
) -> list[dict[str, str]]:
    return _build_labeled_sections(
        key_points=key_points,
        limitations=limitations,
        label_normalizer=_normalize_market_label,
        limitation_label="趨勢提醒",
    )


def _build_guidance_sections(
    *,
    key_points: list[str],
    limitations: list[str],
) -> list[dict[str, str]]:
    return _build_labeled_sections(
        key_points=key_points,
        limitations=limitations,
        label_normalizer=_normalize_guidance_label,
        limitation_label="提醒",
    )


def _build_comparison_sections(
    *,
    key_points: list[str],
    limitations: list[str],
) -> list[dict[str, str]]:
    return _build_labeled_sections(
        key_points=key_points,
        limitations=limitations,
        label_normalizer=_normalize_comparison_label,
        limitation_label="風險",
    )


def _window_around_term(text: str, term: str, radius: int = 88) -> str:
    index = text.lower().find(term.lower())
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(term) + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def _build_citation_snippet(
    *,
    question: str,
    chunk: KnowledgeChunk,
    answer_summary: str,
    answer_key_points: list[str],
    max_chars: int = 220,
) -> str:
    masked_text = mask_personal_text(normalize_text(chunk.text))
    if chunk.source_type.startswith("market-"):
        lines = [line.strip() for line in masked_text.splitlines() if line.strip()]
        if lines:
            return " / ".join(lines[:2])[:max_chars]

    terms = _candidate_terms(question, answer_summary, answer_key_points)
    for term in terms:
        snippet = _window_around_term(masked_text, term)
        if snippet:
            return snippet[:max_chars]

    lines = [line.strip() for line in masked_text.splitlines() if line.strip()]
    if lines:
        return lines[0][:max_chars]
    return masked_text[:max_chars]


def _question_prefers_aggregate(question: str) -> bool:
    normalized = normalize_text(question)
    return any(token in normalized for token in AGGREGATE_HINTS)


def _is_comparison_question(question: str) -> bool:
    return _classify_answer_mode(question=question, resume_profile=None) == "job_comparison"


def _chunk_target_candidates(chunk: KnowledgeChunk) -> list[str]:
    metadata = chunk.metadata_items()
    values = [
        str(metadata.get("matched_role", "")).strip(),
        str(metadata.get("title", "")).strip(),
        chunk.label.strip(),
    ]
    candidates: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_text(value)
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        candidates.append(normalized)
    return candidates


def _chunk_matches_target(chunk: KnowledgeChunk, target: str) -> bool:
    normalized_target = normalize_text(target).lower()
    if not normalized_target:
        return False
    for candidate in _chunk_target_candidates(chunk):
        lowered = candidate.lower()
        if normalized_target in lowered or lowered in normalized_target:
            return True
    return False


def _extract_comparison_targets(question: str, retrieved: list[KnowledgeChunk]) -> list[str]:
    normalized_question = normalize_text(question).lower()
    matches: list[str] = []
    seen: set[str] = set()
    candidate_pool: list[str] = []
    for chunk in retrieved:
        candidate_pool.extend(_chunk_target_candidates(chunk))
    candidate_pool.sort(key=len, reverse=True)
    for candidate in candidate_pool:
        lowered = candidate.lower()
        if not lowered or lowered in seen:
            continue
        if lowered in normalized_question:
            seen.add(lowered)
            matches.append(candidate)
    return matches[:4]


def _chunk_occurrence_score(chunk: KnowledgeChunk) -> float:
    metadata = chunk.metadata_items()
    raw_score = metadata.get("score", 0)
    raw_occurrences = metadata.get("occurrences", 0)
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        score = 0.0
    try:
        occurrences = float(raw_occurrences)
    except (TypeError, ValueError):
        occurrences = 0.0
    importance = IMPORTANCE_RANK.get(str(metadata.get("importance", "")).strip(), 0.0)
    return score * 0.02 + occurrences * 0.05 + importance * 0.2


def _select_market_priority_chunks(
    *,
    question: str,
    intents: set[str],
    all_chunks: list[KnowledgeChunk],
    max_chunks: int,
) -> list[KnowledgeChunk]:
    selected: list[KnowledgeChunk] = []
    if not all_chunks or max_chunks <= 0:
        return selected

    if _question_prefers_aggregate(question) and "skill_gap" in intents:
        candidates = [chunk for chunk in all_chunks if chunk.source_type == "market-skill-insight"]
        return candidates[:max_chunks]

    if _question_prefers_aggregate(question) and "work_content" in intents:
        candidates = [chunk for chunk in all_chunks if chunk.source_type == "market-task-insight"]
        return candidates[:max_chunks]

    return selected


def _comparison_chunk_priority(chunk: KnowledgeChunk) -> tuple[float, float, int]:
    metadata = chunk.metadata_items()
    priority = float(COMPARISON_RETRIEVAL_PRIORITY.get(chunk.source_type, 0))
    try:
        relevance = float(metadata.get("relevance_score", 0) or 0)
    except (TypeError, ValueError):
        relevance = 0.0
    return (priority, relevance, len(chunk.text))


def _ensure_comparison_coverage(
    *,
    question: str,
    all_chunks: list[KnowledgeChunk],
    retrieved: list[KnowledgeChunk],
    top_k: int,
) -> list[KnowledgeChunk]:
    comparison_targets = _extract_comparison_targets(question, all_chunks)
    if not comparison_targets:
        return retrieved[:top_k]

    selected: list[KnowledgeChunk] = []
    seen_ids: set[str] = set()

    for target in comparison_targets:
        candidates = [
            chunk
            for chunk in all_chunks
            if chunk.chunk_id not in seen_ids
            and chunk.source_type in COMPARISON_SOURCE_TYPES
            and _chunk_matches_target(chunk, target)
        ]
        candidates.sort(key=_comparison_chunk_priority, reverse=True)
        if not candidates:
            continue
        chosen = candidates[0]
        selected.append(chosen)
        seen_ids.add(chosen.chunk_id)

    for chunk in retrieved:
        if chunk.chunk_id in seen_ids:
            continue
        selected.append(chunk)
        seen_ids.add(chunk.chunk_id)
        if len(selected) >= top_k:
            return selected[:top_k]

    for target in comparison_targets:
        candidates = [
            chunk
            for chunk in all_chunks
            if chunk.chunk_id not in seen_ids
            and chunk.source_type in COMPARISON_SOURCE_TYPES
            and _chunk_matches_target(chunk, target)
        ]
        candidates.sort(key=_comparison_chunk_priority, reverse=True)
        for chunk in candidates:
            if chunk.chunk_id in seen_ids:
                continue
            selected.append(chunk)
            seen_ids.add(chunk.chunk_id)
            if len(selected) >= top_k:
                return selected[:top_k]

    return selected[:top_k]


def _citation_chunk_bonus(*, question: str, intents: set[str], chunk: KnowledgeChunk) -> float:
    source_type = chunk.source_type
    aggregate = _question_prefers_aggregate(question)
    comparison = _is_comparison_question(question)
    comparison_targets = _extract_comparison_targets(question, [chunk]) if comparison else []

    if comparison:
        if source_type == "job-summary":
            bonus = 1.7
        elif source_type in {"job-skills", "job-work-content", "job-salary"}:
            bonus = 1.1
        else:
            bonus = 0.0
        if comparison_targets:
            bonus += 0.9
        return bonus

    if "source_distribution" in intents and source_type == "market-source-summary":
        return 2.0
    if "role_distribution" in intents and source_type == "market-role-summary":
        return 2.0
    if "location_distribution" in intents and source_type == "market-location-summary":
        return 2.0
    if "salary" in intents:
        if source_type == "job-salary":
            return 1.6
        if source_type == "job-summary":
            return 0.35
    if "skill_gap" in intents:
        if aggregate and source_type == "market-skill-insight":
            return 1.8 + _chunk_occurrence_score(chunk)
        if source_type == "job-skills":
            return 0.45
    if "work_content" in intents:
        if aggregate and source_type == "market-task-insight":
            return 1.8 + _chunk_occurrence_score(chunk)
        if source_type == "job-work-content":
            return 0.45
    if "resume_gap" in intents:
        if source_type == "resume-summary":
            return 1.1
        if source_type == "job-skills":
            return 0.55
    if "market" in intents:
        if source_type == "market-skill-insight":
            return 1.2 + _chunk_occurrence_score(chunk)
        if source_type == "market-task-insight":
            return 1.0 + _chunk_occurrence_score(chunk)
    return 0.0


def _select_citation_chunks(
    *,
    question: str,
    retrieved: list[KnowledgeChunk],
    all_chunks: list[KnowledgeChunk] | None = None,
    max_citations: int = 5,
) -> list[KnowledgeChunk]:
    if not retrieved:
        return []

    comparison = _is_comparison_question(question)
    comparison_targets = _extract_comparison_targets(question, retrieved) if comparison else []
    question_signals = _collect_signals(question)
    intents = _classify_question_intents(question, question_signals)
    scored: list[tuple[float, int, KnowledgeChunk]] = []
    for index, chunk in enumerate(retrieved):
        # 保留 retrieval 原始排序作為 base，再用 citation bonus 重排最適合展示的證據。
        base_rank = max(0.0, 1.0 - index * 0.08)
        bonus = _citation_chunk_bonus(question=question, intents=intents, chunk=chunk)
        scored.append((base_rank + bonus, index, chunk))

    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    ordered = [chunk for _, _, chunk in scored]

    deduped: list[KnowledgeChunk] = []
    seen_ids: set[str] = set()

    for chunk in _select_market_priority_chunks(
        question=question,
        intents=intents,
        all_chunks=all_chunks or retrieved,
        max_chunks=max_citations,
    ):
        if chunk.chunk_id in seen_ids:
            continue
        seen_ids.add(chunk.chunk_id)
        deduped.append(chunk)
        if len(deduped) >= max_citations:
            return deduped[:max_citations]

    if comparison and comparison_targets:
        for target in comparison_targets:
            for chunk in ordered:
                if chunk.chunk_id in seen_ids:
                    continue
                if chunk.source_type not in COMPARISON_SOURCE_TYPES:
                    continue
                if not _chunk_matches_target(chunk, target):
                    continue
                seen_ids.add(chunk.chunk_id)
                deduped.append(chunk)
                break

    for chunk in ordered:
        if chunk.chunk_id in seen_ids:
            continue
        seen_ids.add(chunk.chunk_id)
        deduped.append(chunk)
        if len(deduped) >= max_citations:
            break
    return deduped


def _merge_assistant_citations(
    citations: list[AssistantCitation],
    extra_citations: list[AssistantCitation],
    *,
    limit: int,
) -> list[AssistantCitation]:
    merged: list[AssistantCitation] = []
    seen_keys: set[tuple[str, str]] = set()
    for citation in [*citations, *extra_citations]:
        key = (
            str(citation.url or "").strip(),
            str(citation.label or "").strip(),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(citation)
        if len(merged) >= limit:
            break
    return merged


def _is_aggregate_salary_question(question: str) -> bool:
    normalized = normalize_text(question)
    if _question_prefers_specific_job(question):
        return False
    strong_tokens = ("市場", "整體", "這批", "分布", "平均", "行情")
    if any(token in normalized for token in strong_tokens):
        return True
    return _question_prefers_aggregate_salary(question) and "大概" not in normalized
