"""提供 UI 層會使用到的 service 與 store 工廠函式。"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..config import load_settings
from ..notification_service import NotificationService
from ..product_store import ProductStore
from ..rag_assistant import JobMarketRAGAssistant
from ..search_keyword_recommender import RoleKeywordRecommender
from ..user_data_store import UserDataStore


@st.cache_resource
def get_keyword_recommender() -> RoleKeywordRecommender:
    """回傳搜尋設定會使用到的關鍵字推薦器。"""
    return RoleKeywordRecommender()


def get_user_data_store(db_path: str) -> UserDataStore:
    """依指定 SQLite 路徑建立新的使用者資料儲存物件。"""
    return UserDataStore(Path(db_path))


def get_product_store(db_path: str) -> ProductStore:
    """依指定 SQLite 路徑建立新的產品資料儲存物件。"""
    return ProductStore(Path(db_path))


@st.cache_resource
def get_notification_service(
    *,
    root: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_from_email: str,
    smtp_use_tls: bool,
    smtp_use_ssl: bool,
    line_channel_access_token: str,
    line_channel_secret: str,
    line_to: str,
    public_base_url: str,
    line_webhook_host: str,
    line_webhook_port: int,
) -> NotificationService:
    """建立帶有執行期憑證覆寫的通知服務快取實例。"""
    settings = load_settings(Path(root))
    settings.smtp_host = smtp_host
    settings.smtp_port = smtp_port
    settings.smtp_username = smtp_username
    settings.smtp_password = smtp_password
    settings.smtp_from_email = smtp_from_email
    settings.smtp_use_tls = smtp_use_tls
    settings.smtp_use_ssl = smtp_use_ssl
    settings.line_channel_access_token = line_channel_access_token
    settings.line_channel_secret = line_channel_secret
    settings.line_to = line_to
    settings.public_base_url = public_base_url
    settings.line_webhook_host = line_webhook_host
    settings.line_webhook_port = line_webhook_port
    return NotificationService(settings)


@st.cache_resource
def get_rag_assistant(
    *,
    api_key: str,
    answer_model: str,
    embedding_model: str,
    base_url: str,
    cache_dir: str,
) -> JobMarketRAGAssistant:
    """回傳 AI 助理頁面會使用的快取 RAG 服務。"""
    return JobMarketRAGAssistant(
        api_key=api_key,
        answer_model=answer_model,
        embedding_model=embedding_model,
        base_url=base_url,
        cache_dir=Path(cache_dir),
    )
