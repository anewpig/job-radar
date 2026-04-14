"""Structured models for the job-search workflow agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


AgentRoute = Literal["assistant", "agent"]
AgentStepStatus = Literal[
    "planned",
    "success",
    "blocked",
    "failed",
    "waiting_confirmation",
    "cancelled",
    "skipped",
]
AgentTaskStatus = Literal[
    "planned",
    "running",
    "waiting_confirmation",
    "completed",
    "failed",
    "blocked",
    "cancelled",
]
AgentToolStatus = Literal[
    "success",
    "blocked",
    "failed",
    "needs_confirmation",
    "cancelled",
]

AGENT_TASK_SCHEMA_VERSION = "assistant_agent_task.v1"


@dataclass(slots=True)
class AgentIntent:
    route: AgentRoute = "assistant"
    kind: str = "assistant_chat"
    user_goal: str = ""
    actions: list[str] = field(default_factory=list)
    requires_write: bool = False
    extracted: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentToolCall:
    step_id: str
    tool_name: str
    status: AgentToolStatus
    summary: str = ""
    user_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentStep:
    step_id: str
    title: str
    tool_name: str
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: AgentStepStatus = "planned"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentPendingConfirmation:
    confirmation_id: str
    task_id: str
    step_id: str
    tool_name: str
    message: str
    target_type: str = ""
    target_id: str = ""
    before_summary: str = ""
    after_summary: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentTaskPlan:
    task_id: str
    question: str
    trace_id: str
    intent: AgentIntent
    title: str
    summary: str
    steps: list[AgentStep] = field(default_factory=list)
    status: AgentTaskStatus = "planned"
    result_tab: str = ""
    schema_version: str = AGENT_TASK_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentExecutionResult:
    task_id: str
    question: str
    trace_id: str
    intent_kind: str
    status: AgentTaskStatus
    title: str
    summary: str
    key_points: list[str] = field(default_factory=list)
    answer_text: str = ""
    next_step: str = ""
    result_tab: str = ""
    steps: list[AgentStep] = field(default_factory=list)
    tool_calls: list[AgentToolCall] = field(default_factory=list)
    pending_confirmation: AgentPendingConfirmation | None = None
    schema_version: str = AGENT_TASK_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
