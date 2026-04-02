from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from ..models import UserAccount
from .common import generate_password_reset_code, now_iso


GUEST_USER_ID = 1
GUEST_EMAIL = "guest@job-radar.local"
PBKDF2_ITERATIONS = 200_000


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


class UserRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_guest_user(self) -> UserAccount:
        user = self.get_user(GUEST_USER_ID)
        if user is None:
            raise RuntimeError("訪客帳號初始化失敗。")
        return user

    def get_user(self, user_id: int) -> UserAccount | None:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, is_guest, created_at, updated_at, last_login_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> UserAccount | None:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, is_guest, created_at, updated_at, last_login_at
                FROM users
                WHERE lower(email) = lower(?)
                """,
                (email.strip(),),
            ).fetchone()
        return self._row_to_user(row) if row else None

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
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    email,
                    display_name,
                    password_salt,
                    password_hash,
                    is_guest,
                    created_at,
                    updated_at,
                    last_login_at
                ) VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    cleaned_email,
                    cleaned_name,
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

    def authenticate_user(self, email: str, password: str) -> UserAccount | None:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, is_guest, created_at, updated_at, last_login_at,
                       password_salt, password_hash
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
                salt=str(row[7]),
                expected_hash=str(row[8]),
            ):
                return None
            now = now_iso()
            connection.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
                (now, now, int(row[0])),
            )
            connection.commit()
        return self.get_user(int(row[0]))

    def issue_password_reset(self, email: str, *, ttl_minutes: int = 15) -> tuple[UserAccount, str]:
        user = self.get_user_by_email(email)
        if user is None or user.is_guest:
            raise ValueError("找不到這個 Email 對應的帳號。")
        reset_code = generate_password_reset_code()
        created_at = now_iso()
        expires_at = (datetime.now() + timedelta(minutes=max(1, ttl_minutes))).isoformat(
            timespec="seconds"
        )
        with sqlite3.connect(self.db_path) as connection:
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
                (int(user.id), reset_code, created_at, expires_at),
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

        with sqlite3.connect(self.db_path) as connection:
            token_row = connection.execute(
                """
                SELECT id, expires_at, consumed_at
                FROM password_reset_tokens
                WHERE user_id = ? AND reset_code = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user.id), cleaned_code),
            ).fetchone()
            if token_row is None:
                raise ValueError("重設碼不正確。")
            if str(token_row[2] or "").strip():
                raise ValueError("這組重設碼已使用過，請重新申請。")
            expires_at = str(token_row[1] or "").strip()
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
            is_guest=bool(row[3]),
            created_at=str(row[4] or ""),
            updated_at=str(row[5] or ""),
            last_login_at=str(row[6] or ""),
        )
