"""Tests for assistant workflow agent routing and confirmation gates."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.application.assistant_agent import AssistantAgentPlanningContext  # noqa: E402
from job_spy_tw.assistant_agent.models import AgentIntent  # noqa: E402
from job_spy_tw.assistant_agent.service import JobSearchWorkflowAgent  # noqa: E402
from job_spy_tw.models import MarketSnapshot, NotificationPreference  # noqa: E402


class _SessionState(dict):
    def __getattr__(self, key: str):
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class _DummyProductStore:
    def __init__(self) -> None:
        self.ai_events: list[dict[str, object]] = []
        self.audit_events: list[dict[str, object]] = []
        self.saved_search_calls: list[dict[str, object]] = []

    def record_ai_monitoring_event(self, **kwargs) -> int:
        self.ai_events.append(kwargs)
        return len(self.ai_events)

    def record_audit_event(self, **kwargs) -> int:
        self.audit_events.append(kwargs)
        return len(self.audit_events)

    def find_saved_search_by_signature(self, *args, **kwargs):
        return None

    def build_signature(self, rows, custom_queries_text, crawl_preset_label) -> str:
        return f"{len(rows)}|{custom_queries_text}|{crawl_preset_label}"

    def save_search(self, **kwargs) -> int:
        self.saved_search_calls.append(kwargs)
        return 101


def _import_runtime_module(fake_streamlit):
    sys.modules.pop("job_spy_tw.ui.assistant_agent_runtime", None)
    with mock.patch.dict(sys.modules, {"streamlit": fake_streamlit}):
        return importlib.import_module("job_spy_tw.ui.assistant_agent_runtime")


class AssistantAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = JobSearchWorkflowAgent()
        self.planning_context = AssistantAgentPlanningContext(
            current_search_rows=[],
            custom_queries_text="",
            crawl_preset_label="快速",
            active_saved_search_name="",
            has_snapshot=False,
            has_profile=False,
        )

    def _saved_search_intent(self) -> AgentIntent:
        return AgentIntent(
            route="agent",
            kind="saved_search_management",
            user_goal="把目前條件存成 saved search",
            actions=["create_or_update_saved_search"],
            requires_write=True,
            extracted={
                "roles": ["AI 工程師"],
                "saved_search_name": "AI 工程師",
            },
            reason="test fixture",
        )

    def test_route_request_detects_job_search_agent_task(self) -> None:
        intent = self.agent.route_request(
            question="幫我找 AI 工程師職缺並整理市場摘要",
            planning_context=self.planning_context,
        )

        self.assertEqual(intent.route, "agent")
        self.assertIn("start_or_refresh_search", intent.actions)
        self.assertIn("summarize_market_snapshot", intent.actions)

    def test_route_request_keeps_general_chat_on_assistant_path(self) -> None:
        intent = self.agent.route_request(
            question="可以講個笑話嗎",
            planning_context=self.planning_context,
        )

        self.assertEqual(intent.route, "assistant")

    def test_build_task_plan_is_stable_for_notification_workflow(self) -> None:
        intent = self.agent.route_request(
            question="幫我更新通知，開 email，每次最多 5 筆",
            planning_context=self.planning_context,
        )

        first = self.agent.build_task_plan(
            question="幫我更新通知，開 email，每次最多 5 筆",
            intent=intent,
        )
        second = self.agent.build_task_plan(
            question="幫我更新通知，開 email，每次最多 5 筆",
            intent=intent,
        )

        self.assertEqual(first.intent.kind, second.intent.kind)
        self.assertEqual(
            [step.tool_name for step in first.steps],
            [step.tool_name for step in second.steps],
        )
        self.assertEqual(
            [step.title for step in first.steps],
            [step.title for step in second.steps],
        )
        self.assertEqual(first.status, "planned")

    def test_profile_update_with_new_target_role_also_plans_search_refresh(self) -> None:
        intent = self.agent.route_request(
            question="幫我把目標職缺改成前端工程師，技能加上 React",
            planning_context=self.planning_context,
        )

        self.assertEqual(intent.route, "agent")
        self.assertEqual(intent.kind, "profile_update_and_search")
        self.assertEqual(
            intent.actions,
            [
                "save_assistant_profile",
                "inspect_snapshot",
                "start_or_refresh_search",
                "open_relevant_surface",
            ],
        )

    def test_followup_search_can_use_memory_roles(self) -> None:
        memory_context = AssistantAgentPlanningContext(
            current_search_rows=[],
            custom_queries_text="",
            crawl_preset_label="快速",
            active_saved_search_name="",
            has_snapshot=False,
            has_profile=True,
            remembered_target_roles=["前端工程師"],
            remembered_search_roles=["前端工程師"],
            recent_task_summaries=["最近搜尋：前端工程師"],
        )

        intent = self.agent.route_request(
            question="幫我再找一次",
            planning_context=memory_context,
        )

        self.assertEqual(intent.route, "agent")
        self.assertIn("start_or_refresh_search", intent.actions)
        self.assertEqual(intent.extracted["roles"], ["前端工程師"])

    def test_execute_agent_plan_requires_confirmation_before_saved_search_write(self) -> None:
        product_store = _DummyProductStore()
        task_plan = self.agent.build_task_plan(
            question="幫我把這組條件存成 saved search",
            intent=self._saved_search_intent(),
        )
        fake_streamlit = SimpleNamespace(
            session_state=_SessionState(
                custom_queries_text="",
                crawl_preset_label="快速",
                search_role_rows=[],
                _app_render_nonce="test",
            )
        )
        runtime_module = _import_runtime_module(fake_streamlit)
        runtime_context = runtime_module.AgentRuntimeContext(
            page_context=SimpleNamespace(
                current_user_id=7,
                current_user_is_guest=False,
                current_user_role="user",
                current_signature="sig-1",
                settings=SimpleNamespace(assistant_model="gpt-test"),
                product_store=product_store,
                notification_preferences=NotificationPreference(),
                active_saved_search=None,
                current_search_name="",
                snapshot=MarketSnapshot(
                    generated_at="",
                    queries=[],
                    role_targets=[],
                    jobs=[],
                    skills=[],
                    task_insights=[],
                ),
                user_data_store=SimpleNamespace(),
            ),
            assistant=SimpleNamespace(),
            assistant_profile=None,
        )

        result = runtime_module.execute_agent_plan(
            runtime_context=runtime_context,
            task_plan=task_plan,
        )

        self.assertEqual(result.status, "waiting_confirmation")
        self.assertIsNotNone(result.pending_confirmation)
        self.assertEqual(product_store.saved_search_calls, [])

    def test_guest_user_cannot_execute_write_tool(self) -> None:
        product_store = _DummyProductStore()
        task_plan = self.agent.build_task_plan(
            question="幫我把這組條件存成 saved search",
            intent=self._saved_search_intent(),
        )
        fake_streamlit = SimpleNamespace(
            session_state=_SessionState(
                custom_queries_text="",
                crawl_preset_label="快速",
                search_role_rows=[],
                _app_render_nonce="test",
            )
        )
        runtime_module = _import_runtime_module(fake_streamlit)
        runtime_context = runtime_module.AgentRuntimeContext(
            page_context=SimpleNamespace(
                current_user_id=0,
                current_user_is_guest=True,
                current_user_role="guest",
                current_signature="sig-guest",
                settings=SimpleNamespace(assistant_model="gpt-test"),
                product_store=product_store,
                notification_preferences=NotificationPreference(),
                active_saved_search=None,
                current_search_name="",
                snapshot=MarketSnapshot(
                    generated_at="",
                    queries=[],
                    role_targets=[],
                    jobs=[],
                    skills=[],
                    task_insights=[],
                ),
                user_data_store=SimpleNamespace(),
            ),
            assistant=SimpleNamespace(),
            assistant_profile=None,
        )

        result = runtime_module.execute_agent_plan(
            runtime_context=runtime_context,
            task_plan=task_plan,
        )

        self.assertEqual(result.status, "blocked")
        self.assertIn("訪客模式", result.summary)
        self.assertEqual(product_store.saved_search_calls, [])

    def test_confirmed_saved_search_write_persists_after_confirmation(self) -> None:
        product_store = _DummyProductStore()
        task_plan = self.agent.build_task_plan(
            question="幫我把這組條件存成 saved search",
            intent=self._saved_search_intent(),
        )
        fake_streamlit = SimpleNamespace(
            session_state=_SessionState(
                custom_queries_text="",
                crawl_preset_label="快速",
                search_role_rows=[],
                last_crawl_signature="",
                snapshot=None,
                active_saved_search_id=None,
                _app_render_nonce="test",
            )
        )
        runtime_module = _import_runtime_module(fake_streamlit)
        runtime_context = runtime_module.AgentRuntimeContext(
            page_context=SimpleNamespace(
                current_user_id=9,
                current_user_is_guest=False,
                current_user_role="user",
                current_signature="sig-confirm",
                settings=SimpleNamespace(assistant_model="gpt-test"),
                product_store=product_store,
                notification_preferences=NotificationPreference(),
                active_saved_search=None,
                current_search_name="",
                snapshot=MarketSnapshot(
                    generated_at="",
                    queries=[],
                    role_targets=[],
                    jobs=[],
                    skills=[],
                    task_insights=[],
                ),
                user_data_store=SimpleNamespace(),
            ),
            assistant=SimpleNamespace(),
            assistant_profile=None,
        )

        first = runtime_module.execute_agent_plan(
            runtime_context=runtime_context,
            task_plan=task_plan,
        )
        second = runtime_module.resolve_pending_confirmation(
            runtime_context=runtime_context,
            task_plan=task_plan,
            pending_confirmation=first.pending_confirmation,
            previous_result=first,
            approved=True,
        )

        self.assertEqual(first.status, "waiting_confirmation")
        self.assertEqual(second.status, "completed")
        self.assertEqual(len(product_store.saved_search_calls), 1)
        self.assertTrue(product_store.audit_events)


if __name__ == "__main__":
    unittest.main()
