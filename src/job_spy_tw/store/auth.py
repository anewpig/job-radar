"""Store-layer helpers for auth."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from ..models import UserAccount
from ..security import USER_ROLE_GUEST, USER_ROLE_USER, normalize_user_role
from ..sqlite_utils import connect_sqlite
from .common import generate_password_reset_code, now_iso


GUEST_USER_ID = 1
GUEST_EMAIL = "guest@job-radar.local"
PBKDF2_ITERATIONS = 200_000
PASSWORD_RESET_HASH_PREFIX = "pbkdf2-sha256"


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, *, salt: str, expected_hash: str) -> bool:
    calculated = hash_password(password, salt)
    return hmac.compare_digest(calculated, expected_hash)


def _normalize_reset_code(reset_code: str) -> str:
    return str(reset_code or "").strip().upper()


def _hash_password_reset_code(reset_code: str, *, salt: str) -> str:
    normalized_code = _normalize_reset_code(reset_code)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized_code.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def _encode_password_reset_code(reset_code: str) -> str:
    salt = secrets.token_hex(16)
    return (
        f"{PASSWORD_RESET_HASH_PREFIX}${salt}$"
        f"{_hash_password_reset_code(reset_code, salt=salt)}"
    )


def _verify_password_reset_code(reset_code: str, stored_value: str) -> bool:
    normalized_code = _normalize_reset_code(reset_code)
    cleaned_stored_value = str(stored_value or "").strip()
    if cleaned_stored_value.startswith(f"{PASSWORD_RESET_HASH_PREFIX}$"):
        try:
            _prefix, salt, expected_hash = cleaned_stored_value.split("$", maxsplit=2)
        except ValueError:
            return False
        calculated_hash = _hash_password_reset_code(normalized_code, salt=salt)
        return hmac.compare_digest(calculated_hash, expected_hash)
    return hmac.compare_digest(normalized_code, cleaned_stored_value.upper())


class UserRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_guest_user(self) -> UserAccount:
        user = self.get_user(GUEST_USER_ID)
        if user is None:
            raise RuntimeError("訪客帳號初始化失敗。")
        return user

    def get_user(self, user_id: int) -> UserAccount | None:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, role, is_guest, created_at, updated_at, last_login_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> UserAccount | None:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, role, is_guest, created_at, updated_at, last_login_at
                FROM users
                WHERE lower(email) = lower(?)
                """,
                (email.strip(),),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def list_users(self, *, include_guest: bool = False) -> list[UserAccount]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, email, display_name, role, is_guest, created_at, updated_at, last_login_at
                FROM users
                WHERE (? = 1 OR is_guest = 0)
                ORDER BY id ASC
                """,
                (1 if include_guest else 0,),
            ).fetchall()
        return [user for row in rows if (user := self._row_to_user(row)) is not None]

    def register_user(
        self,
        *,
        email: str,
        password: str,
        display_name: str = "",
    ) -> UserAccount:
        cleaned_email = email.strip().lower()
        cleaned_name = display_name.strip()
        if not cleaned_email or "@" not in cleaned_email:
            raise ValueError("請輸入有效的 Email。")
        if len(password) < 8:
            raise ValueError("密碼至少需要 8 個字元。")
        if self.get_user_by_email(cleaned_email) is not None:
            raise ValueError("這個 Email 已經被註冊。")

        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        now = now_iso()
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    email,
                    display_name,
                    role,
                    password_salt,
                    password_hash,
                    is_guest,
                    created_at,
                    updated_at,
                    last_login_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    cleaned_email,
                    cleaned_name,
                    USER_ROLE_USER,
                    salt,
                    password_hash,
                    now,
                    now,
                    now,
                ),
            )
            connection.commit()
            user_id = int(cursor.lastrowid)
        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("建立帳號後無法讀回使用者資料。")
        return user

    def ensure_system_user(
        self,
        *,
        email: str,
        display_name: str,
        role: str,
    ) -> UserAccount:
        cleaned_email = email.strip().lower()
        cleaned_name = display_name.strip()
        normalized_role = normalize_user_role(role)
        existing = self.get_user_by_email(cleaned_email)
        if existing is not None:
            if (
                existing.role != normalized_role
                or (cleaned_name and existing.display_name != cleaned_name)
            ):
                now = now_iso()
                with connect_sqlite(self.db_path) as connection:
                    connection.execute(
                        """
                        UPDATE users
                        SET role = ?, display_name = ?, updated_at = ?
                        WHERE id = ? AND is_guest = 0
                        """,
                        (
                            normalized_role,
                            cleaned_name or existing.display_name,
                            now,
                            int(existing.id),
                        ),
                    )
                    connection.commit()
                existing = self.get_user(int(existing.id)) or existing
            return existing

        placeholder_password = secrets.token_urlsafe(32)
        salt = secrets.token_hex(16)
        password_hash = hash_password(placeholder_password, salt)
        now = now_iso()
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    email,
                    display_name,
                    role,
                    password_salt,
                    password_hash,
                    is_guest,
                    created_at,
                    updated_at,
                    last_login_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, '')
                """,
                (
                    cleaned_email,
                    cleaned_name,
                    normalized_role,
                    salt,
                    password_hash,
                    now,
                    now,
                ),
            )
            connection.commit()
            user_id = int(cursor.lastrowid)
        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("建立系統帳號後無法讀回使用者資料。")
        return user

    def authenticate_user(self, email: str, password: str) -> UserAccount | None:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, is_guest, created_at, updated_at, last_login_at,
                       role, password_salt, password_hash
                FROM users
                WHERE lower(email) = lower(?)
                """,
                (email.strip(),),
            ).fetchone()
            if row is None:
                return None
            if bool(row[3]):
                return None
            if not verify_password(
                password,
                salt=str(row[8]),
                expected_hash=str(row[9]),
            ):
                return None
            now = now_iso()
            connection.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
                (now, now, int(row[0])),
            )
            connection.commit()
        return self.get_user(int(row[0]))

    def authenticate_oidc_user(
        self,
        *,
        provider: str,
        subject: str,
        email: str,
        display_name: str = "",
        email_verified: bool = False,
        link_user_id: int | None = None,
    ) -> UserAccount:
        cleaned_provider = provider.strip() or "oidc"
        cleaned_subject = subject.strip()
        cleaned_email = email.strip().lower()
        cleaned_name = display_name.strip()
        if not cleaned_email or "@" not in cleaned_email:
            raise ValueError("OIDC 回傳的 Email 無效。")
        if not cleaned_subject:
            raise ValueError("OIDC 回傳的 subject 無效。")
        if not bool(email_verified):
            raise ValueError("第三方登入沒有提供已驗證 Email，無法登入。")

        now = now_iso()
        with connect_sqlite(self.db_path) as connection:
            identity_row = connection.execute(
                """
                SELECT user_id
                FROM user_identities
                WHERE provider = ? AND subject = ?
                """,
                (cleaned_provider, cleaned_subject),
            ).fetchone()
            if identity_row is not None:
                user_id = int(identity_row[0])
                if link_user_id is not None and int(link_user_id) != user_id:
                    raise ValueError("這個第三方帳號已連結到其他工作台帳號。")
                self._touch_oidc_user(
                    connection=connection,
                    user_id=user_id,
                    email=cleaned_email,
                    display_name=cleaned_name,
                    now=now,
                )
            else:
                user_row = connection.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE lower(email) = lower(?)
                    LIMIT 1
                    """,
                    (cleaned_email,),
                ).fetchone()
                if link_user_id is not None:
                    target_user_row = connection.execute(
                        """
                        SELECT id, email, is_guest
                        FROM users
                        WHERE id = ?
                        LIMIT 1
                        """,
                        (int(link_user_id),),
                    ).fetchone()
                    if target_user_row is None or bool(target_user_row[2]):
                        raise ValueError("找不到可連結的網站帳號，請重新登入後再試。")
                    target_email = str(target_user_row[1] or "").strip().lower()
                    if target_email != cleaned_email:
                        raise ValueError(
                            "第三方帳號 Email 與目前網站帳號不同，無法自動連結。"
                        )
                    user_id = int(target_user_row[0])
                    self._touch_oidc_user(
                        connection=connection,
                        user_id=user_id,
                        email=cleaned_email,
                        display_name=cleaned_name,
                        now=now,
                    )
                elif user_row is not None:
                    raise ValueError(
                        "這個 Email 已有網站帳號，請先用密碼登入後再連結第三方登入。"
                    )
                else:
                    user_id = self._create_oidc_user(
                        connection=connection,
                        email=cleaned_email,
                        display_name=cleaned_name,
                        now=now,
                    )
                connection.execute(
                    """
                    INSERT INTO user_identities (
                        provider,
                        subject,
                        user_id,
                        email,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(provider, subject) DO UPDATE SET
                        user_id = excluded.user_id,
                        email = excluded.email,
                        updated_at = excluded.updated_at
                    """,
                    (
                        cleaned_provider,
                        cleaned_subject,
                        user_id,
                        cleaned_email,
                        now,
                        now,
                    ),
                )
            connection.commit()
        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("OIDC 登入後無法讀回使用者資料。")
        return user

    def issue_password_reset(self, email: str, *, ttl_minutes: int = 15) -> tuple[UserAccount, str]:
        user = self.get_user_by_email(email)
        if user is None or user.is_guest:
            raise ValueError("找不到這個 Email 對應的帳號。")
        reset_code = generate_password_reset_code()
        encoded_reset_code = _encode_password_reset_code(reset_code)
        created_at = now_iso()
        expires_at = (datetime.now() + timedelta(minutes=max(1, ttl_minutes))).isoformat(
            timespec="seconds"
        )
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                UPDATE password_reset_tokens
                SET consumed_at = ?
                WHERE user_id = ? AND consumed_at = ''
                """,
                (created_at, int(user.id)),
            )
            connection.execute(
                """
                INSERT INTO password_reset_tokens (
                    user_id,
                    reset_code,
                    created_at,
                    expires_at,
                    consumed_at
                ) VALUES (?, ?, ?, ?, '')
                """,
                (int(user.id), encoded_reset_code, created_at, expires_at),
            )
            connection.commit()
        return user, reset_code

    def reset_password_with_code(
        self,
        *,
        email: str,
        reset_code: str,
        new_password: str,
    ) -> UserAccount:
        cleaned_email = email.strip().lower()
        cleaned_code = reset_code.strip().upper()
        if len(new_password) < 8:
            raise ValueError("新密碼至少需要 8 個字元。")
        user = self.get_user_by_email(cleaned_email)
        if user is None or user.is_guest:
            raise ValueError("找不到這個 Email 對應的帳號。")

        with connect_sqlite(self.db_path) as connection:
            token_row = connection.execute(
                """
                SELECT id, reset_code, expires_at, consumed_at
                FROM password_reset_tokens
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user.id),),
            ).fetchone()
            if token_row is None:
                raise ValueError("重設碼不正確。")
            if not _verify_password_reset_code(cleaned_code, str(token_row[1] or "")):
                raise ValueError("重設碼不正確。")
            if str(token_row[3] or "").strip():
                raise ValueError("這組重設碼已使用過，請重新申請。")
            expires_at = str(token_row[2] or "").strip()
            if not expires_at or datetime.fromisoformat(expires_at) < datetime.now():
                raise ValueError("這組重設碼已過期，請重新申請。")

            salt = secrets.token_hex(16)
            password_hash = hash_password(new_password, salt)
            now = now_iso()
            connection.execute(
                """
                UPDATE users
                SET password_salt = ?, password_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (salt, password_hash, now, int(user.id)),
            )
            connection.execute(
                """
                UPDATE password_reset_tokens
                SET consumed_at = ?
                WHERE id = ?
                """,
                (now, int(token_row[0])),
            )
            connection.commit()
        updated_user = self.get_user(int(user.id))
        if updated_user is None:
            raise RuntimeError("重設密碼後無法讀回使用者資料。")
        return updated_user

    def _row_to_user(self, row) -> UserAccount | None:
        if row is None:
            return None
        return UserAccount(
            id=int(row[0]),
            email=str(row[1]),
            display_name=str(row[2] or ""),
            role=normalize_user_role(str(row[3] or USER_ROLE_USER)),
            is_guest=bool(row[4]),
            created_at=str(row[5] or ""),
            updated_at=str(row[6] or ""),
            last_login_at=str(row[7] or ""),
        )

    def _create_oidc_user(
        self,
        *,
        connection: sqlite3.Connection,
        email: str,
        display_name: str,
        now: str,
    ) -> int:
        placeholder_password = secrets.token_urlsafe(32)
        salt = secrets.token_hex(16)
        password_hash = hash_password(placeholder_password, salt)
        cursor = connection.execute(
            """
            INSERT INTO users (
                email,
                display_name,
                role,
                password_salt,
                password_hash,
                is_guest,
                created_at,
                updated_at,
                last_login_at
            ) VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                email,
                display_name,
                USER_ROLE_USER,
                salt,
                password_hash,
                now,
                now,
                now,
            ),
        )
        return int(cursor.lastrowid)

    def _touch_oidc_user(
        self,
        *,
        connection: sqlite3.Connection,
        user_id: int,
        email: str,
        display_name: str,
        now: str,
    ) -> None:
        connection.execute(
            """
            UPDATE users
            SET email = ?, display_name = CASE WHEN ? != '' THEN ? ELSE display_name END,
                updated_at = ?, last_login_at = ?
            WHERE id = ? AND is_guest = 0
            """,
            (
                email,
                display_name,
                display_name,
                now,
                now,
                user_id,
            ),
        )

    def set_user_role(self, *, user_id: int, role: str) -> UserAccount:
        normalized_role = normalize_user_role(role)
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                "SELECT is_guest FROM users WHERE id = ?",
                (int(user_id),),
            ).fetchone()
            if row is None:
                raise ValueError("找不到指定使用者。")
            if bool(row[0]):
                normalized_role = USER_ROLE_GUEST
            connection.execute(
                """
                UPDATE users
                SET role = ?, updated_at = ?
                WHERE id = ?
                """,
                (normalized_role, now_iso(), int(user_id)),
            )
            connection.commit()
        user = self.get_user(int(user_id))
        if user is None:
            raise RuntimeError("更新角色後無法讀回使用者資料。")
        return user
