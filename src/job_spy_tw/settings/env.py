"""Settings helpers for env."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path, override: bool = True) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if value == "":
            if override:
                os.environ.pop(key, None)
            continue
        if not override and key in os.environ:
            continue
        os.environ[key] = value


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
