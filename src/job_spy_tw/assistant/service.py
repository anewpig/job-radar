"""Assistant helpers for service."""
#把「市場資料 + 履歷資料 + 使用者問題」串起來，先檢索，再丟給 LLM 生成答案，最後包裝成結構化回傳結果。
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..models import AssistantCitation, AssistantResponse, MarketSnapshot, ResumeProfile #結構化回傳
from ..resume_analysis import mask_personal_text #個資遮罩
from ..utils import ensure_directory, normalize_text #如果資料夾不存在就建立，存在就直接回傳，用在 cache directory 初始化
from .chunks import build_chunks #chunking
from .models import KnowledgeChunk
from .prompts import build_answer_prompt
from .retrieval import (
    EmbeddingRetriever,
    _classify_question_intents,
    _collect_signals,
) #把問題和知識片段都轉成 embedding，然後用 cosine similarity 找最相關 chunks

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+#./_-]{2,}|[\u4e00-\u9fff]{2,}")
STOP_TERMS = {
    "目前", "這批", "哪些", "什麼", "可以", "需要", "以及", "目前市場", "目前職缺", "目前這批",
    "重點", "常見", "整理", "答案", "相關", "問題", "內容", "技能", "工作", "職缺", "市場",
    "目前快照", "已根據", "已引用", "下一步", "限制", "結論",
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

#面向求職市場分析的 RAG 助理
class JobMarketRAGAssistant:
    def __init__( #初始化整個助理
        self,
        api_key: str,
        answer_model: str,
        embedding_model: str,
        base_url: str = "",
        cache_dir: Path | None = None,
        client: Any | None = None,
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
        self.embedding_model = embedding_model
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.embedding_cache_dir = (
            ensure_directory(self.cache_dir / "rag_embeddings")
            if self.cache_dir
            else None
        )
        #初始化檢索器，帶入 client、embedding model 和 cache directory
        self.retriever = EmbeddingRetriever(
            client=self.client,
            embedding_model=self.embedding_model,
            cache_dir=self.embedding_cache_dir,
        )

    #回答問題的主流程   
    def answer_question(
        self,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None = None,
        top_k: int = 8,
    ) -> AssistantResponse:
        chunks = self._build_chunks(snapshot=snapshot, resume_profile=resume_profile) #建立 chunks
        retrieved = self._retrieve(question=question, chunks=chunks, top_k=top_k) #檢索相關 chunks
        prompt = self._build_answer_prompt( #建立回答 prompt
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            chunks=retrieved,
        )
        response = self.client.responses.create( #呼叫 LLM 生成回答
            model=self.answer_model,
            temperature=0.2,
            max_output_tokens=1200,
            input=prompt,
        )
        answer_text = getattr(response, "output_text", "").strip() #取出回答文字
        structured_answer = _parse_structured_answer(answer_text)
        citation_chunks = _select_citation_chunks(question=question, retrieved=retrieved)
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
        notes = [ #建立 retrieval notes
            f"已檢索 {len(retrieved)} 個知識片段",
            f"資料快照時間：{snapshot.generated_at}",
        ]
        return AssistantResponse( #回傳 AssistantResponse
            question=question,
            answer=structured_answer["answer"],
            summary=structured_answer["summary"],
            key_points=structured_answer["key_points"],
            limitations=structured_answer["limitations"],
            next_step=structured_answer["next_step"],
            citations=citations,
            retrieval_notes=notes,
            used_chunks=len(retrieved),
            model=self.answer_model,
            retrieval_model=self.embedding_model,
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
            top_k=10,
        )

    #包裝轉呼叫
    def _build_chunks(
        self,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None,
    ):
        return build_chunks(snapshot=snapshot, resume_profile=resume_profile)

    def _retrieve(
        self,
        question: str,
        chunks,
        top_k: int,
    ):
        return self.retriever.retrieve(question=question, chunks=chunks, top_k=top_k)

    def _build_answer_prompt(
        self,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None,
        chunks,
    ) -> str:
        return build_answer_prompt(
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            chunks=chunks,
        )


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
        sections.append(f"結論\n{summary}")
    if key_points:
        sections.append("重點\n" + "\n".join(f"- {point}" for point in key_points))
    if limitations:
        sections.append("限制\n" + "\n".join(f"- {item}" for item in limitations))
    if next_step:
        sections.append(f"下一步\n{next_step}")
    return "\n\n".join(sections).strip() or "目前沒有足夠資訊可回答這個問題。"


def _parse_structured_answer(raw_text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(raw_text)
    try:
        payload = json.loads(cleaned) if cleaned else {}
    except json.JSONDecodeError:
        payload = {}

    if isinstance(payload, dict) and payload:
        summary = str(payload.get("summary", "")).strip()
        key_points = _normalize_string_list(payload.get("key_points"))
        limitations = _normalize_string_list(payload.get("limitations"))
        next_step = str(payload.get("next_step", "")).strip()
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
        "answer": _render_structured_answer(
            summary=summary,
            key_points=key_points,
            limitations=[],
            next_step="",
        ),
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


def _chunk_occurrence_score(chunk: KnowledgeChunk) -> float:
    metadata = chunk.metadata_items()
    raw_occurrences = metadata.get("occurrences", 0)
    try:
        occurrences = float(raw_occurrences)
    except (TypeError, ValueError):
        occurrences = 0.0
    importance = IMPORTANCE_RANK.get(str(metadata.get("importance", "")).strip(), 0.0)
    return occurrences * 0.05 + importance * 0.2


def _citation_chunk_bonus(*, question: str, intents: set[str], chunk: KnowledgeChunk) -> float:
    source_type = chunk.source_type
    aggregate = _question_prefers_aggregate(question)

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
    max_citations: int = 5,
) -> list[KnowledgeChunk]:
    if not retrieved:
        return []

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
    for chunk in ordered:
        if chunk.chunk_id in seen_ids:
            continue
        seen_ids.add(chunk.chunk_id)
        deduped.append(chunk)
        if len(deduped) >= max_citations:
            break
    return deduped
