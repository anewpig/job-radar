"""Bootstrap 階段的 runtime/service 建立流程。"""

from __future__ import annotations

from pathlib import Path

from ..auth_secrets import sync_streamlit_auth_secrets
from ..config import load_settings
from ..runtime_maintenance_service import run_runtime_cleanup
from .bootstrap_types import AppRuntime
from .resources import (
    get_keyword_recommender,
    get_notification_service,
    get_product_store,
    get_user_data_store,
)


def bootstrap_runtime(root: Path) -> AppRuntime:
    """建立支撐整個 Streamlit 應用的共用服務。"""
    sync_streamlit_auth_secrets(root)
    settings = load_settings(root)
    run_runtime_cleanup(
        settings=settings,
        trigger="ui",
    )
    product_store = get_product_store(str(settings.product_state_db_path))
    return AppRuntime(
        root=root,
        settings=settings,
        keyword_recommender=get_keyword_recommender(),
        user_data_store=get_user_data_store(str(settings.user_data_db_path)),
        product_store=product_store,
        notification_service=get_notification_service(
            root=str(root),
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_from_email=settings.smtp_from_email,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_use_ssl=settings.smtp_use_ssl,
            line_channel_access_token=settings.line_channel_access_token,
            line_channel_secret=settings.line_channel_secret,
            line_to=settings.line_to,
            public_base_url=settings.public_base_url,
            line_webhook_host=settings.line_webhook_host,
            line_webhook_port=settings.line_webhook_port,
        ),
        guest_user=product_store.get_guest_user(),
    )
