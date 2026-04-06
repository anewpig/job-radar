"""Compatibility wrapper exposing assistant and retrieval APIs."""

from __future__ import annotations

"""Backward-compatible public entrypoint for the RAG assistant."""

from .assistant import JobMarketRAGAssistant, KnowledgeChunk

__all__ = ["JobMarketRAGAssistant", "KnowledgeChunk"]
