"""Compatibility wrapper exposing resume analysis APIs."""

from __future__ import annotations

"""Backward-compatible public entrypoint for resume analysis."""

from .resume import (
    OpenAIResumeExtractor,
    OpenAIResumeMatcher,
    ResumeAnalysisService,
    ResumeMatcher,
    RuleBasedResumeExtractor,
    describe_resume_source,
    extract_resume_text,
    mask_personal_items,
    mask_personal_text,
    summarize_match_gaps,
)

__all__ = [
    "OpenAIResumeExtractor",
    "OpenAIResumeMatcher",
    "ResumeAnalysisService",
    "ResumeMatcher",
    "RuleBasedResumeExtractor",
    "describe_resume_source",
    "extract_resume_text",
    "mask_personal_items",
    "mask_personal_text",
    "summarize_match_gaps",
]
