"""Assistant helpers for retrieval."""
#把問題和每個知識片段都轉成 embedding，然後用 hybrid retrieval 找最相關 chunks
from __future__ import annotations

import hashlib #產生 hash 值
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from ..openai_usage import extract_openai_usage, merge_openai_usage
from ..resume_analysis import mask_personal_text
from ..utils import chunked, ensure_directory, normalize_text, unique_preserving_order
from .models import KnowledgeChunk

RETRIEVAL_SIGNAL_ALIASES: dict[str, tuple[str, ...]] = {
    "python": ("python",),
    "llm": ("llm", "大型語言模型"),
    "rag": ("rag",),
    "docker": ("docker",),
    "aws": ("aws",),
    "api": ("api", "串接"),
    "knowledge_base": ("knowledge base", "知識庫"),
    "vector_db": ("向量資料庫", "vector database", "vector db"),
    "firmware": ("韌體", "firmware", "嵌入式", "embedded"),
    "cplusplus": ("c/c++", "c++", "c語言"),
    "rtos": ("rtos",),
    "arm": ("arm",),
    "mips": ("mips",),
    "bluetooth": ("bluetooth", "藍牙"),
    "linux": ("linux", "embedded linux"),
    "pm": ("product manager", "pm", "產品經理"),
    "figma": ("figma",),
    "jira": ("jira",),
    "prd": ("prd",),
    "roadmap": ("roadmap", "路線圖"),
    "mvp": ("mvp",),
    "salary": ("薪資", "月薪", "年薪", "salary"),
    "work_content": ("工作內容", "職責", "模組"),
    "skill": ("技能", "能力", "補強"),
    "resume": ("履歷",),
    "source": ("來源", "平台", "104", "1111", "linkedin", "cake"),
    "location": ("地點", "地區", "城市", "縣市"),
    "role": ("角色", "職稱", "title"),
}

QUESTION_INTENT_SOURCE_BONUS: dict[str, dict[str, float]] = {
    "salary": {"job-salary": 0.34, "job-summary": 0.1, "job": 0.18, "job-skill": 0.02, "job-work": 0.02},
    "work_content": {"job-work-content": 0.34, "job-work": 0.34, "job-summary": 0.06, "job": 0.06},
    "skill_gap": {
        "job-skills": 0.22,
        "job-skill": 0.22,
        "market-skill-insight": 0.16,
        "market-skill": 0.16,
        "resume-summary": 0.08,
        "resume": 0.08,
        "job-summary": 0.06,
        "job": 0.06,
    },
    "resume_gap": {
        "resume-summary": 0.18,
        "resume": 0.18,
        "job-skills": 0.18,
        "job-skill": 0.18,
        "job-summary": 0.08,
        "job": 0.08,
    },
    "market": {
        "market-skill-insight": 0.2,
        "market-skill": 0.2,
        "market-task-insight": 0.16,
        "market-task": 0.16,
        "job-summary": 0.06,
        "job": 0.06,
    },
    "source_distribution": {
        "market-source-summary": 0.42,
        "job-summary": 0.08,
        "job": 0.08,
    },
    "role_distribution": {
        "market-role-summary": 0.42,
        "job-summary": 0.08,
        "job": 0.08,
    },
    "location_distribution": {
        "market-location-summary": 0.42,
        "job-summary": 0.08,
        "job": 0.08,
    },
}

ROLE_SIGNAL_ALIASES: dict[str, tuple[str, ...]] = {
    "ai": ("ai應用工程師", "rag ai engineer", "ai engineer", "ai platform engineer", "ai"),
    "firmware": ("韌體工程師", "firmware engineer", "藍牙韌體", "embedded linux firmware"),
    "pm": ("product manager", "產品經理", "pm"),
}

