"""評估框架設定與路徑管理。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import sys


EVAL_ROOT = Path(__file__).resolve().parents[1]


def _discover_default_project_root() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "src" / "job_spy_tw").exists():
        return repo_root
    cwd = Path.cwd().resolve()
    if (cwd / "src" / "job_spy_tw").exists():
        return cwd
    return repo_root


DEFAULT_PROJECT_ROOT = _discover_default_project_root()


@dataclass(slots=True)
class EvalConfig:
    """集中管理評估工作區與主專案路徑。"""

    project_root: Path
    snapshot_path: Path
    fixtures_dir: Path
    results_dir: Path


@dataclass(slots=True)
class EvalModelConfig:
    """集中管理真實模型評估所需的模型設定。"""

    openai_api_key: str
    openai_base_url: str
    assistant_model: str
    embedding_model: str
    resume_llm_model: str
    title_similarity_model: str


def build_config() -> EvalConfig:
    """建立評估框架執行所需的路徑設定。"""
    project_root = Path(os.getenv("JOB_RADAR_PROJECT_ROOT", DEFAULT_PROJECT_ROOT)).resolve()
    return EvalConfig(
        project_root=project_root,
        snapshot_path=project_root / "data" / "jobs_latest.json",
        fixtures_dir=EVAL_ROOT / "fixtures",
        results_dir=EVAL_ROOT / "results",
    )


def ensure_project_importable(project_root: Path) -> None:
    """將主專案的 `src` 加入 `sys.path`，讓外部框架可直接 import 正式程式。"""
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def build_model_config(project_root: Path) -> EvalModelConfig:
    """從主專案 settings 載入真實模型評估需要的設定。"""
    ensure_project_importable(project_root)
    from job_spy_tw.settings.loader import load_settings

    settings = load_settings(project_root)
    return EvalModelConfig(
        openai_api_key=settings.openai_api_key,
        openai_base_url=settings.openai_base_url,
        assistant_model=settings.assistant_model,
        embedding_model=settings.embedding_model,
        resume_llm_model=settings.resume_llm_model,
        title_similarity_model=settings.title_similarity_model,
    )


def require_real_model_config(model_config: EvalModelConfig) -> None:
    """檢查真實模型評估所需的最基本設定。"""
    if not model_config.openai_api_key:
        raise RuntimeError("未設定 OPENAI_API_KEY，無法執行 real model eval。")
