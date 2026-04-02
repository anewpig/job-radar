from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from ..resume_analysis import mask_personal_text
from ..utils import chunked, ensure_directory, normalize_text, unique_preserving_order
from .models import KnowledgeChunk


def prepare_embedding_text(text: str, max_chars: int = 3000) -> str:
    return normalize_text(mask_personal_text(text))[:max_chars]


def stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
        chunk_texts = [prepare_embedding_text(chunk.text) for chunk in chunks]
        embeddings = self._embed_texts([query_text] + chunk_texts)
        query_embedding = embeddings.get(query_text, [])

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk, text in zip(chunks, chunk_texts):
            score = cosine_similarity(query_embedding, embeddings.get(text, []))
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