TOKEN_PATTERN = re.compile(r"[a-z0-9+/#.:-]+|[\u4e00-\u9fff]{2,}")
AGGREGATE_HINT_TOKENS = ("目前", "常見", "重點", "主要", "最多", "集中", "分布", "優先", "值得")
AGGREGATE_SALARY_HINT_TOKENS = ("這批", "整體", "大概", "怎麼看", "分布", "市場")
SPECIFIC_JOB_HINT_TOKENS = ("這個職缺", "這份職缺", "這一職缺", "這份工作", "這個工作", "該職缺")
DIRECT_JOB_SUFFIX_HINTS = SPECIFIC_JOB_HINT_TOKENS + (
    "需要哪些技能",
    "需要什麼技能",
    "主要在做什麼",
    "主要做什麼",
    "負責什麼",
    "薪資怎麼寫",
    "薪資是多少",
)
IMPORTANCE_RANK = {
    "高": 3.0,
    "中高": 2.5,
    "中": 2.0,
    "低": 1.0,
}
EMBEDDING_MEMORY_CACHE_MAX = 4096


#把要拿去做 embedding 的文字先清洗乾淨
def prepare_embedding_text(text: str, max_chars: int = 3000) -> str:
    return normalize_text(mask_personal_text(text))[:max_chars]

#把一份資料穩定地轉成唯一 hash key
def stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

#計算兩個向量的 cosine similarity，結果介於 0 到 1 之間，計算兩個向量有多像
def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_list = list(left)
    right_list = list(right)
    if not left_list or not right_list or len(left_list) != len(right_list):
        return 0.0
    numerator = sum(l * r for l, r in zip(left_list, right_list))
    left_norm = math.sqrt(sum(l * l for l in left_list))
    right_norm = math.sqrt(sum(r * r for r in right_list))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


def _collect_signals(text: str) -> set[str]:
    lowered = prepare_embedding_text(text).lower()
    signals: set[str] = set()
    for canonical, aliases in RETRIEVAL_SIGNAL_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            signals.add(canonical)
    return signals


def _tokenize(text: str) -> set[str]:
    lowered = prepare_embedding_text(text).lower()
    return {token for token in TOKEN_PATTERN.findall(lowered) if len(token.strip()) >= 2}


def _combined_chunk_text(chunk: KnowledgeChunk) -> str:
    return chunk.combined_text()


def _classify_question_intents(question: str, signals: set[str]) -> set[str]:
    lowered = prepare_embedding_text(question).lower()
    intents: set[str] = set()
    if "source" in signals or any(token in lowered for token in ("來源", "平台", "哪個來源")):
        intents.add("source_distribution")
    if "location" in signals or any(token in lowered for token in ("地點", "地區", "城市", "哪裡")):
        intents.add("location_distribution")
    if "role" in signals or any(token in lowered for token in ("匹配角色", "哪些角色", "哪種角色", "職稱")):
        intents.add("role_distribution")
    if "salary" in signals or "薪資" in lowered:
        intents.add("salary")
    if "work_content" in signals or any(
        token in lowered
        for token in ("工作內容", "模組", "職責", "做什麼", "主要做什麼", "主要在做什麼", "負責什麼", "在做什麼")
    ):
        intents.add("work_content")
    if "resume" in signals or "缺口" in lowered:
        intents.add("resume_gap")
    if "skill" in signals or any(token in lowered for token in ("技能", "能力", "補強")):
        intents.add("skill_gap")
    if any(token in lowered for token in ("市場", "趨勢", "重視", "主軸", "集中", "常見", "重點", "優先")):
        intents.add("market")
    if not intents:
        intents.add("skill_gap")
    return intents


def _question_prefers_aggregate(question: str) -> bool:
    normalized = prepare_embedding_text(question)
    return any(token in normalized for token in AGGREGATE_HINT_TOKENS)


def _question_prefers_aggregate_salary(question: str) -> bool:
    normalized = prepare_embedding_text(question)
    return any(token in normalized for token in AGGREGATE_SALARY_HINT_TOKENS)


def _question_prefers_specific_job(question: str) -> bool:
    normalized = prepare_embedding_text(question).lower()
    return any(token in normalized for token in SPECIFIC_JOB_HINT_TOKENS)


