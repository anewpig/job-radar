"""Application-layer facade for the job-search workflow agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..assistant_agent import AgentIntent, AgentTaskPlan, JobSearchWorkflowAgent


@dataclass(slots=True)
class AssistantAgentPlanningContext:
    current_search_rows: list[dict[str, object]]
    custom_queries_text: str
    crawl_preset_label: str
    active_saved_search_name: str = ""
    has_snapshot: bool = False
    has_profile: bool = False
    remembered_target_roles: list[str] = field(default_factory=list)
    remembered_search_roles: list[str] = field(default_factory=list)
    remembered_locations: list[str] = field(default_factory=list)
    remembered_skills: list[str] = field(default_factory=list)
    remembered_experience_level: str = ""
    recent_task_summaries: list[str] = field(default_factory=list)


class AssistantAgentApplication:
    """Facade used by UI to plan job-search workflow agent tasks."""

    def __init__(self, agent: JobSearchWorkflowAgent | None = None) -> None:
        self._agent = agent or JobSearchWorkflowAgent()

    def route_request(
        self,
        *,
        question: str,
        planning_context: AssistantAgentPlanningContext,
    ) -> AgentIntent:
        return self._agent.route_request(
            question=question,
            planning_context=planning_context,
        )

    def build_task_plan(
        self,
        *,
        question: str,
        intent: AgentIntent,
    ) -> AgentTaskPlan:
        return self._agent.build_task_plan(
            question=question,
            intent=intent,
        )
