"""Tests for forgot-password UI handlers."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = types.ModuleType("streamlit")

from job_spy_tw.ui import auth_reset_views, auth_state  # noqa: E402


class _SessionState(dict):
    def __getattr__(self, key: str):
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class _RerunCalled(RuntimeError):
    pass


class AuthResetViewTests(unittest.TestCase):
    def _fake_streamlit(self, session_state: dict[str, object]):
        return SimpleNamespace(
            session_state=_SessionState(session_state),
            rerun=mock.Mock(side_effect=_RerunCalled()),
        )

    def test_forgot_request_rejects_invalid_email_and_records_audit_event(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "dialog_reset_email_input": "not-an-email",
                "auth_form_error": "",
                "auth_form_success": "",
                "auth_form_field_errors": {},
            }
        )
        product_store = SimpleNamespace(
            record_audit_event=mock.Mock(),
            issue_password_reset=mock.Mock(),
        )
        notification_service = SimpleNamespace(send_password_reset_code=mock.Mock())

        with mock.patch.object(auth_reset_views, "st", fake_streamlit):
            with mock.patch.object(auth_state, "st", fake_streamlit):
                with mock.patch.object(
                    auth_reset_views,
                    "new_trace_id",
                    return_value="auth-trace-1",
                ):
                    with self.assertRaises(_RerunCalled):
                        auth_reset_views._handle_forgot_request_submit(
                            product_store=product_store,
                            notification_service=notification_service,
                        )

        product_store.record_audit_event.assert_called_once_with(
            event_type="auth.password_reset.request_validation_failed",
            status="blocked",
            target_type="user_email",
            target_id="not-an-email",
            details={"reason": "invalid_email"},
            trace_id="auth-trace-1",
        )
        product_store.issue_password_reset.assert_not_called()
        notification_service.send_password_reset_code.assert_not_called()
        self.assertEqual(fake_streamlit.session_state.auth_form_error, "請先輸入有效的 Email。")
        self.assertEqual(
            fake_streamlit.session_state.auth_form_field_errors,
            {"reset_email": "請輸入有效的 Email。"},
        )

    def test_forgot_request_uses_generic_success_for_unknown_email(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "dialog_reset_email_input": "missing@example.com",
                "auth_view_mode": auth_state.AUTH_VIEW_LOGIN,
                "auth_form_error": "",
                "auth_form_success": "",
                "auth_form_field_errors": {},
                "auth_reset_email_prefill": "",
            }
        )
        product_store = SimpleNamespace(
            record_audit_event=mock.Mock(),
            issue_password_reset=mock.Mock(side_effect=ValueError("找不到使用者")),
        )
        notification_service = SimpleNamespace(send_password_reset_code=mock.Mock())

        with mock.patch.object(auth_reset_views, "st", fake_streamlit):
            with mock.patch.object(auth_state, "st", fake_streamlit):
                with mock.patch.object(
                    auth_reset_views,
                    "new_trace_id",
                    return_value="auth-trace-2",
                ):
                    with self.assertRaises(_RerunCalled):
                        auth_reset_views._handle_forgot_request_submit(
                            product_store=product_store,
                            notification_service=notification_service,
                        )

        self.assertEqual(
            fake_streamlit.session_state.auth_view_mode,
            auth_state.AUTH_VIEW_FORGOT_CONFIRM,
        )
        self.assertEqual(
            fake_streamlit.session_state.auth_form_success,
            "如果這個 Email 有註冊，我們已寄出重設碼。",
        )
        self.assertEqual(
            fake_streamlit.session_state.auth_reset_email_prefill,
            "missing@example.com",
        )
        self.assertEqual(
            fake_streamlit.session_state.dialog_reset_email_confirm_input,
            "missing@example.com",
        )
        notification_service.send_password_reset_code.assert_not_called()
        product_store.record_audit_event.assert_not_called()

    def test_forgot_confirm_success_returns_to_login_and_records_audit_event(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "dialog_reset_email_confirm_input": "member@example.com",
                "dialog_reset_code_input": "123456",
                "dialog_reset_new_password_input": "new-password-123",
                "dialog_reset_new_password_confirm_input": "new-password-123",
                "auth_view_mode": auth_state.AUTH_VIEW_FORGOT_CONFIRM,
                "auth_form_error": "",
                "auth_form_success": "",
                "auth_form_field_errors": {},
            }
        )
        user = SimpleNamespace(id=5, email="member@example.com", role="user")
        product_store = SimpleNamespace(
            record_audit_event=mock.Mock(),
            reset_password_with_code=mock.Mock(return_value=user),
        )

        with mock.patch.object(auth_reset_views, "st", fake_streamlit):
            with mock.patch.object(auth_state, "st", fake_streamlit):
                with mock.patch.object(
                    auth_reset_views,
                    "new_trace_id",
                    return_value="auth-trace-3",
                ):
                    with self.assertRaises(_RerunCalled):
                        auth_reset_views._handle_forgot_confirm_submit(
                            product_store=product_store
                        )

        product_store.reset_password_with_code.assert_called_once_with(
            email="member@example.com",
            reset_code="123456",
            new_password="new-password-123",
        )
        product_store.record_audit_event.assert_called_once_with(
            event_type="auth.password_reset.confirm_succeeded",
            status="success",
            target_type="user",
            target_id="5",
            details={"email": "member@example.com"},
            user_id=5,
            actor_role="user",
            trace_id="auth-trace-3",
        )
        self.assertEqual(fake_streamlit.session_state.auth_view_mode, auth_state.AUTH_VIEW_LOGIN)
        self.assertEqual(
            fake_streamlit.session_state.auth_form_success,
            "密碼已重設，現在可以直接登入。",
        )

    def test_forgot_confirm_maps_reset_code_error_to_field(self) -> None:
        fake_streamlit = self._fake_streamlit(
            {
                "dialog_reset_email_confirm_input": "member@example.com",
                "dialog_reset_code_input": "000000",
                "dialog_reset_new_password_input": "new-password-123",
                "dialog_reset_new_password_confirm_input": "new-password-123",
                "auth_form_error": "",
                "auth_form_success": "",
                "auth_form_field_errors": {},
            }
        )
        product_store = SimpleNamespace(
            record_audit_event=mock.Mock(),
            reset_password_with_code=mock.Mock(side_effect=ValueError("重設碼無效")),
        )

        with mock.patch.object(auth_reset_views, "st", fake_streamlit):
            with mock.patch.object(auth_state, "st", fake_streamlit):
                with mock.patch.object(
                    auth_reset_views,
                    "new_trace_id",
                    return_value="auth-trace-4",
                ):
                    with self.assertRaises(_RerunCalled):
                        auth_reset_views._handle_forgot_confirm_submit(
                            product_store=product_store
                        )

        product_store.record_audit_event.assert_called_once_with(
            event_type="auth.password_reset.confirm_failed",
            status="error",
            target_type="user_email",
            target_id="member@example.com",
            details={
                "error_code": "AUTH_INVALID_RESET_CODE",
                "error_kind": "auth_error",
                "error_retryable": False,
                "error_user_message": "重設碼無效，請重新確認。",
                "error_message": "重設碼無效",
                "error_type": "ValueError",
                "error_metadata": {
                    "operation": "password_reset_confirm",
                    "email": "member@example.com",
                },
            },
            trace_id="auth-trace-4",
        )
        self.assertEqual(fake_streamlit.session_state.auth_form_error, "重設碼無效，請重新確認。")
        self.assertEqual(
            fake_streamlit.session_state.auth_form_field_errors,
            {"reset_code": "重設碼無效，請重新確認。"},
        )


if __name__ == "__main__":
    unittest.main()
