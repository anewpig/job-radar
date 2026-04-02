from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import AssistantCitation, AssistantResponse, MarketSnapshot, ResumeProfile
from ..resume_analysis import mask_personal_text
from ..utils import ensure_directory
from .chunks import build_chunks
from .prompts import build_answer_prompt
from .retrieval import EmbeddingRetriever

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None


class JobMarketRAGAssistant:
    def __init__(
        self,
        api_key: str,
        answer_model: str,
        embedding_model: str,
        base_url: str = "",
        cache_dir: Path | None = None,
        client: Any | None = None,
    ) -> None:
        if OpenAI is None and client is None:
            raise RuntimeError("OpenAI 套件不可用，無法啟用 RAG 助理。")
        if client is None and not api_key:
            raise RuntimeError("沒有提供 OPENAI_API_KEY。")

        if client is not None:
            self.client = client
        else:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)

        self.answer_model = answer_model
        self.embedding_model = embedding_model
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.embedding_cache_dir = (
            ensure_directory(self.cache_dir / "rag_embeddings")
            if self.cache_dir
            else None
        )
        self.retriever = EmbeddingRetriever(
            client=self.client,
            embedding_model=self.embedding_model,
            cache_dir=self.embedding_cache_dir,
        )

    def answer_question(
        self,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None = None,
        top_k: int = 8,
    ) -> AssistantResponse:
        chunks = self._build_chunks(snapshot=snapshot, resume_profile=resume_profile)
        retrieved = self._retrieve(question=question, chunks=chunks, top_k=top_k)
        prompt = self._build_answer_prompt(
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            chunks=retrieved,
        )
        response = self.client.responses.create(
            model=self.answer_model,
            temperature=0.2,
            max_output_tokens=1200,
            input=prompt,
        )
        answer_text = getattr(response, "output_text", "").strip()
        citations = [
            AssistantCitation(
                label=chunk.label,
                url=chunk.url,
                snippet=mask_personal_text(chunk.text[:180]),
                source_type=chunk.source_type,
            )
            for chunk in retrieved[:5]
        ]
        notes = [
            f"已檢索 {len(retrieved)} 個知識片段",
            f"資料快照時間：{snapshot.generated_at}",
        ]
        return AssistantResponse(
            question=question,
            answer=answer_text or "目前沒有足夠資訊可回答這個問題。",
            citations=citations,
            retrieval_notes=notes,
            used_chunks=len(retrieved),
            model=self.answer_model,
            retrieval_model=self.embedding_model,
        )

    def generate_report(
        self,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None = None,
    ) -> AssistantResponse:
        report_question = (
            "請產出一份簡短求職報告，至少涵蓋："
            "1. 可以優先學習的技能 "
            "2. 還需補足的技能 "
            "3. 工作薪資區間 "
            "4. 常見工作內容 "
            "5. 履歷與市場的匹配建議"
        )
        return self.answer_question(
            question=report_question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            top_k=10,
        )

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
