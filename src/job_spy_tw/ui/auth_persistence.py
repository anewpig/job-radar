"""Persistent auth helpers for password-based login."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import streamlit as st

from ..product_store import ProductStore
from .session import activate_user_session


COOKIE_NAME = "job_radar_auth_token"
COOKIE_PREFIX = "job-radar"


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: int
    issued_at: int
    expires_at: int


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _token_ttl_seconds() -> int:
    raw = _env("JOB_RADAR_AUTH_TOKEN_TTL_SECONDS") or "259200"
    try:
        return max(60, int(raw))
    except ValueError:
        return 259200


def _cookie_password() -> str:
    return _env("JOB_RADAR_AUTH_COOKIE_SECRET") or _env("JOB_RADAR_OIDC_COOKIE_SECRET")


def _token_secret() -> str:
    return _env("JOB_RADAR_AUTH_TOKEN_SECRET") or _cookie_password()


def _urlsafe_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _urlsafe_b64_decode(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def _sign(payload: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _urlsafe_b64(signature)


def _encode_token(payload: TokenPayload, secret: str) -> str:
    body = json.dumps(
        {
            "uid": payload.user_id,
            "iat": payload.issued_at,
            "exp": payload.expires_at,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{_urlsafe_b64(body)}.{_sign(body, secret)}"


def _decode_token(token: str, secret: str) -> TokenPayload | None:
    if not token or "." not in token:
        return None
    body_b64, signature = token.split(".", 1)
    try:
        body = _urlsafe_b64_decode(body_b64)
    except Exception:
        return None
    if not hmac.compare_digest(_sign(body, secret), signature):
        return None
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return None
    try:
        return TokenPayload(
            user_id=int(payload.get("uid")),
            issued_at=int(payload.get("iat")),
            expires_at=int(payload.get("exp")),
        )
    except Exception:
        return None


def _cookie_manager():
    password = _cookie_password()
    if not password:
        return None
    try:
        from streamlit_cookies_manager import EncryptedCookieManager
    except Exception:
        return None
    cookies = EncryptedCookieManager(prefix=COOKIE_PREFIX, password=password)
    if not cookies.ready():
        st.stop()
    return cookies


def persist_login(*, user_id: int) -> None:
    cookies = _cookie_manager()
    if cookies is None:
        return
    secret = _token_secret()
    if not secret:
        return
    now = int(time.time())
    ttl = _token_ttl_seconds()
    token = _encode_token(
        TokenPayload(
            user_id=user_id,
            issued_at=now,
            expires_at=now + ttl,
        ),
        secret=secret,
    )
    cookies[COOKIE_NAME] = token
    cookies.save()


def clear_persistent_login() -> None:
    cookies = _cookie_manager()
    if cookies is None:
        return
    if COOKIE_NAME in cookies:
        cookies.pop(COOKIE_NAME)
        cookies.save()


def restore_persistent_login(
    *,
    product_store: ProductStore,
    guest_user,
) -> bool:
    cookies = _cookie_manager()
    if cookies is None:
        return False
    token = cookies.get(COOKIE_NAME)
    secret = _token_secret()
    if not token or not secret:
        return False
    payload = _decode_token(token, secret)
    if payload is None:
        clear_persistent_login()
        return False
    if payload.expires_at < int(time.time()):
        clear_persistent_login()
        return False
    user = product_store.get_user(int(payload.user_id))
    if user is None or bool(user.is_guest):
        clear_persistent_login()
        return False
    activate_user_session(
        user=user,
        product_store=product_store,
        success_message="",
        login_method="password",
    )
    return True


def persistence_status() -> dict[str, Any]:
    return {
        "cookie_enabled": bool(_cookie_password()),
        "token_secret_enabled": bool(_token_secret()),
        "ttl_seconds": _token_ttl_seconds(),
    }
