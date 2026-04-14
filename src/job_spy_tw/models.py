"""Shared dataclasses and domain models used across the application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

MARKET_SNAPSHOT_SCHEMA_VERSION = "market_snapshot.v2"
ASSISTANT_RESPONSE_SCHEMA_VERSION = "assistant_response.v1"
RESUME_PROFILE_SCHEMA_VERSION = "resume_profile.v1"


@dataclass(slots=True)
class TargetRole:
    name: str
    priority: int
    keywords: list[str] = field(default_factory=list)

    @property
    def weight(self) -> float:
        return max(0.2, 1.1 - ((self.priority - 1) * 0.12))


@dataclass(slots=True)
class SalaryEstimate:
    predicted_low: int = 0
    predicted_mid: int = 0
    predicted_high: int = 0
    currency: str = "TWD"
    period: str = "monthly"
    confidence: float = 0.0
    evidence_job_urls: list[str] = field(default_factory=list)
    model_version: str = ""
    fallback_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JobListing:
    source: str
    title: str
    company: str
    location: str
    url: str
    summary: str = ""
    description: str = ""
    salary: str = ""
    posted_at: str = ""
    matched_role: str = ""
    relevance_score: float = 0.0
    extracted_skills: list[str] = field(default_factory=list)
    work_content_items: list[str] = field(default_factory=list)
    required_skill_items: list[str] = field(default_factory=list)
    requirement_items: list[str] = field(default_factory=list)
    detail_sections: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source_record_id: str = ""
    canonical_identity_key: str = ""
    lineage_trail: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    salary_estimate: SalaryEstimate | None = None

    def __post_init__(self) -> None:
        if isinstance(self.salary_estimate, dict):
            self.salary_estimate = SalaryEstimate(**self.salary_estimate)

    def combined_text(self) -> str:
        return "\n".join(
            filter(
                None,
                [
                    self.title,
                    self.company,
                    self.summary,
                    self.description,
                    "\n".join(self.work_content_items),
                    "\n".join(self.required_skill_items),
                    "\n".join(self.requirement_items),
                    " ".join(self.tags),
                ],
            )
        )

    def requirement_text(self) -> str:
        return "\n".join(filter(None, self.required_skill_items + self.requirement_items))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SkillInsight:
    skill: str
    category: str
    score: float
    importance: str
    occurrences: int
    sources: list[str] = field(default_factory=list)
    sample_jobs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ItemInsight:
    item: str
    score: float
    importance: str
    occurrences: int
    sources: list[str] = field(default_factory=list)
    sample_jobs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResumeProfile:
    source_name: str = ""
    raw_text: str = ""
    summary: str = ""
    target_roles: list[str] = field(default_factory=list)
    core_skills: list[str] = field(default_factory=list)
    tool_skills: list[str] = field(default_factory=list)
    domain_keywords: list[str] = field(default_factory=list)
    preferred_tasks: list[str] = field(default_factory=list)
    generated_prompts: list[str] = field(default_factory=list)
    match_keywords: list[str] = field(default_factory=list)
    extraction_method: str = "rule_based"
    llm_model: str = ""
    notes: list[str] = field(default_factory=list)
    schema_version: str = RESUME_PROFILE_SCHEMA_VERSION

    def searchable_text(self) -> str:
        return "\n".join(
            filter(
                None,
                [
                    self.summary,
                    " ".join(self.target_roles),
                    " ".join(self.core_skills),
                    " ".join(self.tool_skills),
                    " ".join(self.domain_keywords),
                    " ".join(self.preferred_tasks),
                    " ".join(self.generated_prompts),
                    " ".join(self.match_keywords),
                ],
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResumeJobMatch:
    job_url: str
    title: str
    company: str
    source: str
    matched_role: str
    overall_score: float
    role_score: float
    skill_score: float
    task_score: float
    keyword_score: float
    market_fit_score: float = 0.0
    exact_match_score: float = 0.0
    exact_skill_score: float = 0.0
    exact_task_score: float = 0.0
    title_similarity: float = 0.0
    semantic_similarity: float = 0.0
    title_reason: str = ""
    scoring_method: str = "rule_based"
    matched_skills: list[str] = field(default_factory=list)
    matched_tasks: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    missing_tasks: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    fit_summary: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AssistantCitation:
    label: str
    url: str = ""
    snippet: str = ""
    source_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AssistantResponse:
    question: str
    answer: str
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    next_step: str = ""
    answer_mode: str = "market_summary"
    market_sections: list[dict[str, str]] = field(default_factory=list)
    guidance_sections: list[dict[str, str]] = field(default_factory=list)
    comparison_sections: list[dict[str, str]] = field(default_factory=list)
    citations: list[AssistantCitation] = field(default_factory=list)
    retrieval_notes: list[str] = field(default_factory=list)
    used_chunks: int = 0
    model: str = ""
    retrieval_model: str = ""
    schema_version: str = ASSISTANT_RESPONSE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MarketSnapshot:
    generated_at: str
    queries: list[str]
    role_targets: list[TargetRole]
    jobs: list[JobListing]
    skills: list[SkillInsight]
    task_insights: list[ItemInsight] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    schema_version: str = MARKET_SNAPSHOT_SCHEMA_VERSION
    snapshot_kind: str = "complete"
    data_quality: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "queries": self.queries,
            "role_targets": [
                {
                    "name": role.name,
                    "priority": role.priority,
                    "keywords": role.keywords,
                }
                for role in self.role_targets
            ],
            "jobs": [job.to_dict() for job in self.jobs],
            "skills": [skill.to_dict() for skill in self.skills],
            "task_insights": [item.to_dict() for item in self.task_insights],
            "errors": self.errors,
            "snapshot_kind": self.snapshot_kind,
            "data_quality": self.data_quality,
        }


@dataclass(slots=True)
class SavedSearch:
    id: int
    name: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    custom_queries_text: str = ""
    crawl_preset_label: str = "快速"
    signature: str = ""
    known_job_urls: list[str] = field(default_factory=list)
    last_run_at: str = ""
    last_job_count: int = 0
    last_new_job_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FavoriteJob:
    id: int
    saved_at: str
    job_url: str
    title: str
    company: str
    source: str
    saved_search_id: int = 0
    saved_search_name: str = ""
    matched_role: str = ""
    location: str = ""
    salary: str = ""
    application_status: str = "未投遞"
    application_date: str = ""
    interview_date: str = ""
    interview_notes: str = ""
    notes: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JobNotification:
    id: int
    saved_search_id: int
    saved_search_name: str
    created_at: str
    new_jobs: list[dict[str, Any]] = field(default_factory=list)
    is_read: bool = False
    email_sent: bool = False
    line_sent: bool = False
    delivery_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NotificationPreference:
    site_enabled: bool = True
    email_enabled: bool = False
    line_enabled: bool = False
    email_recipients: str = ""
    line_target: str = ""
    line_bind_code: str = ""
    line_bind_requested_at: str = ""
    line_bind_expires_at: str = ""
    line_bound_at: str = ""
    min_relevance_score: float = 20.0
    max_jobs_per_alert: int = 8
    frequency: str = "即時"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentMemoryRecord:
    id: int
    user_id: int
    memory_type: str
    key: str
    summary: str = ""
    value: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    confidence: float = 1.0
    last_used_at: str = ""
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class UserAccount:
    id: int
    email: str
    display_name: str = ""
    role: str = "user"
    is_guest: bool = False
    created_at: str = ""
    updated_at: str = ""
    last_login_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StoredResumeProfile:
    user_id: int
    source_name: str = ""
    profile: ResumeProfile | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "source_name": self.source_name,
            "profile": self.profile.to_dict() if self.profile is not None else None,
            "updated_at": self.updated_at,
        }
