"""實驗 manifest 與 case-level export。"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import EvalConfig
from .reporting import write_csv, write_json


def _stringify_path(path: Path | None) -> str | None:
    return str(path.resolve()) if path else None


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _relative_to(base: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_descriptor(path: Path | None, *, base: Path | None = None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.exists():
        return {
            "path": _relative_to(base or resolved.parent, resolved) if base else str(resolved),
            "exists": False,
        }
    stat = resolved.stat()
    return {
        "path": _relative_to(base or resolved.parent, resolved) if base else str(resolved),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "sha256": _sha256(resolved),
    }


def _run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _git_context(root: Path) -> dict[str, Any]:
    repo_root = _run_git(root, "rev-parse", "--show-toplevel")
    if not repo_root:
        return {"available": False, "root": str(root.resolve())}
    dirty_output = _run_git(root, "status", "--porcelain") or ""
    return {
        "available": True,
        "root": repo_root,
        "commit": _run_git(root, "rev-parse", "HEAD"),
        "branch": _run_git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(dirty_output),
    }


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")


def write_case_exports(
    *,
    run_dir: Path,
    case_sections: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []
    for section, rows in case_sections.items():
        normalized_rows = [dict(row) for row in rows]
        csv_path = run_dir / f"{section}_cases.csv"
        jsonl_path = run_dir / f"{section}_cases.jsonl"
        write_csv(csv_path, normalized_rows)
        write_jsonl(jsonl_path, normalized_rows)
        exports.append(
            {
                "section": section,
                "row_count": len(normalized_rows),
                "csv_path": _relative_to(run_dir, csv_path),
                "jsonl_path": _relative_to(run_dir, jsonl_path),
            }
        )
    return exports


def build_experiment_manifest(
    *,
    config: EvalConfig,
    run_name: str,
    run_dir: Path,
    summary_path: Path,
    report_path: Path,
    cli_args: Mapping[str, Any] | None = None,
    source_paths: Mapping[str, str | Path] | None = None,
    model_config: Mapping[str, Any] | None = None,
    snapshot_path: Path | None = None,
    fixtures_root: Path | None = None,
    case_exports: Sequence[Mapping[str, Any]] | None = None,
    extra_artifacts: Sequence[Mapping[str, Any]] | None = None,
    bundle_manifests: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    eval_root = config.fixtures_dir.parent.resolve()
    fixtures_root = fixtures_root.resolve() if fixtures_root else config.fixtures_dir.resolve()
    dataset_files = [
        fixtures_root / "assistant_questions.json",
        fixtures_root / "resume_extraction_labels.jsonl",
        fixtures_root / "resume_match_labels.jsonl",
        fixtures_root / "resume_cases.json",
        fixtures_root / "retrieval_cases.json",
    ]
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_name": run_name,
        "run_dir": str(run_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "report_path": str(report_path.resolve()),
        "cli_args": _json_safe(dict(cli_args or {})),
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "paths": {
            "project_root": str(config.project_root.resolve()),
            "eval_root": str(eval_root),
            "fixtures_root": str(fixtures_root),
            "results_dir": str(config.results_dir.resolve()),
            "snapshot_path": _stringify_path(snapshot_path.resolve() if snapshot_path else config.snapshot_path.resolve()),
        },
        "git": {
            "project_repo": _git_context(config.project_root),
            "eval_repo": _git_context(eval_root),
        },
        "dataset": {
            "fixtures_root": str(fixtures_root),
            "files": [
                descriptor
                for descriptor in (_file_descriptor(path, base=fixtures_root) for path in dataset_files)
                if descriptor
            ],
        },
        "snapshot": _file_descriptor(snapshot_path.resolve() if snapshot_path else config.snapshot_path.resolve()),
        "model_config": _json_safe(dict(model_config or {})),
        "source_paths": {
            key: str(value.resolve()) if isinstance(value, Path) else str(value)
            for key, value in (source_paths or {}).items()
        },
        "case_exports": _json_safe([dict(item) for item in (case_exports or [])]),
        "extra_artifacts": _json_safe([dict(item) for item in (extra_artifacts or [])]),
        "bundle_manifests": _json_safe([dict(item) for item in (bundle_manifests or [])]),
    }
    return manifest


def write_experiment_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    write_json(path, dict(manifest))
