"""Settings helpers for models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    data_dir: Path
    request_timeout: float
    request_delay: float
    max_concurrent_requests: int
    max_pages_per_source: int
    max_detail_jobs_per_source: int
    min_relevance_score: float
    location: str
    enable_cake: bool
    enable_linkedin: bool
    allow_insecure_ssl_fallback: bool
    user_agent: str
    openai_api_key: str
    openai_base_url: str
    resume_llm_model: str
    title_similarity_model: str
    embedding_model: str
    assistant_model: str
    snapshot_ttl_seconds: int = 1800
    search_cache_ttl_seconds: int = 1800
    detail_cache_ttl_seconds: int = 43200
    cache_max_bytes: int = 256_000_000
    cache_max_files: int = 4_000
    cache_backend: str = "filesystem"
    queue_backend: str = "sqlite"
    database_backend: str = "sqlite"
    crawl_execution_mode: str = "inline"
    crawl_job_lease_seconds: int = 180
    show_backend_console: bool = True
    runtime_job_max_retries: int = 1
    runtime_job_retry_backoff_seconds: int = 90
    runtime_cleanup_interval_seconds: int = 21600
    runtime_job_retention_days: int = 14
    runtime_snapshot_retention_days: int = 30
    runtime_partial_snapshot_retention_hours: int = 12
    runtime_signal_retention_days: int = 14
    market_history_retention_days: int = 90
    market_history_max_runs_per_query: int = 100
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    notification_email_to: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    line_channel_access_token: str = ""
    line_channel_secret: str = ""
    line_to: str = ""
    public_base_url: str = ""
    line_webhook_host: str = "0.0.0.0"
    line_webhook_port: int = 8787
    global_search_enabled: bool = True
    global_search_name: str = ""
    global_search_keywords: list[str] = field(default_factory=list)
    global_search_frequency_days: int = 2
    global_search_preset_label: str = "平衡"
    global_search_force_refresh: bool = True
    global_search_user_email: str = ""
    linkedin_cooldown_seconds: int = 1800
    assistant_general_chat_model: str = ""
    assistant_prompt_variant: str = "control"
    assistant_latency_profile: str = "fast"
    assistant_ann_sync_interval_seconds: int = 900
    assistant_persistent_index_enabled: bool = False
    assistant_persistent_index_sources: tuple[str, ...] = ("snapshot_file",)
    assistant_persistent_index_max_snapshots: int = 1
    assistant_persistent_index_max_history_rows: int = 500
    assistant_external_search_enabled: bool = False
    assistant_external_search_provider: str = "duckduckgo"
    assistant_external_search_max_results: int = 3
    assistant_external_search_timeout_seconds: float = 4.0
    assistant_external_search_cache_ttl_seconds: int = 900
    salary_prediction_enabled: bool = True
    salary_prediction_model_path: Path | None = None
    backend_console_allowed_roles: tuple[str, ...] = ("operator", "admin")
    log_format: str = "text"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def snapshot_path(self) -> Path:
        return self.data_dir / "jobs_latest.json"

    @property
    def snapshot_store_dir(self) -> Path:
        return self.data_dir / "snapshots"

    @property
    def user_data_db_path(self) -> Path:
        return self.data_dir / "user_submissions.sqlite3"

    @property
    def product_state_db_path(self) -> Path:
        return self.data_dir / "product_state.sqlite3"

    @property
    def query_state_db_path(self) -> Path:
        return self.data_dir / "query_runtime.sqlite3"

    @property
    def market_history_db_path(self) -> Path:
        return self.data_dir / "market_history.sqlite3"
