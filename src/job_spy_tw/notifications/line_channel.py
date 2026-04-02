from __future__ import annotations

import ssl
from urllib import error, request

import certifi

from ..settings import Settings


def build_secure_ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def should_retry_without_ssl_verification(settings: Settings, exc: Exception) -> bool:
    if not settings.allow_insecure_ssl_fallback:
        return False
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError) or (
        "CERTIFICATE_VERIFY_FAILED" in str(exc)
    )


def open_line_request(
    req: request.Request,
    ssl_context: ssl.SSLContext,
) -> None:
    try:
        with request.urlopen(req, timeout=20, context=ssl_context) as response:  # noqa: S310
            if response.status >= 300:
                raise RuntimeError(f"LINE API 回傳 {response.status}")
    except error.HTTPError as exc:
        detail = ""
        try:
            payload = exc.read().decode("utf-8", errors="ignore").strip()
            if payload:
                detail = f"：{payload}"
        except Exception:  # noqa: BLE001
            detail = ""
        raise RuntimeError(f"LINE API 回傳 {exc.code}{detail}") from exc
