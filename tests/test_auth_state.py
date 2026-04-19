"""Tests for auth-state OIDC session synchronization."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui import auth_state  # noqa: E402


class _SessionState(dict):
    def __getattr__(self, key: str):
        return self[key]

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class _FakeUser:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self.payload)


class _RerunCalled(RuntimeError):
    pass


class AuthStateTests(unittest.TestCase):
    def _fake_streamlit(
        self,
        *,
        session_state: dict[str, object],
        user_payload: dict[str, object],
        rerun_raises: bool = False,
    ):
        rerun = mock.Mock()
        if rerun_raises:
            rerun.side_effect = _RerunCalled()
        return SimpleNamespace(
            session_state=_SessionState(session_state),
            user=_FakeUser(user_payload),
            logout=mock.Mock(),
            rerun=rerun,
        )

    def test_sync_oidc_user_session_keeps_password_session_without_pending_link(self) -> None:
        fake_streamlit = self._fake_streamlit(
            session_state={
                "auth_login_method": "password",
                "auth_user_id": 42,
                "auth_user_email": "member@example.com",
                "auth_pending_oidc_link_user_id": 0,
                "show_auth_dialog": False,
            },
            user_payload={
                "is_logged_in": True,
                "iss": "https://accounts.google.com",
                "sub": "google-sub-1",
                "email": "member@example.com",
                "name": "Member",
                "email_verified": True,
            },
        )
        product_store = SimpleNamespace(
            authenticate_oidc_user=mock.Mock(
                side_effect=AssertionError("OIDC user should not be synchronized")
            )
        )
        guest_user = SimpleNamespace(id=0)

        with mock.patch.object(auth_state, "st", fake_streamlit):
            auth_state.sync_oidc_user_session(
                guest_user=guest_user,
                product_store=product_store,
            )

        product_store.authenticate_oidc_user.assert_not_called()
        fake_streamlit.logout.assert_not_called()
        fake_streamlit.rerun.assert_not_called()

    def test_sync_oidc_user_session_links_pending_identity_and_reruns(self) -> None:
        linked_user = SimpleNamespace(
            id=7,
            email="linked@example.com",
            display_name="Linked OIDC",
            is_guest=False,
        )
        fake_streamlit = self._fake_streamlit(
            session_state={
                "auth_login_method": "password",
                "auth_user_id": 7,
                "auth_user_email": "linked@example.com",
                "auth_pending_oidc_link_user_id": 7,
                "auth_pending_oidc_provider": "google",
                "show_auth_dialog": True,
            },
            user_payload={
                "is_logged_in": True,
                "iss": "google",
                "sub": "google-sub-9",
                "email": "linked@example.com",
                "name": "Linked OIDC",
                "email_verified": True,
            },
            rerun_raises=True,
        )
        product_store = SimpleNamespace(
            authenticate_oidc_user=mock.Mock(return_value=linked_user)
        )
        guest_user = SimpleNamespace(id=0)

        with mock.patch.object(auth_state, "st", fake_streamlit):
            with mock.patch.object(auth_state, "activate_user_session") as activate:
                with self.assertRaises(_RerunCalled):
                    auth_state.sync_oidc_user_session(
                        guest_user=guest_user,
                        product_store=product_store,
                    )

        product_store.authenticate_oidc_user.assert_called_once_with(
            provider="google",
            subject="google-sub-9",
            email="linked@example.com",
            display_name="Linked OIDC",
            email_verified=True,
            link_user_id=7,
        )
        activate.assert_called_once_with(
            user=linked_user,
            product_store=product_store,
            success_message="",
            login_method="oidc",
            oidc_provider="google",
            oidc_subject="google-sub-9",
        )
        self.assertEqual(fake_streamlit.session_state.auth_pending_oidc_link_user_id, 0)
        self.assertEqual(fake_streamlit.session_state.auth_pending_oidc_provider, "")
        self.assertFalse(fake_streamlit.session_state.show_auth_dialog)
        fake_streamlit.logout.assert_not_called()

    def test_sync_oidc_user_session_resets_to_guest_on_validation_error(self) -> None:
        fake_streamlit = self._fake_streamlit(
            session_state={
                "auth_login_method": "guest",
                "auth_user_id": 0,
                "auth_user_email": "",
                "auth_pending_oidc_link_user_id": 9,
                "auth_pending_oidc_provider": "google",
                "show_auth_dialog": False,
                "auth_form_error": "",
                "auth_form_success": "",
                "auth_form_field_errors": {},
            },
            user_payload={
                "is_logged_in": True,
                "iss": "google",
                "sub": "google-sub-unverified",
                "email": "guest@example.com",
                "name": "Guest",
                "email_verified": False,
            },
        )
        product_store = SimpleNamespace(
            authenticate_oidc_user=mock.Mock(side_effect=ValueError("Email 必須先驗證"))
        )
        guest_user = SimpleNamespace(id=0, email="guest@example.com", is_guest=True)

        with mock.patch.object(auth_state, "st", fake_streamlit):
            with mock.patch.object(auth_state, "activate_user_session") as activate:
                auth_state.sync_oidc_user_session(
                    guest_user=guest_user,
                    product_store=product_store,
                )

        self.assertEqual(fake_streamlit.session_state.auth_form_error, "Email 必須先驗證")
        self.assertTrue(fake_streamlit.session_state.show_auth_dialog)
        self.assertEqual(fake_streamlit.session_state.auth_pending_oidc_link_user_id, 0)
        self.assertEqual(fake_streamlit.session_state.auth_pending_oidc_provider, "")
        activate.assert_called_once_with(
            user=guest_user,
            product_store=product_store,
            success_message="",
        )
        fake_streamlit.logout.assert_called_once_with()
        fake_streamlit.rerun.assert_not_called()


if __name__ == "__main__":
    unittest.main()
