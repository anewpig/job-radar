"""Structured application errors for runtime, auth, AI, and notifications."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any, Mapping
from urllib import error as urllib_error


ERROR_KIND_CONNECTOR = "connector_error"
ERROR_KIND_LLM = "llm_error"
ERROR_KIND_RUNTIME = "runtime_error"
ERROR_KIND_AUTH = "auth_error"
ERROR_KIND_NOTIFICATION = "notification_error"
ERROR_KIND_VALIDATION = "validation_error"
ERROR_KIND_UNKNOWN = "unknown_error"

ERROR_CODE_CONNECTOR_TIMEOUT = "CONNECTOR_TIMEOUT"
ERROR_CODE_CONNECTOR_RATE_LIMITED = "CONNECTOR_RATE_LIMITED"
ERROR_CODE_CONNECTOR_REQUEST_BLOCKED = "CONNECTOR_REQUEST_BLOCKED"
ERROR_CODE_CONNECTOR_PARSE_FAILED = "CONNECTOR_PARSE_FAILED"
ERROR_CODE_CONNECTOR_UNAVAILABLE = "CONNECTOR_UNAVAILABLE"
ERROR_CODE_CONNECTOR_UNEXPECTED = "CONNECTOR_UNEXPECTED"

ERROR_CODE_LLM_INVALID_API_KEY = "LLM_INVALID_API_KEY"
ERROR_CODE_LLM_PERMISSION_SCOPE_MISSING = "LLM_PERMISSION_SCOPE_MISSING"
ERROR_CODE_LLM_AUTHENTICATION_FAILED = "LLM_AUTHENTICATION_FAILED"
ERROR_CODE_LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
ERROR_CODE_LLM_TIMEOUT = "LLM_TIMEOUT"
ERROR_CODE_LLM_SERVICE_UNAVAILABLE = "LLM_SERVICE_UNAVAILABLE"
ERROR_CODE_LLM_UNEXPECTED = "LLM_UNEXPECTED"

ERROR_CODE_RUNTIME_DATABASE_LOCKED = "RUNTIME_DATABASE_LOCKED"
ERROR_CODE_RUNTIME_QUEUE_STATE_INVALID = "RUNTIME_QUEUE_STATE_INVALID"
ERROR_CODE_RUNTIME_CLEANUP_FAILED = "RUNTIME_CLEANUP_FAILED"
ERROR_CODE_RUNTIME_JOB_FAILED = "RUNTIME_JOB_FAILED"
ERROR_CODE_RUNTIME_UNEXPECTED = "RUNTIME_UNEXPECTED"

ERROR_CODE_AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
ERROR_CODE_AUTH_DUPLICATE_EMAIL = "AUTH_DUPLICATE_EMAIL"
ERROR_CODE_AUTH_INVALID_RESET_CODE = "AUTH_INVALID_RESET_CODE"
ERROR_CODE_AUTH_RESET_CODE_EXPIRED = "AUTH_RESET_CODE_EXPIRED"
ERROR_CODE_AUTH_NOTIFICATION_FAILED = "AUTH_NOTIFICATION_FAILED"
ERROR_CODE_AUTH_INVALID_INPUT = "AUTH_INVALID_INPUT"
ERROR_CODE_AUTH_UNEXPECTED = "AUTH_UNEXPECTED"

ERROR_CODE_NOTIFICATION_EMAIL_NOT_CONFIGURED = "NOTIFICATION_EMAIL_NOT_CONFIGURED"
ERROR_CODE_NOTIFICATION_EMAIL_SEND_FAILED = "NOTIFICATION_EMAIL_SEND_FAILED"
ERROR_CODE_NOTIFICATION_LINE_SEND_FAILED = "NOTIFICATION_LINE_SEND_FAILED"
ERROR_CODE_NOTIFICATION_SSL_VERIFICATION_FAILED = "NOTIFICATION_SSL_VERIFICATION_FAILED"
ERROR_CODE_NOTIFICATION_UNEXPECTED = "NOTIFICATION_UNEXPECTED"

ERROR_CODE_VALIDATION_INVALID_INPUT = "VALIDATION_INVALID_INPUT"
ERROR_CODE_VALIDATION_MISSING_INPUT = "VALIDATION_MISSING_INPUT"
ERROR_CODE_UNKNOWN_UNEXPECTED = "UNKNOWN_UNEXPECTED"


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    code: str
    kind: str
    retryable: bool
    user_message: str


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: str
    kind: str
    retryable: bool
    user_message: str
    technical_message: str
    error_type: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.code,
            "error_kind": self.kind,
            "error_retryable": self.retryable,
            "error_user_message": self.user_message,
            "error_message": self.technical_message,
            "error_type": self.error_type,
            "error_metadata": sanitize_metadata(self.metadata),
        }


class JobRadarError(Exception):
    """Application error with code, user-safe message, and retryability."""

    def __init__(
        self,
        *,
        code: str,
        kind: str,
        user_message: str,
        technical_message: str = "",
        retryable: bool = False,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = str(code).strip() or ERROR_CODE_UNKNOWN_UNEXPECTED
        self.kind = str(kind).strip() or ERROR_KIND_UNKNOWN
        self.user_message = str(user_message).strip() or "目前無法完成這個操作。"
        self.technical_message = (
            str(technical_message).strip()
            or self.user_message
            or self.code
        )
        self.retryable = bool(retryable)
        self.metadata = sanitize_metadata(metadata or {})
        super().__init__(self.technical_message)

    @property
    def info(self) -> ErrorInfo:
        return ErrorInfo(
            code=self.code,
            kind=self.kind,
            retryable=self.retryable,
            user_message=self.user_message,
            technical_message=self.technical_message,
            error_type=type(self).__name__,
            metadata=dict(self.metadata),
        )


ERROR_DEFINITIONS: dict[str, ErrorDefinition] = {
    ERROR_CODE_CONNECTOR_TIMEOUT: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_TIMEOUT,
        kind=ERROR_KIND_CONNECTOR,
        retryable=True,
        user_message="職缺來源連線逾時，稍後可再試一次。",
    ),
    ERROR_CODE_CONNECTOR_RATE_LIMITED: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_RATE_LIMITED,
        kind=ERROR_KIND_CONNECTOR,
        retryable=True,
        user_message="職缺來源目前限制請求頻率，稍後再試。",
    ),
    ERROR_CODE_CONNECTOR_REQUEST_BLOCKED: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_REQUEST_BLOCKED,
        kind=ERROR_KIND_CONNECTOR,
        retryable=True,
        user_message="職缺來源暫時拒絕這次請求，稍後再試。",
    ),
    ERROR_CODE_CONNECTOR_PARSE_FAILED: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_PARSE_FAILED,
        kind=ERROR_KIND_CONNECTOR,
        retryable=False,
        user_message="職缺來源格式已改變，這次資料暫時無法解析。",
    ),
    ERROR_CODE_CONNECTOR_UNAVAILABLE: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_UNAVAILABLE,
        kind=ERROR_KIND_CONNECTOR,
        retryable=True,
        user_message="職缺來源暫時無法連線，稍後可再試。",
    ),
    ERROR_CODE_CONNECTOR_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_CONNECTOR_UNEXPECTED,
        kind=ERROR_KIND_CONNECTOR,
        retryable=False,
        user_message="職缺抓取流程發生未預期錯誤。",
    ),
    ERROR_CODE_LLM_INVALID_API_KEY: ErrorDefinition(
        code=ERROR_CODE_LLM_INVALID_API_KEY,
        kind=ERROR_KIND_LLM,
        retryable=False,
        user_message="OpenAI API key 無效或已失效，請更新金鑰後再試。",
    ),
    ERROR_CODE_LLM_PERMISSION_SCOPE_MISSING: ErrorDefinition(
        code=ERROR_CODE_LLM_PERMISSION_SCOPE_MISSING,
        kind=ERROR_KIND_LLM,
        retryable=False,
        user_message="OpenAI 專案或 API key 缺少必要權限，請確認 project scope 已包含 Responses write。",
    ),
    ERROR_CODE_LLM_AUTHENTICATION_FAILED: ErrorDefinition(
        code=ERROR_CODE_LLM_AUTHENTICATION_FAILED,
        kind=ERROR_KIND_LLM,
        retryable=False,
        user_message="OpenAI 驗證失敗，請確認 API key 與專案設定。",
    ),
    ERROR_CODE_LLM_RATE_LIMITED: ErrorDefinition(
        code=ERROR_CODE_LLM_RATE_LIMITED,
        kind=ERROR_KIND_LLM,
        retryable=True,
        user_message="OpenAI 請求次數已達上限，請稍後再試。",
    ),
    ERROR_CODE_LLM_TIMEOUT: ErrorDefinition(
        code=ERROR_CODE_LLM_TIMEOUT,
        kind=ERROR_KIND_LLM,
        retryable=True,
        user_message="OpenAI 回應逾時，請稍後再試。",
    ),
    ERROR_CODE_LLM_SERVICE_UNAVAILABLE: ErrorDefinition(
        code=ERROR_CODE_LLM_SERVICE_UNAVAILABLE,
        kind=ERROR_KIND_LLM,
        retryable=True,
        user_message="OpenAI 服務暫時不可用，請稍後再試。",
    ),
    ERROR_CODE_LLM_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_LLM_UNEXPECTED,
        kind=ERROR_KIND_LLM,
        retryable=False,
        user_message="AI 服務發生未預期錯誤。",
    ),
    ERROR_CODE_RUNTIME_DATABASE_LOCKED: ErrorDefinition(
        code=ERROR_CODE_RUNTIME_DATABASE_LOCKED,
        kind=ERROR_KIND_RUNTIME,
        retryable=True,
        user_message="系統資料庫忙碌中，稍後可再試一次。",
    ),
    ERROR_CODE_RUNTIME_QUEUE_STATE_INVALID: ErrorDefinition(
        code=ERROR_CODE_RUNTIME_QUEUE_STATE_INVALID,
        kind=ERROR_KIND_RUNTIME,
        retryable=False,
        user_message="背景工作佇列狀態異常，請到維運頁檢查。",
    ),
    ERROR_CODE_RUNTIME_CLEANUP_FAILED: ErrorDefinition(
        code=ERROR_CODE_RUNTIME_CLEANUP_FAILED,
        kind=ERROR_KIND_RUNTIME,
        retryable=False,
        user_message="系統清理流程失敗，請檢查維運訊號。",
    ),
    ERROR_CODE_RUNTIME_JOB_FAILED: ErrorDefinition(
        code=ERROR_CODE_RUNTIME_JOB_FAILED,
        kind=ERROR_KIND_RUNTIME,
        retryable=False,
        user_message="背景工作執行失敗，請到維運頁查看 dead-letter queue。",
    ),
    ERROR_CODE_RUNTIME_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_RUNTIME_UNEXPECTED,
        kind=ERROR_KIND_RUNTIME,
        retryable=False,
        user_message="系統執行流程發生未預期錯誤。",
    ),
    ERROR_CODE_AUTH_INVALID_CREDENTIALS: ErrorDefinition(
        code=ERROR_CODE_AUTH_INVALID_CREDENTIALS,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="帳號或密碼不正確。",
    ),
    ERROR_CODE_AUTH_DUPLICATE_EMAIL: ErrorDefinition(
        code=ERROR_CODE_AUTH_DUPLICATE_EMAIL,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="這個 Email 已經被註冊。",
    ),
    ERROR_CODE_AUTH_INVALID_RESET_CODE: ErrorDefinition(
        code=ERROR_CODE_AUTH_INVALID_RESET_CODE,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="重設碼無效，請重新確認。",
    ),
    ERROR_CODE_AUTH_RESET_CODE_EXPIRED: ErrorDefinition(
        code=ERROR_CODE_AUTH_RESET_CODE_EXPIRED,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="重設碼已過期，請重新申請。",
    ),
    ERROR_CODE_AUTH_NOTIFICATION_FAILED: ErrorDefinition(
        code=ERROR_CODE_AUTH_NOTIFICATION_FAILED,
        kind=ERROR_KIND_AUTH,
        retryable=True,
        user_message="目前無法寄送驗證或重設通知，請稍後再試。",
    ),
    ERROR_CODE_AUTH_INVALID_INPUT: ErrorDefinition(
        code=ERROR_CODE_AUTH_INVALID_INPUT,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="輸入資料不完整或格式不正確。",
    ),
    ERROR_CODE_AUTH_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_AUTH_UNEXPECTED,
        kind=ERROR_KIND_AUTH,
        retryable=False,
        user_message="帳號流程發生未預期錯誤。",
    ),
    ERROR_CODE_NOTIFICATION_EMAIL_NOT_CONFIGURED: ErrorDefinition(
        code=ERROR_CODE_NOTIFICATION_EMAIL_NOT_CONFIGURED,
        kind=ERROR_KIND_NOTIFICATION,
        retryable=False,
        user_message="Email 通知服務尚未設定。",
    ),
    ERROR_CODE_NOTIFICATION_EMAIL_SEND_FAILED: ErrorDefinition(
        code=ERROR_CODE_NOTIFICATION_EMAIL_SEND_FAILED,
        kind=ERROR_KIND_NOTIFICATION,
        retryable=True,
        user_message="Email 通知寄送失敗，稍後可再試。",
    ),
    ERROR_CODE_NOTIFICATION_LINE_SEND_FAILED: ErrorDefinition(
        code=ERROR_CODE_NOTIFICATION_LINE_SEND_FAILED,
        kind=ERROR_KIND_NOTIFICATION,
        retryable=True,
        user_message="LINE 通知寄送失敗，稍後可再試。",
    ),
    ERROR_CODE_NOTIFICATION_SSL_VERIFICATION_FAILED: ErrorDefinition(
        code=ERROR_CODE_NOTIFICATION_SSL_VERIFICATION_FAILED,
        kind=ERROR_KIND_NOTIFICATION,
        retryable=True,
        user_message="通知服務的 SSL 驗證失敗。",
    ),
    ERROR_CODE_NOTIFICATION_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_NOTIFICATION_UNEXPECTED,
        kind=ERROR_KIND_NOTIFICATION,
        retryable=False,
        user_message="通知流程發生未預期錯誤。",
    ),
    ERROR_CODE_VALIDATION_INVALID_INPUT: ErrorDefinition(
        code=ERROR_CODE_VALIDATION_INVALID_INPUT,
        kind=ERROR_KIND_VALIDATION,
        retryable=False,
        user_message="輸入內容格式不正確。",
    ),
    ERROR_CODE_VALIDATION_MISSING_INPUT: ErrorDefinition(
        code=ERROR_CODE_VALIDATION_MISSING_INPUT,
        kind=ERROR_KIND_VALIDATION,
        retryable=False,
        user_message="缺少必要輸入欄位。",
    ),
    ERROR_CODE_UNKNOWN_UNEXPECTED: ErrorDefinition(
        code=ERROR_CODE_UNKNOWN_UNEXPECTED,
        kind=ERROR_KIND_UNKNOWN,
        retryable=False,
        user_message="系統發生未預期錯誤。",
    ),
}


def sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_metadata(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def classify_error(exc: Exception) -> str:
    return build_error_info(exc).kind


def definition_for(code: str) -> ErrorDefinition:
    return ERROR_DEFINITIONS.get(
        str(code).strip(),
        ERROR_DEFINITIONS[ERROR_CODE_UNKNOWN_UNEXPECTED],
    )


def build_application_error(
    *,
    code: str,
    technical_message: str = "",
    metadata: Mapping[str, Any] | None = None,
    retryable: bool | None = None,
    user_message: str | None = None,
) -> JobRadarError:
    definition = definition_for(code)
    return JobRadarError(
        code=definition.code,
        kind=definition.kind,
        user_message=(user_message or definition.user_message),
        technical_message=technical_message,
        retryable=definition.retryable if retryable is None else bool(retryable),
        metadata=metadata,
    )


def build_error_info(
    error: Exception | ErrorInfo | str,
    *,
    default_kind: str | None = None,
    default_code: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    retryable: bool | None = None,
    user_message: str | None = None,
) -> ErrorInfo:
    base_metadata = sanitize_metadata(metadata or {})
    if isinstance(error, ErrorInfo):
        merged_metadata = {**error.metadata, **base_metadata}
        return ErrorInfo(
            code=error.code,
            kind=error.kind,
            retryable=error.retryable if retryable is None else bool(retryable),
            user_message=user_message or error.user_message,
            technical_message=error.technical_message,
            error_type=error.error_type,
            metadata=merged_metadata,
        )

    if isinstance(error, JobRadarError):
        return build_error_info(
            error.info,
            metadata=base_metadata,
            retryable=retryable,
            user_message=user_message,
        )

    technical_message = str(error).strip() if isinstance(error, Exception) else str(error).strip()
    error_type = type(error).__name__ if isinstance(error, Exception) else "ErrorString"
    inferred = _infer_definition(
        error if isinstance(error, Exception) else None,
        technical_message=technical_message,
        default_kind=default_kind,
        default_code=default_code,
        metadata=base_metadata,
    )
    definition = definition_for(inferred.code)
    effective_retryable = definition.retryable if retryable is None else bool(retryable)
    effective_user_message = user_message or definition.user_message
    return ErrorInfo(
        code=definition.code,
        kind=definition.kind,
        retryable=effective_retryable,
        user_message=effective_user_message,
        technical_message=technical_message or effective_user_message or definition.code,
        error_type=error_type,
        metadata=base_metadata,
    )


def error_metadata(
    error: Exception | ErrorInfo | str,
    *,
    default_kind: str | None = None,
    default_code: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_error_info(
        error,
        default_kind=default_kind,
        default_code=default_code,
        metadata=metadata,
    ).to_dict()


def format_error_message(
    error: Exception | ErrorInfo | str,
    *,
    default_kind: str | None = None,
    default_code: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> str:
    return build_error_info(
        error,
        default_kind=default_kind,
        default_code=default_code,
        metadata=metadata,
    ).user_message


def serialize_error_info(error: Exception | ErrorInfo | str) -> dict[str, Any]:
    info = build_error_info(error)
    return {
        "code": info.code,
        "kind": info.kind,
        "retryable": info.retryable,
        "user_message": info.user_message,
        "technical_message": info.technical_message,
        "error_type": info.error_type,
        "metadata": sanitize_metadata(info.metadata),
    }


def _infer_definition(
    exc: Exception | None,
    *,
    technical_message: str,
    default_kind: str | None,
    default_code: str | None,
    metadata: Mapping[str, Any],
) -> ErrorDefinition:
    lowered = technical_message.lower()
    inferred_kind = _infer_kind(exc, lowered, default_kind=default_kind)
    if default_code:
        definition = definition_for(default_code)
        if default_kind and definition.kind != default_kind:
            return ErrorDefinition(
                code=definition.code,
                kind=default_kind,
                retryable=definition.retryable,
                user_message=definition.user_message,
            )
        return definition
    if inferred_kind == ERROR_KIND_LLM:
        return _infer_llm_definition(lowered)
    if inferred_kind == ERROR_KIND_NOTIFICATION:
        return _infer_notification_definition(lowered, metadata=metadata)
    if inferred_kind == ERROR_KIND_AUTH:
        return _infer_auth_definition(lowered, metadata=metadata)
    if inferred_kind == ERROR_KIND_RUNTIME:
        return _infer_runtime_definition(exc, lowered, metadata=metadata)
    if inferred_kind == ERROR_KIND_CONNECTOR:
        return _infer_connector_definition(lowered)
    if inferred_kind == ERROR_KIND_VALIDATION:
        return _infer_validation_definition(lowered)
    return ERROR_DEFINITIONS[ERROR_CODE_UNKNOWN_UNEXPECTED]


def _infer_kind(
    exc: Exception | None,
    lowered: str,
    *,
    default_kind: str | None,
) -> str:
    if default_kind:
        return default_kind
    if isinstance(exc, sqlite3.OperationalError):
        return ERROR_KIND_RUNTIME
    if isinstance(exc, urllib_error.URLError):
        return ERROR_KIND_NOTIFICATION if "line" in lowered else ERROR_KIND_CONNECTOR
    if any(token in lowered for token in ("openai", "embedding", "responses", "api key", "model")):
        return ERROR_KIND_LLM
    if any(token in lowered for token in ("smtp", "email", "line", "webhook", "mail")):
        return ERROR_KIND_NOTIFICATION
    if any(token in lowered for token in ("password", "login", "登入", "註冊", "reset", "重設")):
        return ERROR_KIND_AUTH
    if any(token in lowered for token in ("queue", "runtime", "lease", "worker", "scheduler", "cleanup", "database")):
        return ERROR_KIND_RUNTIME
    if any(token in lowered for token in ("crawl", "connector", "scrape", "html", "http")):
        return ERROR_KIND_CONNECTOR
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return ERROR_KIND_VALIDATION
    return ERROR_KIND_UNKNOWN


def _infer_llm_definition(lowered: str) -> ErrorDefinition:
    if "api.responses.write" in lowered or (
        "responses.write" in lowered and "permission" in lowered
    ):
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_PERMISSION_SCOPE_MISSING]
    if "invalid_api_key" in lowered or "incorrect api key provided" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_INVALID_API_KEY]
    if "401" in lowered and "authentication" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_AUTHENTICATION_FAILED]
    if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_RATE_LIMITED]
    if "timeout" in lowered or "timed out" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_TIMEOUT]
    if any(token in lowered for token in ("502", "503", "504", "service unavailable", "bad gateway")):
        return ERROR_DEFINITIONS[ERROR_CODE_LLM_SERVICE_UNAVAILABLE]
    return ERROR_DEFINITIONS[ERROR_CODE_LLM_UNEXPECTED]


def _infer_connector_definition(lowered: str) -> ErrorDefinition:
    if "timeout" in lowered or "timed out" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_TIMEOUT]
    if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_RATE_LIMITED]
    if any(token in lowered for token in ("403", "forbidden", "request denied", "blocked", "999")):
        return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_REQUEST_BLOCKED]
    if any(token in lowered for token in ("parse", "parser", "html", "selector", "schema")):
        return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_PARSE_FAILED]
    if any(token in lowered for token in ("connection", "network", "remote disconnected", "temporary failure", "service unavailable", "name or service not known")):
        return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_UNAVAILABLE]
    return ERROR_DEFINITIONS[ERROR_CODE_CONNECTOR_UNEXPECTED]


def _infer_runtime_definition(
    exc: Exception | None,
    lowered: str,
    *,
    metadata: Mapping[str, Any],
) -> ErrorDefinition:
    if isinstance(exc, sqlite3.OperationalError) or any(
        token in lowered
        for token in (
            "database is locked",
            "database table is locked",
            "database busy",
        )
    ):
        return ERROR_DEFINITIONS[ERROR_CODE_RUNTIME_DATABASE_LOCKED]
    if str(metadata.get("operation", "")).strip() == "runtime_cleanup":
        return ERROR_DEFINITIONS[ERROR_CODE_RUNTIME_CLEANUP_FAILED]
    if any(token in lowered for token in ("queue", "lease", "job #", "failed to find crawl job")):
        return ERROR_DEFINITIONS[ERROR_CODE_RUNTIME_QUEUE_STATE_INVALID]
    if any(token in lowered for token in ("worker", "crawl job", "scheduler")):
        return ERROR_DEFINITIONS[ERROR_CODE_RUNTIME_JOB_FAILED]
    return ERROR_DEFINITIONS[ERROR_CODE_RUNTIME_UNEXPECTED]


def _infer_auth_definition(
    lowered: str,
    *,
    metadata: Mapping[str, Any],
) -> ErrorDefinition:
    if any(token in lowered for token in ("已經被註冊", "already registered", "already exists")):
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_DUPLICATE_EMAIL]
    if any(token in lowered for token in ("invalid credentials", "帳號或密碼不正確")):
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_INVALID_CREDENTIALS]
    if "重設碼" in lowered and any(token in lowered for token in ("過期", "expired")):
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_RESET_CODE_EXPIRED]
    if "重設碼" in lowered and any(token in lowered for token in ("無效", "錯誤", "invalid")):
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_INVALID_RESET_CODE]
    if str(metadata.get("operation", "")).strip() == "password_reset_request":
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_NOTIFICATION_FAILED]
    if any(token in lowered for token in ("email", "密碼", "password", "輸入有效")):
        return ERROR_DEFINITIONS[ERROR_CODE_AUTH_INVALID_INPUT]
    return ERROR_DEFINITIONS[ERROR_CODE_AUTH_UNEXPECTED]


def _infer_notification_definition(
    lowered: str,
    *,
    metadata: Mapping[str, Any],
) -> ErrorDefinition:
    channel = str(metadata.get("channel", "")).strip().lower()
    if "尚未設定" in lowered and "email" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_NOTIFICATION_EMAIL_NOT_CONFIGURED]
    if "certificate_verify_failed" in lowered or "ssl" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_NOTIFICATION_SSL_VERIFICATION_FAILED]
    if channel == "line" or "line" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_NOTIFICATION_LINE_SEND_FAILED]
    if channel == "email" or "email" in lowered or "smtp" in lowered:
        return ERROR_DEFINITIONS[ERROR_CODE_NOTIFICATION_EMAIL_SEND_FAILED]
    return ERROR_DEFINITIONS[ERROR_CODE_NOTIFICATION_UNEXPECTED]


def _infer_validation_definition(lowered: str) -> ErrorDefinition:
    if any(token in lowered for token in ("required", "missing", "請輸入", "必要")):
        return ERROR_DEFINITIONS[ERROR_CODE_VALIDATION_MISSING_INPUT]
    return ERROR_DEFINITIONS[ERROR_CODE_VALIDATION_INVALID_INPUT]