def _has_direct_title_anchor(question: str, title: str) -> bool:
    lowered_question = prepare_embedding_text(question).lower()
    lowered_title = prepare_embedding_text(title).lower()
    if not lowered_title:
        return False
    title_index = lowered_question.find(lowered_title)
    if title_index == -1:
        return False
    suffix = lowered_question[title_index + len(lowered_title) :].lstrip(" ：:，,。!?？")
    return any(suffix.startswith(token) for token in DIRECT_JOB_SUFFIX_HINTS)


def _has_title_prefix_context(question: str, title: str) -> bool:
    lowered_question = prepare_embedding_text(question).lower()
    lowered_title = prepare_embedding_text(title).lower()
    if not lowered_title:
        return False
    title_index = lowered_question.find(lowered_title)
    if title_index <= 0:
        return False
    prefix = lowered_question[:title_index].strip(" ：:，,。!?？")
    return bool(_tokenize(prefix))


def _role_alignment_bonus(question: str, chunk: KnowledgeChunk) -> float:
    lowered_question = prepare_embedding_text(question).lower()
    lowered_chunk = _combined_chunk_text(chunk).lower()
    bonus = 0.0
    for _, aliases in ROLE_SIGNAL_ALIASES.items():
        query_hit = any(alias.lower() in lowered_question for alias in aliases)
        chunk_hit = any(alias.lower() in lowered_chunk for alias in aliases)
        if query_hit and chunk_hit:
            bonus += 0.12
    return bonus


def _job_reference_bonus(question: str, chunk: KnowledgeChunk) -> float:
    if chunk.source_type.startswith("market-"):
        return 0.0

    metadata = chunk.metadata_items()
    lowered_question = prepare_embedding_text(question).lower()
    has_specific_job_hint = _question_prefers_specific_job(question)

    title = prepare_embedding_text(str(metadata.get("title", ""))).lower()
    company = prepare_embedding_text(str(metadata.get("company", ""))).lower()
    matched_role = prepare_embedding_text(str(metadata.get("matched_role", ""))).lower()

    bonus = 0.0
    if title:
        prefixed_title = _has_title_prefix_context(question, title)
        if _has_direct_title_anchor(question, title):
            if prefixed_title:
                bonus += 0.16
            else:
                bonus += 0.42
        elif title in lowered_question:
            if prefixed_title:
                bonus += 0.04
            else:
                bonus += min(0.24, 0.08 + len(title) * 0.012)
        if prefixed_title and has_specific_job_hint:
            bonus -= 0.06
    if company and company in lowered_question:
        bonus += 0.24
    if has_specific_job_hint and matched_role and matched_role in lowered_question:
        bonus += 0.08
    if has_specific_job_hint and (title or company):
        bonus += 0.06
    return min(0.72, bonus)


def _specific_job_market_penalty(question: str, intents: set[str], chunk: KnowledgeChunk) -> float:
    if not chunk.source_type.startswith("market-"):
        return 0.0
    if not _question_prefers_specific_job(question):
        return 0.0

    penalty = 0.12
    if "work_content" in intents and chunk.source_type in {"market-task-insight", "market-task"}:
        penalty += 0.18
    if "skill_gap" in intents and chunk.source_type in {"market-skill-insight", "market-skill"}:
        penalty += 0.16
    return penalty


def _lexical_overlap_score(question_tokens: set[str], chunk_tokens: set[str]) -> float:
    if not question_tokens or not chunk_tokens:
        return 0.0
    overlap = question_tokens & chunk_tokens
    if not overlap:
        return 0.0
    return min(1.0, len(overlap) / max(1.0, len(question_tokens)))


def _signal_overlap_score(question_signals: set[str], chunk_signals: set[str]) -> float:
    if not question_signals or not chunk_signals:
        return 0.0
    overlap = question_signals & chunk_signals
    if not overlap:
        return 0.0
    return min(1.0, len(overlap) / len(question_signals))


