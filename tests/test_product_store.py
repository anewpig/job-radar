"""Tests for product store behavior."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import (  # noqa: E402
    JobListing,
    MarketSnapshot,
    NotificationPreference,
    ResumeProfile,
    TargetRole,
)
from job_spy_tw.product_store import ProductStore  # noqa: E402
from job_spy_tw.store import ProductStoreDatabase  # noqa: E402


class ProductStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(tempfile.mkdtemp()) / "product_state.sqlite3"
        self.store = ProductStore(self.db_path)
        self.rows = [
            {
                "enabled": True,
                "priority": 1,
                "role": "AI工程師",
                "keywords": "LLM, RAG",
            }
        ]

    def _build_snapshot(self, *jobs: JobListing) -> MarketSnapshot:
        return MarketSnapshot(
            generated_at="2026-04-02T12:00:00",
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM", "RAG"])],
            jobs=list(jobs),
            skills=[],
            task_insights=[],
            errors=[],
        )

    def _register_user(self, email: str) -> object:
        return self.store.register_user(
            email=email,
            password="password123",
            display_name=email.split("@", 1)[0],
        )

    def test_save_search_and_detect_new_jobs(self) -> None:
        first_job = JobListing(
            source="104",
            title="AI工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI工程師",
        )
        search_id = self.store.save_search(
            name="AI追蹤",
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(first_job),
        )

        second_job = JobListing(
            source="1111",
            title="AI工程師",
            company="Another",
            location="新北市",
            url="https://example.com/jobs/2",
            matched_role="AI工程師",
        )
        result = self.store.sync_saved_search_results(
            search_id=search_id,
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(first_job, second_job),
        )

        self.assertFalse(result["baseline_created"])
        self.assertEqual(len(result["new_jobs"]), 1)
        self.assertEqual(result["new_jobs"][0]["url"], second_job.url)
        self.assertEqual(self.store.unread_notification_count(), 1)

    def test_saved_search_seen_jobs_are_normalized_out_of_legacy_json_column(self) -> None:
        first_job = JobListing(
            source="104",
            title="AI工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI工程師",
        )
        second_job = JobListing(
            source="1111",
            title="AI工程師",
            company="Another",
            location="新北市",
            url="https://example.com/jobs/2",
            matched_role="AI工程師",
        )

        search_id = self.store.save_search(
            name="正規化測試",
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(first_job, second_job),
        )
        saved_search = self.store.get_saved_search(search_id)

        self.assertIsNotNone(saved_search)
        assert saved_search is not None
        self.assertEqual(
            saved_search.known_job_urls,
            [first_job.url, second_job.url],
        )

        with sqlite3.connect(self.db_path) as connection:
            legacy_payload = connection.execute(
                "SELECT known_job_urls FROM saved_searches WHERE id = ?",
                (search_id,),
            ).fetchone()
            normalized_rows = connection.execute(
                """
                SELECT job_url
                FROM saved_search_seen_jobs
                WHERE search_id = ?
                ORDER BY ordinal ASC
                """,
                (search_id,),
            ).fetchall()

        self.assertEqual(str(legacy_payload[0]), "[]")
        self.assertEqual(
            [str(row[0]) for row in normalized_rows],
            [first_job.url, second_job.url],
        )

    def test_toggle_favorite_adds_and_removes_job(self) -> None:
        job = JobListing(
            source="104",
            title="資料工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/99",
            matched_role="軟體工程師",
        )
        self.assertTrue(self.store.toggle_favorite(job))
        self.assertTrue(self.store.is_favorite(job.url))
        self.assertEqual(len(self.store.list_favorites()), 1)

        self.assertFalse(self.store.toggle_favorite(job))
        self.assertFalse(self.store.is_favorite(job.url))
        self.assertEqual(len(self.store.list_favorites()), 0)

    def test_toggle_favorite_links_job_to_saved_search(self) -> None:
        job = JobListing(
            source="104",
            title="AI工程師",
            company="Example AI",
            location="台北市",
            url="https://example.com/jobs/55",
            matched_role="AI工程師",
        )
        search_id = self.store.save_search(
            name="AI追蹤",
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(job),
        )

        self.assertTrue(
            self.store.toggle_favorite(
                job,
                saved_search_id=search_id,
                saved_search_name="AI追蹤",
            )
        )
        favorites = self.store.list_favorites_for_search(search_id)
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0].saved_search_name, "AI追蹤")

    def test_update_favorite_and_delete_saved_search(self) -> None:
        job = JobListing(
            source="104",
            title="產品經理",
            company="Example PM",
            location="台北市",
            url="https://example.com/jobs/88",
            matched_role="PM",
        )
        self.store.toggle_favorite(job)
        self.store.update_favorite(
            job_url=job.url,
            application_status="已投遞",
            notes="已依職缺調整履歷",
        )
        favorite = self.store.list_favorites()[0]
        self.assertEqual(favorite.application_status, "已投遞")
        self.assertIn("調整履歷", favorite.notes)

        search_id = self.store.save_search(
            name="PM追蹤",
            rows=self.rows,
            custom_queries_text="PM",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(job),
        )
        self.store.delete_saved_search(search_id)
        self.assertIsNone(self.store.get_saved_search(search_id))

    def test_delete_favorite_removes_job_from_board(self) -> None:
        job = JobListing(
            source="104",
            title="藥師",
            company="Example Pharmacy",
            location="台北市",
            url="https://example.com/jobs/pharmacist",
            matched_role="藥師",
        )
        self.store.toggle_favorite(job)
        self.assertEqual(len(self.store.list_favorites()), 1)

        self.store.delete_favorite(job.url)

        self.assertEqual(len(self.store.list_favorites()), 0)
        self.assertFalse(self.store.is_favorite(job.url))

    def test_notification_preferences_and_filtered_new_jobs(self) -> None:
        job1 = JobListing(
            source="104",
            title="AI工程師",
            company="A",
            location="台北市",
            url="https://example.com/jobs/a",
            matched_role="AI工程師",
            relevance_score=25,
        )
        job2 = JobListing(
            source="104",
            title="AI工程師",
            company="B",
            location="台北市",
            url="https://example.com/jobs/b",
            matched_role="AI工程師",
            relevance_score=42,
        )
        search_id = self.store.save_search(
            name="AI通知",
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(job1),
        )
        self.store.save_notification_preferences(
            NotificationPreference(
                site_enabled=True,
                email_enabled=True,
                line_enabled=False,
                email_recipients="me@example.com",
                line_target="",
                min_relevance_score=30,
                max_jobs_per_alert=3,
                frequency="即時",
            )
        )
        preferences = self.store.get_notification_preferences()
        self.assertTrue(preferences.email_enabled)
        self.assertEqual(preferences.email_recipients, "me@example.com")
        self.assertEqual(preferences.min_relevance_score, 30)

        result = self.store.sync_saved_search_results(
            search_id=search_id,
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(job1, job2),
            min_relevance_score=preferences.min_relevance_score,
            max_jobs=preferences.max_jobs_per_alert,
            create_notification=preferences.site_enabled,
        )
        self.assertEqual(len(result["new_jobs"]), 1)
        self.assertEqual(result["new_jobs"][0]["url"], job2.url)

    def test_issue_and_consume_line_bind_code(self) -> None:
        preferences = self.store.issue_line_bind_code(ttl_minutes=15)
        self.assertTrue(preferences.line_bind_code.startswith("LINE-"))
        self.assertTrue(preferences.line_bind_expires_at)

        result = self.store.consume_line_bind_code(
            preferences.line_bind_code,
            "U1234567890",
        )

        self.assertTrue(result["ok"])
        refreshed = self.store.get_notification_preferences()
        self.assertEqual(refreshed.line_target, "U1234567890")
        self.assertEqual(refreshed.line_bind_code, "")
        self.assertTrue(refreshed.line_bound_at)

    def test_register_and_authenticate_user(self) -> None:
        created = self._register_user("member@example.com")

        authenticated = self.store.authenticate_user("member@example.com", "password123")

        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.id, created.id)
        self.assertEqual(authenticated.email, "member@example.com")
        self.assertIsNone(self.store.authenticate_user("member@example.com", "wrong-password"))

    def test_user_scoped_saved_searches_and_favorites(self) -> None:
        alice = self._register_user("alice@example.com")
        bob = self._register_user("bob@example.com")
        job = JobListing(
            source="104",
            title="AI 應用工程師",
            company="Example AI",
            location="台北市",
            url="https://example.com/jobs/scoped",
            matched_role="AI應用工程師",
        )

        alice_search_id = self.store.save_search(
            user_id=alice.id,
            name="我的 AI 追蹤",
            rows=self.rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._build_snapshot(job),
        )
        self.store.save_search(
            user_id=bob.id,
            name="我的 AI 追蹤",
            rows=self.rows,
            custom_queries_text="遠端",
            crawl_preset_label="平衡",
            snapshot=self._build_snapshot(job),
        )
        self.store.toggle_favorite(
            job,
            user_id=alice.id,
            saved_search_id=alice_search_id,
            saved_search_name="我的 AI 追蹤",
        )

        self.assertEqual(len(self.store.list_saved_searches(user_id=alice.id)), 1)
        self.assertEqual(len(self.store.list_saved_searches(user_id=bob.id)), 1)
        self.assertEqual(len(self.store.list_favorites(user_id=alice.id)), 1)
        self.assertEqual(len(self.store.list_favorites(user_id=bob.id)), 0)

    def test_user_scoped_notification_preferences_and_resume_profile(self) -> None:
        alice = self._register_user("notify@example.com")
        bob = self._register_user("resume@example.com")
        self.store.save_notification_preferences(
            NotificationPreference(
                site_enabled=True,
                email_enabled=True,
                line_enabled=False,
                email_recipients="notify@example.com",
                line_target="",
                min_relevance_score=55,
                max_jobs_per_alert=5,
                frequency="即時",
            ),
            user_id=alice.id,
        )
        profile = ResumeProfile(
            source_name="alice_resume.pdf",
            summary="熟悉 Python 與 LLM 應用。",
            target_roles=["AI應用工程師"],
            core_skills=["Python", "LLM"],
        )
        self.store.save_resume_profile(user_id=alice.id, profile=profile)

        alice_preferences = self.store.get_notification_preferences(user_id=alice.id)
        bob_preferences = self.store.get_notification_preferences(user_id=bob.id)
        stored_profile = self.store.get_resume_profile(user_id=alice.id)
        missing_profile = self.store.get_resume_profile(user_id=bob.id)

        self.assertTrue(alice_preferences.email_enabled)
        self.assertEqual(alice_preferences.email_recipients, "notify@example.com")
        self.assertFalse(bob_preferences.email_enabled)
        self.assertIsNotNone(stored_profile)
        self.assertEqual(stored_profile.profile.summary, "熟悉 Python 與 LLM 應用。")
        self.assertIsNone(missing_profile)

    def test_authenticate_oidc_user_creates_and_reuses_identity(self) -> None:
        first = self.store.authenticate_oidc_user(
            provider="https://accounts.google.com",
            subject="google-sub-123",
            email="oidc@example.com",
            display_name="OIDC Member",
            email_verified=True,
        )
        second = self.store.authenticate_oidc_user(
            provider="https://accounts.google.com",
            subject="google-sub-123",
            email="oidc@example.com",
            display_name="OIDC Member Updated",
            email_verified=True,
        )

        self.assertEqual(first.id, second.id)
        refreshed = self.store.get_user(first.id)
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed.display_name, "OIDC Member Updated")

    def test_authenticate_oidc_user_rejects_implicit_link_for_existing_email(self) -> None:
        created = self._register_user("linked@example.com")

        with self.assertRaises(ValueError):
            self.store.authenticate_oidc_user(
                provider="https://accounts.google.com",
                subject="google-sub-999",
                email="linked@example.com",
                display_name="Linked OIDC",
                email_verified=True,
            )

        refreshed = self.store.get_user(created.id)
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed.display_name, "linked")

    def test_authenticate_oidc_user_links_existing_email_account_explicitly(self) -> None:
        created = self._register_user("linked@example.com")

        linked = self.store.authenticate_oidc_user(
            provider="https://accounts.google.com",
            subject="google-sub-999",
            email="linked@example.com",
            display_name="Linked OIDC",
            email_verified=True,
            link_user_id=created.id,
        )

        self.assertEqual(created.id, linked.id)
        refreshed = self.store.get_user(created.id)
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed.display_name, "Linked OIDC")

    def test_authenticate_oidc_user_requires_verified_email(self) -> None:
        with self.assertRaises(ValueError):
            self.store.authenticate_oidc_user(
                provider="https://accounts.google.com",
                subject="google-sub-unverified",
                email="oidc@example.com",
                display_name="OIDC Member",
                email_verified=False,
            )

    def test_update_favorite_persists_application_and_interview_fields(self) -> None:
        alice = self._register_user("timeline@example.com")
        job = JobListing(
            source="104",
            title="產品經理",
            company="Timeline Inc.",
            location="台北市",
            url="https://example.com/jobs/timeline",
            matched_role="PM",
        )

        self.store.toggle_favorite(job, user_id=alice.id)
        self.store.update_favorite(
            user_id=alice.id,
            job_url=job.url,
            application_status="已面試",
            notes="已完成第一輪。",
            application_date="2026-04-02",
            interview_date="2026-04-10",
            interview_notes="主管面談，需準備作品集。",
        )

        favorite = self.store.list_favorites(user_id=alice.id)[0]
        self.assertEqual(favorite.application_date, "2026-04-02")
        self.assertEqual(favorite.interview_date, "2026-04-10")
        self.assertEqual(favorite.interview_notes, "主管面談，需準備作品集。")

    def test_issue_and_consume_line_bind_code_for_registered_user(self) -> None:
        user = self._register_user("linebind@example.com")
        preferences = self.store.issue_line_bind_code(user_id=user.id, ttl_minutes=15)

        result = self.store.consume_line_bind_code(
            preferences.line_bind_code,
            "U9999999999",
        )

        self.assertTrue(result["ok"])
        refreshed = self.store.get_notification_preferences(user_id=user.id)
        guest_preferences = self.store.get_notification_preferences()
        self.assertEqual(refreshed.line_target, "U9999999999")
        self.assertEqual(guest_preferences.line_target, "")

    def test_record_visit_increments_total_visits(self) -> None:
        before = self.store.get_total_visits()

        after_first = self.store.record_visit()
        after_second = self.store.record_visit()

        self.assertEqual(after_first, before + 1)
        self.assertEqual(after_second, before + 2)
        self.assertEqual(self.store.get_total_visits(), before + 2)

    def test_record_ai_monitoring_event_persists_low_sensitivity_fields(self) -> None:
        event_id = self.store.record_ai_monitoring_event(
            event_type="assistant.answer_question",
            status="success",
            latency_ms=1234.5,
            model_name="gpt-5.4-mini",
            query_signature="sig-monitoring",
            metadata={
                "question_length": 18,
                "snapshot_jobs": 42,
                "used_chunks": 6,
            },
        )

        recent_events = self.store.list_recent_ai_monitoring_events(limit=5)
        recent_summary = self.store.summarize_recent_ai_monitoring(limit=5)

        self.assertGreater(event_id, 0)
        self.assertEqual(len(recent_events), 1)
        self.assertEqual(recent_events[0]["event_type"], "assistant.answer_question")
        self.assertEqual(recent_events[0]["status"], "success")
        self.assertEqual(recent_events[0]["model_name"], "gpt-5.4-mini")
        self.assertEqual(recent_events[0]["query_signature"], "sig-monitoring")
        self.assertEqual(recent_events[0]["metadata"]["question_length"], 18)
        self.assertIn("assistant.answer_question", recent_summary)
        self.assertEqual(recent_summary["assistant.answer_question"]["count"], 1)
        self.assertEqual(recent_summary["assistant.answer_question"]["error_count"], 0)

    def test_evaluate_ai_latency_budgets_flags_warn_and_fail(self) -> None:
        for latency_ms in (4100.0, 4300.0, 4700.0):
            self.store.record_ai_monitoring_event(
                event_type="assistant.answer_question",
                status="success",
                latency_ms=latency_ms,
                model_name="gpt-5.4-mini",
                metadata={"usage_total_tokens": 2200},
            )
        for latency_ms in (2800.0, 3200.0, 3400.0):
            self.store.record_ai_monitoring_event(
                event_type="resume.match_jobs",
                status="success",
                latency_ms=latency_ms,
                model_name="gpt-5.4-mini",
                metadata={"usage_total_tokens": 5200},
            )
        for status in ("error", "error", "success"):
            self.store.record_ai_monitoring_event(
                event_type="assistant.generate_report",
                status=status,
                latency_ms=2500.0,
                model_name="gpt-5.4-mini",
                metadata={"usage_total_tokens": 3000},
            )

        budgets = self.store.evaluate_ai_latency_budgets(limit=20)

        self.assertEqual(budgets["status"], "FAIL")
        self.assertEqual(
            budgets["event_budgets"]["assistant.answer_question"]["status"],
            "PASS",
        )
        self.assertEqual(
            budgets["event_budgets"]["resume.match_jobs"]["status"],
            "PASS",
        )
        self.assertEqual(
            budgets["event_budgets"]["assistant.generate_report"]["status"],
            "FAIL",
        )
        self.assertEqual(budgets["cost_tracking"]["status"], "PASS")

    def test_evaluate_ai_latency_budgets_flags_token_budget_warn(self) -> None:
        for _ in range(3):
            self.store.record_ai_monitoring_event(
                event_type="assistant.answer_question",
                status="success",
                latency_ms=3200.0,
                model_name="gpt-5.4-mini",
                metadata={"usage_total_tokens": 6200},
            )

        budgets = self.store.evaluate_ai_latency_budgets(limit=10)

        self.assertEqual(budgets["status"], "PASS")
        self.assertEqual(budgets["cost_tracking"]["status"], "WARN")
        self.assertEqual(
            budgets["cost_tracking"]["event_budgets"]["assistant.answer_question"]["status"],
            "WARN",
        )

    def test_summarize_assistant_modes_groups_by_answer_mode(self) -> None:
        self.store.record_ai_monitoring_event(
            event_type="assistant.answer_question",
            status="success",
            latency_ms=2100.0,
            model_name="gpt-5.4-mini",
            metadata={
                "answer_mode": "market_summary",
                "usage_total_tokens": 1800,
            },
        )
        self.store.record_ai_monitoring_event(
            event_type="assistant.answer_question",
            status="error",
            latency_ms=3100.0,
            model_name="gpt-5.4-mini",
            metadata={
                "answer_mode": "job_comparison",
                "usage_total_tokens": 2600,
            },
        )
        self.store.record_ai_monitoring_event(
            event_type="assistant.generate_report",
            status="success",
            latency_ms=4100.0,
            model_name="gpt-5.4-mini",
            metadata={
                "answer_mode": "market_summary",
                "usage_total_tokens": 3200,
            },
        )

        mode_summary = self.store.summarize_assistant_modes(limit=10)

        self.assertIn("assistant.answer_question", mode_summary)
        self.assertIn("market_summary", mode_summary["assistant.answer_question"])
        self.assertIn("job_comparison", mode_summary["assistant.answer_question"])
        self.assertEqual(
            mode_summary["assistant.answer_question"]["market_summary"]["count"],
            1,
        )
        self.assertEqual(
            mode_summary["assistant.answer_question"]["job_comparison"]["error_count"],
            1,
        )
        self.assertEqual(
            mode_summary["assistant.generate_report"]["market_summary"]["avg_total_tokens"],
            3200.0,
        )

    def test_upsert_and_list_agent_memories(self) -> None:
        user = self._register_user("memory@example.com")

        memory_id = self.store.upsert_agent_memory(
            user_id=user.id,
            memory_type="profile_fact",
            key="assistant_profile",
            value={
                "target_roles": ["前端工程師"],
                "skills": ["React", "TypeScript"],
            },
            summary="目標職缺：前端工程師；目前技能：React、TypeScript",
            source="assistant_agent_profile",
        )
        fetched = self.store.get_agent_memory(
            user_id=user.id,
            memory_type="profile_fact",
            key="assistant_profile",
        )
        listed = self.store.list_agent_memories(
            user_id=user.id,
            memory_type="profile_fact",
            limit=5,
        )

        self.assertGreater(memory_id, 0)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.value["target_roles"], ["前端工程師"])
        self.assertEqual(fetched.value["skills"], ["React", "TypeScript"])
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].key, "assistant_profile")

    def test_issue_password_reset_and_reset_password_with_code(self) -> None:
        user = self._register_user("reset@example.com")

        issued_user, reset_code = self.store.issue_password_reset("reset@example.com")
        with sqlite3.connect(self.db_path) as connection:
            stored_reset_code = connection.execute(
                """
                SELECT reset_code
                FROM password_reset_tokens
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user.id),),
            ).fetchone()
        updated_user = self.store.reset_password_with_code(
            email="reset@example.com",
            reset_code=reset_code,
            new_password="new-password-123",
        )
        authenticated = self.store.authenticate_user("reset@example.com", "new-password-123")

        self.assertEqual(issued_user.id, user.id)
        self.assertIsNotNone(stored_reset_code)
        assert stored_reset_code is not None
        self.assertNotEqual(str(stored_reset_code[0]), reset_code)
        self.assertTrue(str(stored_reset_code[0]).startswith("pbkdf2-sha256$"))
        self.assertEqual(updated_user.id, user.id)
        self.assertIsNotNone(authenticated)
        self.assertIsNone(self.store.authenticate_user("reset@example.com", "password123"))

    def test_password_reset_code_cannot_be_reused(self) -> None:
        self._register_user("reuse@example.com")
        _issued_user, reset_code = self.store.issue_password_reset("reuse@example.com")
        self.store.reset_password_with_code(
            email="reuse@example.com",
            reset_code=reset_code,
            new_password="new-password-123",
        )

        with self.assertRaises(ValueError):
            self.store.reset_password_with_code(
                email="reuse@example.com",
                reset_code=reset_code,
                new_password="another-password-123",
            )

    def test_product_state_database_initializes_secondary_indexes(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            index_names = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                ).fetchall()
            }

        self.assertIn("idx_saved_searches_user_signature", index_names)
        self.assertIn("idx_saved_searches_user_updated_at", index_names)
        self.assertIn("idx_saved_search_seen_jobs_search_ordinal", index_names)
        self.assertIn("idx_favorite_jobs_user_saved_search", index_names)
        self.assertIn("idx_favorite_jobs_user_application_status", index_names)
        self.assertIn("idx_job_notifications_user_read_created", index_names)
        self.assertIn("idx_user_identities_user_provider", index_names)
        self.assertIn("idx_user_identities_email", index_names)
        self.assertIn("idx_ai_monitoring_events_type_created", index_names)
        self.assertIn("idx_ai_monitoring_events_user_created", index_names)
        self.assertIn("idx_ai_monitoring_events_status_created", index_names)
        self.assertIn("idx_agent_memories_user_type_updated", index_names)
        self.assertIn("idx_agent_memories_user_key", index_names)

    def test_product_state_database_backfills_seen_jobs_from_legacy_json(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "legacy_product_state.sqlite3"
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE saved_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    name TEXT NOT NULL,
                    rows_json TEXT NOT NULL DEFAULT '[]',
                    custom_queries_text TEXT NOT NULL DEFAULT '',
                    crawl_preset_label TEXT NOT NULL DEFAULT '快速',
                    signature TEXT NOT NULL DEFAULT '',
                    known_job_urls TEXT NOT NULL DEFAULT '[]',
                    last_run_at TEXT NOT NULL DEFAULT '',
                    last_job_count INTEGER NOT NULL DEFAULT 0,
                    last_new_job_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, name)
                )
                """
            )
            connection.execute(
                """
                INSERT INTO saved_searches (
                    user_id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    "Legacy search",
                    "[]",
                    "",
                    "快速",
                    "sig-legacy",
                    '["https://example.com/jobs/legacy-1","https://example.com/jobs/legacy-2"]',
                    "2026-04-02T12:00:00",
                    2,
                    0,
                    "2026-04-02T12:00:00",
                    "2026-04-02T12:00:00",
                ),
            )
            connection.commit()

        ProductStoreDatabase(db_path).initialize()
        store = ProductStore(db_path)
        saved_search = store.get_saved_search(1)

        self.assertIsNotNone(saved_search)
        assert saved_search is not None
        self.assertEqual(
            saved_search.known_job_urls,
            [
                "https://example.com/jobs/legacy-1",
                "https://example.com/jobs/legacy-2",
            ],
        )

        with sqlite3.connect(db_path) as connection:
            legacy_payload = connection.execute(
                "SELECT known_job_urls FROM saved_searches WHERE id = 1"
            ).fetchone()
            seen_count = connection.execute(
                "SELECT COUNT(*) FROM saved_search_seen_jobs WHERE search_id = 1"
            ).fetchone()

        self.assertEqual(str(legacy_payload[0]), "[]")
        self.assertEqual(int(seen_count[0]), 2)


if __name__ == "__main__":
    unittest.main()
