from __future__ import annotations

"""Backward-compatible public facade for product state storage."""

from pathlib import Path
from typing import Any

from .models import JobListing, MarketSnapshot, NotificationPreference, ResumeProfile
from .store import (
    AppMetricsRepository,
    FavoriteRepository,
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
        self.saved_searches = SavedSearchRepository(db_path)
        self.favorites = FavoriteRepository(db_path)
        self.notifications = NotificationRepository(db_path)
        self.user_profiles = UserProfileRepository(db_path)
        self.guest_user_id = GUEST_USER_ID

    def get_guest_user(self):
        return self.users.get_guest_user()

    def get_user(self, user_id: int):
        return self.users.get_user(user_id)

    def get_user_by_email(self, email: str):
        return self.users.get_user_by_email(email)

    def register_user(self, *, email: str, password: str, display_name: str = ""):
        return self.users.register_user(
            email=email,
            password=password,
            display_name=display_name,
        )

    def authenticate_user(self, email: str, password: str):
        return self.users.authenticate_user(email, password)

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