def _source_type_bonus(question: str, intents: set[str], chunk: KnowledgeChunk) -> float:
    aggregate = _question_prefers_aggregate(question)
    specific_job = _question_prefers_specific_job(question)
    effective_intents = set(intents)
    if effective_intents & {"source_distribution", "role_distribution", "location_distribution"}:
        effective_intents.discard("market")

    bonus = 0.0
    for intent in effective_intents:
        bonus += QUESTION_INTENT_SOURCE_BONUS.get(intent, {}).get(chunk.source_type, 0.0)
    if aggregate and "skill_gap" in intents and chunk.source_type in {"market-skill-insight", "market-skill"}:
        bonus += 0.48
    if aggregate and "skill_gap" in intents and chunk.source_type in {"job-skills", "job-skill"}:
        bonus += 0.16
    if aggregate and "work_content" in intents and chunk.source_type in {"market-task-insight", "market-task"}:
        bonus += 0.52
    if aggregate and "work_content" in intents and chunk.source_type in {"job-work-content", "job-work"}:
        bonus += 0.18
    if _question_prefers_aggregate_salary(question) and "salary" in intents and chunk.source_type in {"job-summary", "job"}:
        bonus += 0.2
    if specific_job and "work_content" in intents and chunk.source_type in {"job-work-content", "job-work"}:
        bonus += 0.24
    if specific_job and "work_content" in intents and chunk.source_type in {"job-summary", "job"}:
        bonus += 0.08
    if specific_job and "skill_gap" in intents and chunk.source_type in {"job-skills", "job-skill"}:
        bonus += 0.22
    if specific_job and "skill_gap" in intents and chunk.source_type in {"job-summary", "job"}:
        bonus += 0.08
    if specific_job and "salary" in intents and chunk.source_type in {"job-salary"}:
        bonus += 0.22
    if specific_job and "salary" in intents and chunk.source_type in {"job-summary", "job"}:
        bonus += 0.1
    return bonus


def _market_priority_bonus(question: str, intents: set[str], chunk: KnowledgeChunk) -> float:
    metadata = chunk.metadata_items()
    try:
        occurrences = float(metadata.get("occurrences", 0))
    except (TypeError, ValueError):
        occurrences = 0.0
    importance = IMPORTANCE_RANK.get(str(metadata.get("importance", "")).strip(), 0.0)

    if _question_prefers_aggregate(question) and "skill_gap" in intents and chunk.source_type in {"market-skill-insight", "market-skill"}:
        return min(0.42, occurrences * 0.02 + importance * 0.06)
    if _question_prefers_aggregate(question) and "work_content" in intents and chunk.source_type in {"market-task-insight", "market-task"}:
        return min(0.42, occurrences * 0.02 + importance * 0.06)
    return 0.0


def _hybrid_score(
    *,
    embedding_score: float,
    question: str,
    question_tokens: set[str],
    question_signals: set[str],
    intents: set[str],
    chunk: KnowledgeChunk,
) -> float:
    chunk_text = _combined_chunk_text(chunk)
    chunk_tokens = _tokenize(chunk_text)
    chunk_signals = _collect_signals(chunk_text)
    lexical = _lexical_overlap_score(question_tokens, chunk_tokens)
    signal = _signal_overlap_score(question_signals, chunk_signals)
    type_bonus = _source_type_bonus(question, intents, chunk)
    market_priority_bonus = _market_priority_bonus(question, intents, chunk)
    role_bonus = _role_alignment_bonus(question, chunk)
    job_bonus = _job_reference_bonus(question, chunk)
    market_penalty = _specific_job_market_penalty(question, intents, chunk)
    return (
        embedding_score * 0.52
        + lexical * 0.18
        + signal * 0.22
        + type_bonus
        + market_priority_bonus
        + role_bonus
        + job_bonus
        - market_penalty
    )


