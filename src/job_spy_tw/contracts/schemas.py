"""JSON schema definitions for core DTO contracts."""

from __future__ import annotations

from ..models import (
    ASSISTANT_RESPONSE_SCHEMA_VERSION,
    MARKET_SNAPSHOT_SCHEMA_VERSION,
    RESUME_PROFILE_SCHEMA_VERSION,
)


SCHEMA_REGISTRY: dict[str, dict[str, object]] = {
    MARKET_SNAPSHOT_SCHEMA_VERSION: {
        "title": "MarketSnapshot",
        "type": "object",
        "required": ["schema_version", "generated_at", "queries", "jobs", "skills"],
        "properties": {
            "schema_version": {"type": "string"},
            "generated_at": {"type": "string"},
            "queries": {"type": "array", "items": {"type": "string"}},
            "role_targets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "priority"],
                    "properties": {
                        "name": {"type": "string"},
                        "priority": {"type": "integer"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "jobs": {"type": "array"},
            "skills": {"type": "array"},
            "task_insights": {"type": "array"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "snapshot_kind": {"type": "string"},
            "data_quality": {"type": "object"},
        },
    },
    RESUME_PROFILE_SCHEMA_VERSION: {
        "title": "ResumeProfile",
        "type": "object",
        "required": ["schema_version", "summary", "extraction_method"],
        "properties": {
            "schema_version": {"type": "string"},
            "source_name": {"type": "string"},
            "summary": {"type": "string"},
            "target_roles": {"type": "array", "items": {"type": "string"}},
            "core_skills": {"type": "array", "items": {"type": "string"}},
            "tool_skills": {"type": "array", "items": {"type": "string"}},
            "domain_keywords": {"type": "array", "items": {"type": "string"}},
            "preferred_tasks": {"type": "array", "items": {"type": "string"}},
            "generated_prompts": {"type": "array", "items": {"type": "string"}},
            "match_keywords": {"type": "array", "items": {"type": "string"}},
            "extraction_method": {"type": "string"},
            "llm_model": {"type": "string"},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    },
    ASSISTANT_RESPONSE_SCHEMA_VERSION: {
        "title": "AssistantResponse",
        "type": "object",
        "required": ["schema_version", "question", "answer", "answer_mode"],
        "properties": {
            "schema_version": {"type": "string"},
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "summary": {"type": "string"},
            "key_points": {"type": "array", "items": {"type": "string"}},
            "limitations": {"type": "array", "items": {"type": "string"}},
            "next_step": {"type": "string"},
            "answer_mode": {"type": "string"},
            "market_sections": {"type": "array"},
            "guidance_sections": {"type": "array"},
            "comparison_sections": {"type": "array"},
            "citations": {"type": "array"},
            "retrieval_notes": {"type": "array"},
            "used_chunks": {"type": "integer"},
            "model": {"type": "string"},
            "retrieval_model": {"type": "string"},
        },
    },
}
