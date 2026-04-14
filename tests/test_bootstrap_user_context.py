"""Tests for bootstrap-time user/session helpers."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot, TargetRole  # noqa: E402
from job_spy_tw.storage import save_snapshot  # noqa: E402
from job_spy_tw.ui import bootstrap_user_context  # noqa: E402


class _SessionState(dict):
    def __getattr__(self, key: str):
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class BootstrapUserContextTests(unittest.TestCase):
    def build_settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=5.0,
            request_delay=0.2,
            max_concurrent_requests=4,
            max_pages_per_source=2,
            max_detail_jobs_per_source=8,
            min_relevance_score=0.0,
            location="台灣",
            enable_cake=True,
            enable_linkedin=True,
            allow_insecure_ssl_fallback=True,
            user_agent="test-agent",
            openai_api_key="",
            openai_base_url="",
            resume_llm_model="gpt-4.1-mini",
            title_similarity_model="gpt-4.1-mini",
            embedding_model="text-embedding-3-large",
            assistant_model="gpt-4.1-mini",
        )

    def _snapshot(self) -> MarketSnapshot:
        return MarketSnapshot(
            generated_at="2026-04-06T10:00:00",
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=[
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example",
                    location="台北市",
                    url="https://example.com/jobs/1",
                )
            ],
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_hydrate_initial_snapshot_does_not_load_global_snapshot_file(self) -> None:
        settings = self.build_settings()
        save_snapshot(self._snapshot(), settings.snapshot_path)
        fake_streamlit = types.SimpleNamespace(
            session_state=_SessionState(snapshot=None),
        )

        with mock.patch.object(bootstrap_user_context, "st", fake_streamlit):
            bootstrap_user_context.hydrate_initial_snapshot(settings)

        self.assertIsNone(fake_streamlit.session_state.snapshot)


if __name__ == "__main__":
    unittest.main()
