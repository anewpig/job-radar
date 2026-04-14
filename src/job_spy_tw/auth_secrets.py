"""Helpers for syncing Streamlit OIDC secrets from environment variables."""

from __future__ import annotations

import json
import os
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path

from .settings.env import load_dotenv


GOOGLE_SERVER_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


@dataclass(frozen=True, slots=True)
class AuthSecretsSyncResult:
    """Summary of the generated Streamlit auth secrets state."""

    secrets_path: Path
    wrote_file: bool
    managed_by_env: bool
    configured_providers: tuple[str, ...]
    missing_shared_fields: tuple[str, ...]
    provider_missing_fields: dict[str, tuple[str, ...]]


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _auth_env_present() -> bool:
    return any(
        _env(name)
        for name in (
            "JOB_RADAR_OIDC_REDIRECT_URI",
            "JOB_RADAR_OIDC_COOKIE_SECRET",
            "JOB_RADAR_GOOGLE_CLIENT_ID",
            "JOB_RADAR_GOOGLE_CLIENT_SECRET",
            "JOB_RADAR_GOOGLE_SERVER_METADATA_URL",
            "JOB_RADAR_FACEBOOK_CLIENT_ID",
            "JOB_RADAR_FACEBOOK_CLIENT_SECRET",
            "JOB_RADAR_FACEBOOK_SERVER_METADATA_URL",
        )
    )


def _provider_config(
    *,
    name: str,
    env_prefix: str,
    default_server_metadata_url: str = "",
) -> tuple[dict[str, str] | None, tuple[str, ...]]:
    client_id = _env(f"{env_prefix}_CLIENT_ID")
    client_secret = _env(f"{env_prefix}_CLIENT_SECRET")
    server_metadata_url = _env(f"{env_prefix}_SERVER_METADATA_URL") or default_server_metadata_url
    missing_fields: list[str] = []
    if not client_id:
        missing_fields.append("client_id")
    if not client_secret:
        missing_fields.append("client_secret")
    if not server_metadata_url:
        missing_fields.append("server_metadata_url")
    if missing_fields:
        return None, tuple(missing_fields)
    return {
        "name": name,
        "client_id": client_id,
        "client_secret": client_secret,
        "server_metadata_url": server_metadata_url,
    }, ()


def _build_auth_sections() -> tuple[dict[str, str], list[dict[str, str]], tuple[str, ...], dict[str, tuple[str, ...]]]:
    public_base_url = _env("JOB_RADAR_PUBLIC_BASE_URL").rstrip("/")
    redirect_uri = _env("JOB_RADAR_OIDC_REDIRECT_URI")
    if not redirect_uri and public_base_url:
        redirect_uri = f"{public_base_url}/oauth2callback"
    cookie_secret = _env("JOB_RADAR_OIDC_COOKIE_SECRET")

    shared_auth: dict[str, str] = {}
    missing_shared_fields: list[str] = []
    if redirect_uri:
        shared_auth["redirect_uri"] = redirect_uri
    else:
        missing_shared_fields.append("redirect_uri")
    if cookie_secret:
        shared_auth["cookie_secret"] = cookie_secret
    else:
        missing_shared_fields.append("cookie_secret")

    provider_missing_fields: dict[str, tuple[str, ...]] = {}
    providers: list[dict[str, str]] = []
    google_config, google_missing = _provider_config(
        name="google",
        env_prefix="JOB_RADAR_GOOGLE",
        default_server_metadata_url=GOOGLE_SERVER_METADATA_URL,
    )
    if google_config is not None:
        providers.append(google_config)
    else:
        provider_missing_fields["google"] = google_missing

    facebook_config, facebook_missing = _provider_config(
        name="facebook",
        env_prefix="JOB_RADAR_FACEBOOK",
    )
    if facebook_config is not None:
        providers.append(facebook_config)
    else:
        provider_missing_fields["facebook"] = facebook_missing

    return (
        shared_auth,
        providers,
        tuple(missing_shared_fields),
        provider_missing_fields,
    )


def render_streamlit_auth_secrets_from_env(root: str | Path) -> str | None:
    """Render `.streamlit/secrets.toml` content from auth-related env vars."""
    root_path = Path(root)
    load_dotenv(root_path / ".env", override=True)
    if not _auth_env_present():
        return None

    shared_auth, providers, _, _ = _build_auth_sections()
    if "redirect_uri" not in shared_auth or "cookie_secret" not in shared_auth or not providers:
        return None

    lines = [
        "# Generated from .env by job_spy_tw.auth_secrets.",
        "# Update auth values in .env instead of editing this file by hand.",
    ]
    lines.append("")
    lines.append("[auth]")
    lines.append(f'redirect_uri = {json.dumps(shared_auth["redirect_uri"])}')
    lines.append(f'cookie_secret = {json.dumps(shared_auth["cookie_secret"])}')
    for provider in providers:
        lines.append("")
        lines.append(f'[auth.{provider["name"]}]')
        lines.append(f'client_id = {json.dumps(provider["client_id"])}')
        lines.append(f'client_secret = {json.dumps(provider["client_secret"])}')
        lines.append(
            "server_metadata_url = "
            f'{json.dumps(provider["server_metadata_url"])}'
        )
    return "\n".join(lines) + "\n"


def sync_streamlit_auth_secrets(root: str | Path) -> AuthSecretsSyncResult:
    """Create or refresh `.streamlit/secrets.toml` from `.env` auth settings."""
    root_path = Path(root)
    load_dotenv(root_path / ".env", override=True)
    secrets_path = root_path / ".streamlit" / "secrets.toml"
    shared_auth, providers, missing_shared_fields, provider_missing_fields = _build_auth_sections()
    managed_by_env = _auth_env_present()
    if not managed_by_env:
        return AuthSecretsSyncResult(
            secrets_path=secrets_path,
            wrote_file=False,
            managed_by_env=False,
            configured_providers=(),
            missing_shared_fields=(),
            provider_missing_fields={},
        )

    rendered = render_streamlit_auth_secrets_from_env(root_path)
    if rendered is None:
        return AuthSecretsSyncResult(
            secrets_path=secrets_path,
            wrote_file=False,
            managed_by_env=True,
            configured_providers=(),
            missing_shared_fields=missing_shared_fields,
            provider_missing_fields=provider_missing_fields,
        )

    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    secrets_path.write_text(rendered, encoding="utf-8")
    return AuthSecretsSyncResult(
        secrets_path=secrets_path,
        wrote_file=True,
        managed_by_env=True,
        configured_providers=tuple(provider["name"] for provider in providers)
        if "redirect_uri" in shared_auth and "cookie_secret" in shared_auth
        else (),
        missing_shared_fields=missing_shared_fields,
        provider_missing_fields=provider_missing_fields,
    )


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Sync Streamlit OIDC secrets from .env.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project root that contains .env and .streamlit/",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = sync_streamlit_auth_secrets(Path(args.base_dir))
    if not result.managed_by_env:
        print("No auth env vars found. Existing .streamlit/secrets.toml was left untouched.")
        return 0

    providers = ", ".join(result.configured_providers) or "none"
    print(f"Synced auth secrets: {result.secrets_path}")
    print(f"Configured providers: {providers}")
    if result.missing_shared_fields:
        print("Missing shared auth fields:", ", ".join(result.missing_shared_fields))
    missing_provider_lines = [
        f"{provider}({', '.join(fields)})"
        for provider, fields in sorted(result.provider_missing_fields.items())
        if fields
    ]
    if missing_provider_lines:
        print("Provider gaps:", "; ".join(missing_provider_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
