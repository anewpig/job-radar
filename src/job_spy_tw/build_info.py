"""Build and release metadata helpers."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any


PACKAGE_NAME = "job-spy-tw"
API_VERSION = "job-radar.api.v1"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    package_name: str
    package_version: str
    api_version: str
    deploy_env: str
    release_channel: str
    git_sha: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_build_info() -> BuildInfo:
    try:
        package_version = version(PACKAGE_NAME)
    except PackageNotFoundError:
        package_version = "0.0.0+local"
    return BuildInfo(
        package_name=PACKAGE_NAME,
        package_version=package_version,
        api_version=API_VERSION,
        deploy_env=os.getenv("JOB_RADAR_DEPLOY_ENV", "local").strip() or "local",
        release_channel=os.getenv("JOB_RADAR_RELEASE_CHANNEL", "dev").strip() or "dev",
        git_sha=os.getenv("JOB_RADAR_GIT_SHA", "unknown").strip() or "unknown",
    )
