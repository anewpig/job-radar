"""Shared prompt and retrieval version registry."""

from __future__ import annotations


ANSWER_PROMPT_BASE_VERSION = "answer_prompt.v3"
ANSWER_PROMPT_VARIANT_VERSIONS: dict[str, str] = {
    "control": f"{ANSWER_PROMPT_BASE_VERSION}.control",
    "compact_qa": f"{ANSWER_PROMPT_BASE_VERSION}.compact_qa",
}
ANSWER_PROMPT_VERSION = ANSWER_PROMPT_VARIANT_VERSIONS["control"]
RETRIEVAL_POLICY_VERSION = "retrieval_policy.v5"
CHUNKING_POLICY_VERSION = "chunking.v5"
PERSISTENT_INDEX_VERSION = "persistent_ann.v2"
RESUME_EXTRACTION_PROMPT_VERSION = "resume_extract_prompt.v2"
TITLE_SIMILARITY_PROMPT_VERSION = "resume_title_similarity.v1"


def normalize_prompt_variant(value: str) -> str:
    """Normalize answer prompt experiment labels."""
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in ANSWER_PROMPT_VARIANT_VERSIONS:
        return normalized
    return "control"


def answer_prompt_version(value: str) -> str:
    """Resolve prompt version for the current variant."""
    return ANSWER_PROMPT_VARIANT_VERSIONS[normalize_prompt_variant(value)]
