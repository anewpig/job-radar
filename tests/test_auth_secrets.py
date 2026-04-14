"""Tests for syncing Streamlit auth secrets from environment values."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.auth_secrets import sync_streamlit_auth_secrets  # noqa: E402


class AuthSecretsSyncTests(unittest.TestCase):
    def test_sync_writes_google_config_and_derives_redirect_uri(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        env = {
            "JOB_RADAR_PUBLIC_BASE_URL": "https://jobradar.example.com",
            "JOB_RADAR_OIDC_COOKIE_SECRET": "cookie-secret",
            "JOB_RADAR_GOOGLE_CLIENT_ID": "google-client-id",
            "JOB_RADAR_GOOGLE_CLIENT_SECRET": "google-client-secret",
        }

        with patch.dict(os.environ, env, clear=True):
            result = sync_streamlit_auth_secrets(base_dir)

        self.assertTrue(result.wrote_file)
        self.assertEqual(result.configured_providers, ("google",))
        content = (base_dir / ".streamlit" / "secrets.toml").read_text(encoding="utf-8")
        self.assertIn('redirect_uri = "https://jobradar.example.com/oauth2callback"', content)
        self.assertIn("[auth.google]", content)
        self.assertIn('server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"', content)
        self.assertNotIn("[auth.facebook]", content)

    def test_sync_writes_facebook_only_when_full_oidc_config_exists(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        env = {
            "JOB_RADAR_OIDC_REDIRECT_URI": "https://jobradar.example.com/oauth2callback",
            "JOB_RADAR_OIDC_COOKIE_SECRET": "cookie-secret",
            "JOB_RADAR_GOOGLE_CLIENT_ID": "google-client-id",
            "JOB_RADAR_GOOGLE_CLIENT_SECRET": "google-client-secret",
            "JOB_RADAR_FACEBOOK_CLIENT_ID": "facebook-client-id",
            "JOB_RADAR_FACEBOOK_CLIENT_SECRET": "facebook-client-secret",
            "JOB_RADAR_FACEBOOK_SERVER_METADATA_URL": "https://broker.example.com/.well-known/openid-configuration",
        }

        with patch.dict(os.environ, env, clear=True):
            result = sync_streamlit_auth_secrets(base_dir)

        self.assertEqual(result.configured_providers, ("google", "facebook"))
        content = (base_dir / ".streamlit" / "secrets.toml").read_text(encoding="utf-8")
        self.assertIn("[auth.facebook]", content)
        self.assertIn(
            'server_metadata_url = "https://broker.example.com/.well-known/openid-configuration"',
            content,
        )

    def test_incomplete_auth_env_does_not_overwrite_existing_manual_secrets(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        secrets_path = base_dir / ".streamlit" / "secrets.toml"
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        original = "[auth]\nredirect_uri = \"manual\"\ncookie_secret = \"manual\"\n"
        secrets_path.write_text(original, encoding="utf-8")

        with patch.dict(
            os.environ,
            {
                "JOB_RADAR_OIDC_COOKIE_SECRET": "cookie-secret",
                "JOB_RADAR_GOOGLE_CLIENT_ID": "google-client-id",
            },
            clear=True,
        ):
            result = sync_streamlit_auth_secrets(base_dir)

        self.assertTrue(result.managed_by_env)
        self.assertFalse(result.wrote_file)
        self.assertEqual(
            secrets_path.read_text(encoding="utf-8"),
            original,
        )
        self.assertIn("redirect_uri", result.missing_shared_fields)

    def test_sync_leaves_existing_file_untouched_without_auth_env(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        secrets_path = base_dir / ".streamlit" / "secrets.toml"
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        secrets_path.write_text("[auth]\nredirect_uri = \"manual\"\n", encoding="utf-8")

        with patch.dict(os.environ, {}, clear=True):
            result = sync_streamlit_auth_secrets(base_dir)

        self.assertFalse(result.wrote_file)
        self.assertFalse(result.managed_by_env)
        self.assertEqual(
            secrets_path.read_text(encoding="utf-8"),
            "[auth]\nredirect_uri = \"manual\"\n",
        )

    def test_public_base_url_alone_does_not_trigger_auth_sync(self) -> None:
        base_dir = Path(tempfile.mkdtemp())
        secrets_path = base_dir / ".streamlit" / "secrets.toml"
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        secrets_path.write_text("[auth]\nredirect_uri = \"manual\"\n", encoding="utf-8")

        with patch.dict(
            os.environ,
            {"JOB_RADAR_PUBLIC_BASE_URL": "https://jobradar.example.com"},
            clear=True,
        ):
            result = sync_streamlit_auth_secrets(base_dir)

        self.assertFalse(result.managed_by_env)
        self.assertEqual(
            secrets_path.read_text(encoding="utf-8"),
            "[auth]\nredirect_uri = \"manual\"\n",
        )


if __name__ == "__main__":
    unittest.main()
