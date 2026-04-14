"""Compatibility wrapper exposing persisted product state operations."""

from __future__ import annotations

"""Backward-compatible public facade for product state storage."""

from pathlib import Path
from typing import Any

from .models import JobListing, MarketSnapshot, NotificationPreference, ResumeProfile
from .store import (
    AIMonitoringRepository,
    AgentMemoryRepository,
    AuditLogRepository,
    AppMetricsRepository,
    FavoriteRepository,
    FeedbackRepository,
    GUEST_USER_ID,
    NotificationRepository,
    ProductStoreDatabase,
    SavedSearchRepository,
    UserProfileRepository,
    UserRepository,
)


class ProductStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        ProductStoreDatabase(db_path).initialize()
        self.users = UserRepository(db_path)
        self.metrics = AppMetricsRepository(db_path)
        self.ai_monitoring = AIMonitoringRepository(db_path)
        self.audit_logs = AuditLogRepository(db_path)
        self.agent_memories = AgentMemoryRepository(db_path)
        self.saved_searches = SavedSearchRepository(db_path)
        self.favorites = FavoriteRepository(db_path)
        self.notifications = NotificationRepository(db_path)
        self.user_profiles = UserProfileRepository(db_path)
        self.feedback = FeedbackRepository(db_path)
        self.guest_user_id = GUEST_USER_ID

    def get_guest_user(self):
        return self.users.get_guest_user()

    def get_user(self, user_id: int):
        return self.users.get_user(user_id)

    def get_user_by_email(self, email: str):
        return self.users.get_user_by_email(email)

    def list_users(self, *, include_guest: bool = False):
        return self.users.list_users(include_guest=include_guest)

    def set_user_role(self, *, user_id: int, role: str):
        return self.users.set_user_role(user_id=user_id, role=role)

    def register_user(self, *, email: str, password: str, display_name: str = ""):
        return self.users.register_user(
            email=email,
            password=password,
            display_name=display_name,
        )

    def ensure_system_user(self, *, email: str, display_name: str, role: str):
        return self.users.ensure_system_user(
            email=email,
            display_name=display_name,
            role=role,
        )

    def authenticate_user(self, email: str, password: str):
        return self.users.authenticate_user(email, password)

    def authenticate_oidc_user(
        self,
        *,
        provider: str,
        subject: str,
        email: str,
        display_name: str = "",
        email_verified: bool = False,
        link_user_id: int | None = None,
    ):
        return self.users.authenticate_oidc_user(
            provider=provider,
            subject=subject,
            email=email,
            display_name=display_name,
            email_verified=email_verified,
            link_user_id=link_user_id,
        )

    def issue_password_reset(self, email: str, *, ttl_minutes: int = 15):
        return self.users.issue_password_reset(email, ttl_minutes=ttl_minutes)

    def reset_password_with_code(self, *, email: str, reset_code: str, new_password: str):
        return self.users.reset_password_with_code(
            email=email,
            reset_code=reset_code,
            new_password=new_password,
        )

    def get_resume_profile(self, *, user_id: int):
        return self.user_profiles.get_resume_profile(user_id=user_id)

    def save_resume_profile(self, *, user_id: int, profile: ResumeProfile) -> None:
        self.user_profiles.save_resume_profile(user_id=user_id, profile=profile)

    def clear_resume_profile(self, *, user_id: int) -> None:
        self.user_profiles.clear_resume_profile(user_id=user_id)

    def get_total_visits(self) -> int:
        return self.metrics.get_total_visits()

    def record_visit(self) -> int:
        return self.metrics.record_visit()

    def record_ai_monitoring_event(
        self,
        *,
        event_type: str,
        status: str = "success",
        latency_ms: float = 0.0,
        model_name: str = "",
        query_signature: str = "",
        metadata: dict[str, Any] | None = None,
        user_id: int = GUEST_USER_ID,
    ) -> int:
        return self.ai_monitoring.record_event(
            event_type=event_type,
            status=status,
            latency_ms=latency_ms,
            model_name=model_name,
            query_signature=query_signature,
            metadata=metadata,
            user_id=user_id,
        )

    def list_recent_ai_monitoring_events(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.ai_monitoring.list_recent_events(user_id=user_id, limit=limit)

    def summarize_recent_ai_monitoring(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 200,
    ) -> dict[str, dict[str, float | int]]:
        return self.ai_monitoring.summarize_recent(user_id=user_id, limit=limit)

    def evaluate_ai_latency_budgets(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, Any]:
        return self.ai_monitoring.evaluate_latency_budgets(
            user_id=user_id,
            limit=limit,
        )

    def summarize_assistant_modes(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, dict[str, Any]]:
        return self.ai_monitoring.summarize_assistant_modes(
            user_id=user_id,
            limit=limit,
        )

    def summarize_ai_cache_efficiency(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, Any]:
        return self.ai_monitoring.summarize_cache_efficiency(
            user_id=user_id,
            limit=limit,
        )

    def record_audit_event(
        self,
        *,
        event_type: str,
        status: str = "success",
        target_type: str = "",
        target_id: str = "",
        details: dict[str, Any] | None = None,
        user_id: int = GUEST_USER_ID,
        actor_role: str = "guest",
        trace_id: str = "",
    ) -> int:
        return self.audit_logs.record_event(
            event_type=event_type,
            status=status,
            target_type=target_type,
            target_id=target_id,
            details=details,
            user_id=user_id,
            actor_role=actor_role,
            trace_id=trace_id,
        )

    def record_feedback_event(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        target_type: str,
        target_id: str,
        rating: int,
        tags: list[str] | None = None,
        comment: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        return self.feedback.record_feedback(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            tags=tags,
            comment=comment,
            metadata=metadata,
        )

    def list_recent_feedback_events(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.feedback.list_recent_feedback(user_id=user_id, limit=limit)

    def list_recent_audit_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.audit_logs.list_recent_events(limit=limit)

    def upsert_agent_memory(
        self,
        *,
        memory_type: str,
        key: str,
        value: dict[str, Any] | None = None,
        summary: str = "",
        source: str = "",
        confidence: float = 1.0,
        expires_at: str = "",
        is_active: bool = True,
        user_id: int = GUEST_USER_ID,
    ) -> int:
        return self.agent_memories.upsert_memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            value=value,
            summary=summary,
            source=source,
            confidence=confidence,
            expires_at=expires_at,
            is_active=is_active,
        )

    def get_agent_memory(
        self,
        *,
        memory_type: str,
        key: str,
        user_id: int = GUEST_USER_ID,
        active_only: bool = True,
    ):
        return self.agent_memories.get_memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            active_only=active_only,
        )

    def list_agent_memories(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        memory_type: str = "",
        limit: int = 20,
        active_only: bool = True,
    ):
        return self.agent_memories.list_memories(
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
            active_only=active_only,
        )

    def touch_agent_memory(
        self,
        *,
        memory_type: str,
        key: str,
        user_id: int = GUEST_USER_ID,
    ) -> None:
        self.agent_memories.touch_memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
        )

    def build_signature(
        self,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
    ) -> str:
        return self.saved_searches.build_signature(
            rows, custom_queries_text, crawl_preset_label
        )

    def save_search(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        name: str,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        snapshot: MarketSnapshot | None = None,
        search_id: int | None = None,
    ) -> int:
        return self.saved_searches.save_search(
            user_id=user_id,
            name=name,
            rows=rows,
            custom_queries_text=custom_queries_text,
            crawl_preset_label=crawl_preset_label,
            snapshot=snapshot,
            search_id=search_id,
        )

    def list_saved_searches(self, *, user_id: int = GUEST_USER_ID):
        return self.saved_searches.list_saved_searches(user_id=user_id)

    def list_saved_search_subscribers(self, *, signature: str):
        return self.saved_searches.list_saved_search_subscribers(signature=signature)

    def get_saved_search(self, search_id: int, *, user_id: int = GUEST_USER_ID):
        return self.saved_searches.get_saved_search(search_id, user_id=user_id)

    def find_saved_search_by_signature(
        self,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        *,
        user_id: int = GUEST_USER_ID,
    ):
        return self.saved_searches.find_saved_search_by_signature(
            rows,
            custom_queries_text,
            crawl_preset_label,
            user_id=user_id,
        )

    def sync_saved_search_results(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        search_id: int,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        snapshot: MarketSnapshot,
        min_relevance_score: float = 0.0,
        max_jobs: int = 20,
        create_notification: bool = True,
    ) -> dict[str, Any]:
        return self.saved_searches.sync_saved_search_results(
            user_id=user_id,
            search_id=search_id,
            rows=rows,
            custom_queries_text=custom_queries_text,
            crawl_preset_label=crawl_preset_label,
            snapshot=snapshot,
            min_relevance_score=min_relevance_score,
            max_jobs=max_jobs,
            create_notification=create_notification,
        )

    def delete_saved_search(self, search_id: int, *, user_id: int = GUEST_USER_ID) -> None:
        self.saved_searches.delete_saved_search(search_id, user_id=user_id)

    def get_notification_preferences(self, *, user_id: int = GUEST_USER_ID):
        return self.notifications.get_notification_preferences(user_id=user_id)

    def save_notification_preferences(
        self,
        preferences: NotificationPreference,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> None:
        self.notifications.save_notification_preferences(preferences, user_id=user_id)

    def issue_line_bind_code(
        self, *, user_id: int = GUEST_USER_ID, ttl_minutes: int = 15
    ):
        return self.notifications.issue_line_bind_code(
            user_id=user_id,
            ttl_minutes=ttl_minutes,
        )

    def consume_line_bind_code(
        self,
        bind_code: str,
        user_id_text: str,
        *,
        user_id: int | None = None,
    ) -> dict[str, str | bool]:
        return self.notifications.consume_line_bind_code(
            bind_code,
            user_id_text,
            user_id=user_id,
        )

    def clear_line_target(self, *, user_id: int = GUEST_USER_ID) -> None:
        self.notifications.clear_line_target(user_id=user_id)

    def update_notification_delivery(
        self,
        notification_id: int,
        *,
        user_id: int = GUEST_USER_ID,
        email_sent: bool,
        line_sent: bool,
        delivery_notes: list[str],
    ) -> None:
        self.notifications.update_notification_delivery(
            notification_id,
            user_id=user_id,
            email_sent=email_sent,
            line_sent=line_sent,
            delivery_notes=delivery_notes,
        )

    def list_notifications(self, limit: int = 20, *, user_id: int = GUEST_USER_ID):
        return self.notifications.list_notifications(limit=limit, user_id=user_id)

    def unread_notification_count(self, *, user_id: int = GUEST_USER_ID) -> int:
        return self.notifications.unread_notification_count(user_id=user_id)

    def mark_all_notifications_read(self, *, user_id: int = GUEST_USER_ID) -> None:
        self.notifications.mark_all_notifications_read(user_id=user_id)

    def toggle_favorite(
        self,
        job: JobListing,
        *,
        user_id: int = GUEST_USER_ID,
        saved_search_id: int | None = None,
        saved_search_name: str = "",
    ) -> bool:
        return self.favorites.toggle_favorite(
            job,
            user_id=user_id,
            saved_search_id=saved_search_id,
            saved_search_name=saved_search_name,
        )

    def is_favorite(self, job_url: str, *, user_id: int = GUEST_USER_ID) -> bool:
        return self.favorites.is_favorite(job_url, user_id=user_id)

    def list_favorites(self, *, user_id: int = GUEST_USER_ID):
        return self.favorites.list_favorites(user_id=user_id)

    def list_favorites_for_search(
        self, search_id: int, *, user_id: int = GUEST_USER_ID
    ):
        return self.favorites.list_favorites_for_search(search_id, user_id=user_id)

    def update_favorite(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        job_url: str,
        application_status: str,
        notes: str,
        application_date: str = "",
        interview_date: str = "",
        interview_notes: str = "",
    ) -> None:
        self.favorites.update_favorite(
            user_id=user_id,
            job_url=job_url,
            application_status=application_status,
            notes=notes,
            application_date=application_date,
            interview_date=interview_date,
            interview_notes=interview_notes,
        )

    def delete_favorite(self, job_url: str, *, user_id: int = GUEST_USER_ID) -> None:
        self.favorites.delete_favorite(job_url, user_id=user_id)
