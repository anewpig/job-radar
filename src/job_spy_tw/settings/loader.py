"""Settings helpers for loader."""

from __future__ import annotations

import os
from pathlib import Path

from .env import env_bool, load_dotenv
from .models import Settings


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def load_settings(base_dir: str | Path | None = None) -> Settings:
    root = Path(base_dir or Path.cwd())
    load_dotenv(root / ".env", override=True)
    data_dir = root / os.getenv("JOB_SPY_DATA_DIR", "data")
    default_llm_model = os.getenv("JOB_SPY_LLM_MODEL", "gpt-4.1-mini").strip()

    return Settings(
        data_dir=data_dir,
        request_timeout=float(os.getenv("JOB_SPY_REQUEST_TIMEOUT", "20")),
        request_delay=float(os.getenv("JOB_SPY_REQUEST_DELAY", "1.0")),
        max_concurrent_requests=int(os.getenv("JOB_SPY_MAX_CONCURRENT_REQUESTS", "4")),
        max_pages_per_source=int(os.getenv("JOB_SPY_MAX_PAGES_PER_SOURCE", "1")),
        max_detail_jobs_per_source=int(
            os.getenv("JOB_SPY_MAX_DETAIL_JOBS_PER_SOURCE", "0")
        ),
        min_relevance_score=float(os.getenv("JOB_SPY_MIN_RELEVANCE_SCORE", "18")),
        location=os.getenv("JOB_SPY_LOCATION", "台灣"),
        enable_cake=env_bool("JOB_SPY_ENABLE_CAKE", True),
        enable_linkedin=env_bool("JOB_SPY_ENABLE_LINKEDIN", True),
        allow_insecure_ssl_fallback=env_bool(
            "JOB_SPY_ALLOW_INSECURE_SSL_FALLBACK", True
        ),
        user_agent=DEFAULT_USER_AGENT,
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
        resume_llm_model=default_llm_model,
        title_similarity_model=os.getenv(
            "JOB_SPY_TITLE_MODEL", default_llm_model
        ).strip(),
        embedding_model=os.getenv(
            "JOB_SPY_EMBEDDING_MODEL", "text-embedding-3-large"
        ).strip(),
        assistant_model=os.getenv(
            "JOB_SPY_ASSISTANT_MODEL", default_llm_model
        ).strip(),
        snapshot_ttl_seconds=int(os.getenv("JOB_SPY_SNAPSHOT_TTL_SECONDS", "1800")),
        search_cache_ttl_seconds=int(
            os.getenv("JOB_SPY_SEARCH_CACHE_TTL_SECONDS", "1800")
        ),
        detail_cache_ttl_seconds=int(
            os.getenv("JOB_SPY_DETAIL_CACHE_TTL_SECONDS", "43200")
        ),
        cache_max_bytes=int(os.getenv("JOB_SPY_CACHE_MAX_BYTES", "256000000")),
        cache_max_files=int(os.getenv("JOB_SPY_CACHE_MAX_FILES", "4000")),
        cache_backend=os.getenv("JOB_SPY_CACHE_BACKEND", "filesystem").strip(),
        queue_backend=os.getenv("JOB_SPY_QUEUE_BACKEND", "sqlite").strip(),
        database_backend=os.getenv("JOB_SPY_DATABASE_BACKEND", "sqlite").strip(),
        crawl_execution_mode=os.getenv("JOB_SPY_CRAWL_EXECUTION_MODE", "inline").strip(),
        crawl_job_lease_seconds=int(
            os.getenv("JOB_SPY_CRAWL_JOB_LEASE_SECONDS", "180")
        ),
        show_backend_console=env_bool(
            "JOB_SPY_ENABLE_BACKEND_CONSOLE",
            True,
        ),
        runtime_job_max_retries=int(
            os.getenv("JOB_SPY_RUNTIME_JOB_MAX_RETRIES", "1")
        ),
        runtime_job_retry_backoff_seconds=int(
            os.getenv("JOB_SPY_RUNTIME_JOB_RETRY_BACKOFF_SECONDS", "90")
        ),
        runtime_cleanup_interval_seconds=int(
            os.getenv("JOB_SPY_RUNTIME_CLEANUP_INTERVAL_SECONDS", "21600")
        ),
        runtime_job_retention_days=int(
            os.getenv("JOB_SPY_RUNTIME_JOB_RETENTION_DAYS", "14")
        ),
        runtime_snapshot_retention_days=int(
            os.getenv("JOB_SPY_RUNTIME_SNAPSHOT_RETENTION_DAYS", "30")
        ),
        runtime_partial_snapshot_retention_hours=int(
            os.getenv("JOB_SPY_RUNTIME_PARTIAL_SNAPSHOT_RETENTION_HOURS", "12")
        ),
        runtime_signal_retention_days=int(
            os.getenv("JOB_SPY_RUNTIME_SIGNAL_RETENTION_DAYS", "14")
        ),
        market_history_retention_days=int(
            os.getenv("JOB_SPY_MARKET_HISTORY_RETENTION_DAYS", "90")
        ),
        market_history_max_runs_per_query=int(
            os.getenv("JOB_SPY_MARKET_HISTORY_MAX_RUNS_PER_QUERY", "100")
        ),
        smtp_host=os.getenv("JOB_RADAR_SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("JOB_RADAR_SMTP_PORT", "587")),
        smtp_username=os.getenv("JOB_RADAR_SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("JOB_RADAR_SMTP_PASSWORD", "").strip(),
        smtp_from_email=os.getenv("JOB_RADAR_SMTP_FROM", "").strip(),
        notification_email_to=os.getenv("JOB_RADAR_NOTIFY_EMAIL_TO", "").strip(),
        smtp_use_tls=env_bool("JOB_RADAR_SMTP_USE_TLS", True),
        smtp_use_ssl=env_bool("JOB_RADAR_SMTP_USE_SSL", False),
        line_channel_access_token=os.getenv(
            "JOB_RADAR_LINE_CHANNEL_ACCESS_TOKEN", ""
        ).strip(),
        line_channel_secret=os.getenv("JOB_RADAR_LINE_CHANNEL_SECRET", "").strip(),
        line_to=os.getenv("JOB_RADAR_LINE_TO", "").strip(),
        public_base_url=os.getenv("JOB_RADAR_PUBLIC_BASE_URL", "").strip().rstrip("/"),
        line_webhook_host=os.getenv("JOB_RADAR_LINE_WEBHOOK_HOST", "0.0.0.0").strip(),
        line_webhook_port=int(os.getenv("JOB_RADAR_LINE_WEBHOOK_PORT", "8787")),
    )
