"""Tests for staged crawl UI flow helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui import crawl_runtime_flow  # noqa: E402


class _SessionState(dict):
    def __getattr__(self, key: str):
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class CrawlRuntimeFlowTests(unittest.TestCase):
    def _fake_streamlit(self, session_state: dict[str, object]):
        status_handle = SimpleNamespace(
            write=mock.Mock(),
            update=mock.Mock(),
        )
        return SimpleNamespace(
            session_state=_SessionState(session_state),
            status=mock.Mock(return_value=status_handle),
            rerun=mock.Mock(),
            warning=mock.Mock(),
        )

    def test_explicit_run_routes_next_render_to_overview(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "search_role_rows": [{"enabled": True, "role": "AI 工程師", "keywords": ""}],
                "search_role_draft_index": 0,
                "custom_queries_text": "",
                "crawl_preset_label": "快速",
                "crawl_refresh_mode": "使用快取",
                "crawl_worker_id": "worker-1",
                "active_saved_search_id": 0,
                "main_tab_selection": "assistant",
                "pending_main_tab_selection": "",
            }
        )
        start_result = SimpleNamespace(
            status="awaiting_snapshot",
            snapshot=None,
            pending_state=SimpleNamespace(
                query_signature="sig-1",
                active_job_id=12,
                pending_queries=[],
                pending_jobs=[],
                pending_errors=[],
                partial_ready_at="",
                detail_cursor=0,
                detail_total=0,
                remaining_page_cursor=1,
                initial_wave_sources=[],
            ),
            warning_message="",
        )

        with mock.patch.object(crawl_runtime_flow, "st", fake_streamlit):
            with mock.patch.object(crawl_runtime_flow, "get_committed_search_rows", return_value=[]):
                with mock.patch.object(crawl_runtime_flow, "build_role_targets", return_value=[]):
                    with mock.patch.object(crawl_runtime_flow, "apply_crawl_preset", return_value=SimpleNamespace(max_pages_per_source=1, max_detail_jobs_per_source=10)):
                        with mock.patch.object(crawl_runtime_flow, "build_crawl_queries", return_value=["ai engineer"]):
                            with mock.patch.object(crawl_runtime_flow, "estimate_crawl_eta_label", return_value="10 秒"):
                                with mock.patch.object(crawl_runtime_flow, "apply_pending_crawl_state") as apply_state:
                                    with mock.patch.object(crawl_runtime_flow, "CrawlApplication") as crawl_app_cls:
                                        crawl_app_cls.return_value.start.return_value = start_result
                                        crawl_runtime_flow.maybe_start_crawl(
                                            settings=SimpleNamespace(crawl_execution_mode="worker"),
                                            search_setup_state=SimpleNamespace(
                                                run_crawl=True,
                                                crawl_preset=SimpleNamespace(label="快速"),
                                                custom_queries="",
                                                force_refresh=False,
                                            ),
                                            product_store=SimpleNamespace(),
                                            notification_service=SimpleNamespace(),
                                            current_user_id=7,
                                            current_user_is_guest=False,
                                            notification_preferences=SimpleNamespace(),
                                            current_signature="sig-1",
                                        )

        self.assertEqual(fake_streamlit.session_state.main_tab_selection, "overview")
        self.assertEqual(fake_streamlit.session_state.pending_main_tab_selection, "overview")
        apply_state.assert_called_once()
        fake_streamlit.rerun.assert_not_called()

    def test_saved_search_refresh_keeps_current_tab(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "pending_saved_search_refresh_id": 11,
                "search_role_rows": [{"enabled": True, "role": "AI 工程師", "keywords": ""}],
                "search_role_draft_index": 0,
                "custom_queries_text": "",
                "crawl_preset_label": "快速",
                "crawl_refresh_mode": "使用快取",
                "crawl_worker_id": "worker-1",
                "active_saved_search_id": 0,
                "main_tab_selection": "tracking",
                "pending_main_tab_selection": "",
            }
        )
        start_result = SimpleNamespace(
            status="awaiting_snapshot",
            snapshot=None,
            pending_state=SimpleNamespace(
                query_signature="sig-2",
                active_job_id=13,
                pending_queries=[],
                pending_jobs=[],
                pending_errors=[],
                partial_ready_at="",
                detail_cursor=0,
                detail_total=0,
                remaining_page_cursor=1,
                initial_wave_sources=[],
            ),
            warning_message="",
        )

        with mock.patch.object(crawl_runtime_flow, "st", fake_streamlit):
            with mock.patch.object(crawl_runtime_flow, "get_committed_search_rows", return_value=[]):
                with mock.patch.object(crawl_runtime_flow, "build_role_targets", return_value=[]):
                    with mock.patch.object(crawl_runtime_flow, "apply_crawl_preset", return_value=SimpleNamespace(max_pages_per_source=1, max_detail_jobs_per_source=10)):
                        with mock.patch.object(crawl_runtime_flow, "build_crawl_queries", return_value=["ai engineer"]):
                            with mock.patch.object(crawl_runtime_flow, "estimate_crawl_eta_label", return_value="10 秒"):
                                with mock.patch.object(crawl_runtime_flow, "apply_pending_crawl_state"):
                                    with mock.patch.object(crawl_runtime_flow, "CrawlApplication") as crawl_app_cls:
                                        crawl_app_cls.return_value.start.return_value = start_result
                                        crawl_runtime_flow.maybe_start_crawl(
                                            settings=SimpleNamespace(crawl_execution_mode="worker"),
                                            search_setup_state=SimpleNamespace(
                                                run_crawl=False,
                                                crawl_preset=SimpleNamespace(label="快速"),
                                                custom_queries="",
                                                force_refresh=False,
                                            ),
                                            product_store=SimpleNamespace(),
                                            notification_service=SimpleNamespace(),
                                            current_user_id=7,
                                            current_user_is_guest=False,
                                            notification_preferences=SimpleNamespace(),
                                            current_signature="sig-2",
                                        )

        self.assertEqual(fake_streamlit.session_state.main_tab_selection, "tracking")
        self.assertEqual(fake_streamlit.session_state.pending_main_tab_selection, "")

    def test_safe_rerun_fragment_falls_back_to_full_rerun(self) -> None:
        rerun_calls: list[dict[str, object]] = []

        def _rerun(*, scope=None):
            rerun_calls.append({"scope": scope})
            if scope == "fragment":
                raise crawl_runtime_flow.StreamlitAPIException("fragment rerun unavailable")

        fake_streamlit = SimpleNamespace(
            session_state=_SessionState({}),
            rerun=mock.Mock(side_effect=_rerun),
        )

        with mock.patch.object(crawl_runtime_flow, "st", fake_streamlit):
            crawl_runtime_flow._safe_rerun_fragment()

        self.assertEqual(
            rerun_calls,
            [
                {"scope": "fragment"},
                {"scope": None},
            ],
        )


if __name__ == "__main__":
    unittest.main()
