"""Assistant helpers for retrieval."""
#把問題和每個知識片段都轉成 embedding，然後用 hybrid retrieval 找最相關 chunks
from __future__ import annotations

import hashlib #產生 hash 值
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

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
    if "work_content" in signals or any(token in lowered for token in ("工作內容", "模組", "職責")):
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
    effective_intents = set(intents)
    if effective_intents & {"source_distribution", "role_distribution", "location_distribution"}:
        effective_intents.discard("market")

    bonus = 0.0
    for intent in effective_intents:
        bonus += QUESTION_INTENT_SOURCE_BONUS.get(intent, {}).get(chunk.source_type, 0.0)
    if aggregate and "skill_gap" in intents and chunk.source_type in {"market-skill-insight", "market-skill"}:
        bonus += 0.48
    if aggregate and "work_content" in intents and chunk.source_type in {"market-task-insight", "market-task"}:
        bonus += 0.52
    return bonus


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
    role_bonus = _role_alignment_bonus(question, chunk)
    return (
        embedding_score * 0.52
        + lexical * 0.18
        + signal * 0.22
        + type_bonus
        + role_bonus
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

    def retrieve(
        self,
        *,
        question: str,
        chunks: list[KnowledgeChunk],
        top_k: int,
    ) -> list[KnowledgeChunk]:
        if not chunks:
            return []

        query_text = prepare_embedding_text(question)
        question_tokens = _tokenize(question)
        question_signals = _collect_signals(question)
        intents = _classify_question_intents(question, question_signals)
        chunk_texts = [prepare_embedding_text(chunk.text) for chunk in chunks]
        embeddings = self._embed_texts([query_text] + chunk_texts)
        query_embedding = embeddings.get(query_text, [])

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk, text in zip(chunks, chunk_texts):
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
        return [chunk for _, chunk in scored[:top_k]]

    def _embed_texts(self, texts: list[str]) -> dict[str, list[float]]:
        vectors: dict[str, list[float]] = {}
        missing: list[str] = []
        for text in unique_preserving_order([text for text in texts if text]):
            cache_key = stable_hash({"model": self.embedding_model, "text": text})
            cached = self._read_cache(cache_key)
            if cached is not None:
                vectors[text] = [float(value) for value in cached.get("embedding", [])]
            else:
                missing.append(text)

        for batch in chunked(missing, 50):
            if not batch:
                continue
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch,
            )
            for text, item in zip(batch, response.data):
                embedding = [float(value) for value in item.embedding]
                vectors[text] = embedding
                cache_key = stable_hash({"model": self.embedding_model, "text": text})
                self._write_cache(cache_key, {"embedding": embedding})
        return vectors

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