def _coarse_candidate_score(
    *,
    question: str,
    question_tokens: set[str],
    question_signals: set[str],
    intents: set[str],
    chunk: KnowledgeChunk,
) -> float:
    chunk_text = _combined_chunk_text(chunk)
    chunk_tokens = _tokenize(chunk_text)
    chunk_signals = _collect_signals(chunk_text)
    lexical = _lexical_overlap_score(question_tokens, chunk_tokens)
    signal = _signal_overlap_score(question_signals, chunk_signals)
    type_bonus = _source_type_bonus(question, intents, chunk)
    market_priority_bonus = _market_priority_bonus(question, intents, chunk)
    role_bonus = _role_alignment_bonus(question, chunk)
    job_bonus = _job_reference_bonus(question, chunk)
    market_penalty = _specific_job_market_penalty(question, intents, chunk)
    return lexical * 0.35 + signal * 0.3 + type_bonus + market_priority_bonus + role_bonus + job_bonus - market_penalty


def _diversity_target_source_types(question: str, intents: set[str]) -> tuple[str, ...]:
    if _question_prefers_specific_job(question) and "work_content" in intents:
        return ("job-work-content", "job-summary")
    if _question_prefers_specific_job(question) and "skill_gap" in intents:
        return ("job-skills", "job-summary")
    if _question_prefers_specific_job(question) and "salary" in intents:
        return ("job-salary", "job-summary")
    if _question_prefers_aggregate(question) and "skill_gap" in intents:
        return ("market-skill-insight", "job-skills")
    if _question_prefers_aggregate(question) and "work_content" in intents:
        return ("market-task-insight", "job-work-content")
    if _question_prefers_aggregate_salary(question) and "salary" in intents:
        return ("job-salary", "job-summary")
    return ()


def _select_diverse_top_k(
    *,
    question: str,
    intents: set[str],
    scored: list[tuple[float, KnowledgeChunk]],
    top_k: int,
) -> list[KnowledgeChunk]:
    diversity_targets = _diversity_target_source_types(question, intents)
    if not diversity_targets:
        return [chunk for _, chunk in scored[:top_k]]

    selected: list[KnowledgeChunk] = []
    selected_ids: set[str] = set()
    for source_type in diversity_targets:
        match = next((chunk for _, chunk in scored if chunk.source_type == source_type), None)
        if match is None or match.chunk_id in selected_ids:
            continue
        selected.append(match)
        selected_ids.add(match.chunk_id)

    for _, chunk in scored:
        if chunk.chunk_id in selected_ids:
            continue
        selected.append(chunk)
        selected_ids.add(chunk.chunk_id)
        if len(selected) >= top_k:
            break

    return selected[:top_k]


def _select_candidate_chunks(
    *,
    question: str,
    question_tokens: set[str],
    question_signals: set[str],
    intents: set[str],
    chunks: list[KnowledgeChunk],
    top_k: int,
) -> list[KnowledgeChunk]:
    candidate_limit = min(len(chunks), max(top_k * 6, 24))
    if len(chunks) <= candidate_limit:
        return chunks

    coarse_scored: list[tuple[float, KnowledgeChunk]] = []
    positive_count = 0
    for chunk in chunks:
        score = _coarse_candidate_score(
            question=question,
            question_tokens=question_tokens,
            question_signals=question_signals,
            intents=intents,
            chunk=chunk,
        )
        if score > 0:
            positive_count += 1
        coarse_scored.append((score, chunk))

    coarse_scored.sort(key=lambda item: item[0], reverse=True)

    if positive_count == 0:
        return chunks[:candidate_limit]

    if positive_count < candidate_limit:
        return [chunk for _, chunk in coarse_scored[:candidate_limit]]

    return _select_diverse_top_k(
        question=question,
        intents=intents,
        scored=coarse_scored,
        top_k=candidate_limit,
    )

#整個檢索器本體
class EmbeddingRetriever:
    def __init__(
        self,
        *,
        client: Any,
        embedding_model: str,
        cache_dir: Path | None = None,
    ) -> None:
        self.client = client
        self.embedding_model = embedding_model
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.last_usage = merge_openai_usage()
        self._memory_cache: dict[str, list[float]] = {}
        self._embed_stats: dict[str, int] = {}
        self.last_stats: dict[str, Any] = {}

    def retrieve(
        self,
        *,
        question: str,
        chunks: list[KnowledgeChunk],
        top_k: int,
    ) -> list[KnowledgeChunk]:
        if not chunks:
            return []
        self.last_usage = merge_openai_usage()
        self._embed_stats = {
            "embedding_memory_hits": 0,
            "embedding_disk_hits": 0,
            "embedding_remote_texts": 0,
            "embedding_remote_batches": 0,
        }

        query_text = prepare_embedding_text(question)
        question_tokens = _tokenize(question)
        question_signals = _collect_signals(question)
        intents = _classify_question_intents(question, question_signals)
        candidate_chunks = _select_candidate_chunks(
            question=question,
            question_tokens=question_tokens,
            question_signals=question_signals,
            intents=intents,
            chunks=chunks,
            top_k=top_k,
        )
        chunk_texts = [prepare_embedding_text(chunk.text) for chunk in candidate_chunks]
        embeddings = self._embed_texts([query_text] + chunk_texts)
        query_embedding = embeddings.get(query_text, [])

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk, text in zip(candidate_chunks, chunk_texts):
            embedding_score = cosine_similarity(query_embedding, embeddings.get(text, []))
            score = _hybrid_score(
                embedding_score=embedding_score,
                question=question,
                question_tokens=question_tokens,
                question_signals=question_signals,
                intents=intents,
                chunk=chunk,
            )
            if score <= 0:
                continue
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = _select_diverse_top_k(
            question=question,
            intents=intents,
            scored=scored,
            top_k=top_k,
        )
        self.last_stats = {
            "question_intents": sorted(intents),
            "candidate_chunk_count": len(candidate_chunks),
            "retrieval_scored_chunk_count": len(scored),
            "retrieved_chunk_count": len(selected),
            "top_k": int(top_k),
            **self._embed_stats,
        }
        return selected

    def _embed_texts(self, texts: list[str]) -> dict[str, list[float]]:
        vectors: dict[str, list[float]] = {}
        missing: list[str] = []
        for text in unique_preserving_order([text for text in texts if text]):
            cache_key = stable_hash({"model": self.embedding_model, "text": text})
            memory_cached = self._memory_cache.get(cache_key)
            if memory_cached is not None:
                vectors[text] = list(memory_cached)
                self._embed_stats["embedding_memory_hits"] = (
                    int(self._embed_stats.get("embedding_memory_hits", 0)) + 1
                )
                continue

            cached = self._read_cache(cache_key)
            if cached is not None:
                embedding = [float(value) for value in cached.get("embedding", [])]
                vectors[text] = embedding
                self._remember_memory_embedding(cache_key, embedding)
                self._embed_stats["embedding_disk_hits"] = (
                    int(self._embed_stats.get("embedding_disk_hits", 0)) + 1
                )
                continue

            missing.append(text)

        for batch in chunked(missing, 50):
            if not batch:
                continue
            self._embed_stats["embedding_remote_batches"] = (
                int(self._embed_stats.get("embedding_remote_batches", 0)) + 1
            )
            self._embed_stats["embedding_remote_texts"] = (
                int(self._embed_stats.get("embedding_remote_texts", 0)) + len(batch)
            )
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch,
            )
            self.last_usage = merge_openai_usage(
                self.last_usage,
                extract_openai_usage(response),
            )
            for text, item in zip(batch, response.data):
                embedding = [float(value) for value in item.embedding]
                vectors[text] = embedding
                cache_key = stable_hash({"model": self.embedding_model, "text": text})
                self._remember_memory_embedding(cache_key, embedding)
                self._write_cache(cache_key, {"embedding": embedding})
        return vectors

    def _remember_memory_embedding(self, key: str, embedding: list[float]) -> None:
        self._memory_cache[key] = list(embedding)
        while len(self._memory_cache) > EMBEDDING_MEMORY_CACHE_MAX:
            oldest_key = next(iter(self._memory_cache))
            self._memory_cache.pop(oldest_key, None)

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        if self.cache_dir is None:
            return None
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_cache(self, key: str, payload: dict[str, Any]) -> None:
        if self.cache_dir is None:
            return
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
