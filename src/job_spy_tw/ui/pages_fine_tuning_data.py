"""Fine-tuning dashboard data loader."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
from urllib.request import urlopen


POSTTRAIN_ENV_KEYS = {
    "sft_manifest": "JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL",
    "dpo_manifest": "JOB_RADAR_POSTTRAIN_DPO_MANIFEST_URL",
    "eval_manifest": "JOB_RADAR_POSTTRAIN_EVAL_MANIFEST_URL",
    "review_manifest": "JOB_RADAR_POSTTRAIN_REVIEW_MANIFEST_URL",
    "trackio_sft": "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_URL",
    "trackio_dpo": "JOB_RADAR_POSTTRAIN_TRACKIO_DPO_URL",
}

ARTIFACT_ENV_KEYS = {
    "base_model": "JOB_RADAR_POSTTRAIN_BASE_MODEL",
    "sft_adapter_repo": "JOB_RADAR_POSTTRAIN_SFT_ADAPTER_REPO",
    "sft_model_repo": "JOB_RADAR_POSTTRAIN_SFT_MODEL_REPO",
    "dpo_adapter_repo": "JOB_RADAR_POSTTRAIN_DPO_ADAPTER_REPO",
    "dpo_model_repo": "JOB_RADAR_POSTTRAIN_DPO_MODEL_REPO",
    "dataset_repo": "JOB_RADAR_POSTTRAIN_DATASET_REPO",
    "artifact_repo": "JOB_RADAR_POSTTRAIN_ARTIFACT_REPO",
    "trackio_project": "JOB_RADAR_POSTTRAIN_TRACKIO_PROJECT",
    "latest_sft_run_id": "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_RUN_ID",
    "latest_dpo_run_id": "JOB_RADAR_POSTTRAIN_TRACKIO_DPO_RUN_ID",
}

LOCAL_SUMMARY_PREFIXES = {
    "sft_manifest": "posttrain_sft_dataset",
    "dpo_manifest": "posttrain_dpo_pairs",
    "eval_manifest": "posttrain_eval_comparison",
    "review_manifest": "posttrain_review_manifest",
}


def _project_root(project_root: Path | None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    return Path(__file__).resolve().parents[3]


def _results_dir(project_root: Path | None) -> Path:
    return _project_root(project_root) / "job-radar-eval" / "results"


def _is_url(ref: str) -> bool:
    parsed = urlparse(str(ref or "").strip())
    return parsed.scheme in {"http", "https"}


def _read_json_ref(ref: str) -> dict[str, Any]:
    if _is_url(ref):
        with urlopen(ref, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(ref).expanduser().resolve().read_text(encoding="utf-8"))


def _latest_local_summary(project_root: Path | None, prefix: str) -> str | None:
    candidates = sorted(_results_dir(project_root).glob(f"{prefix}_*/summary.json"))
    if not candidates:
        return None
    return str(candidates[-1].resolve())


def _infer_sample_size(payload: dict[str, Any], rows_key: str | None = None) -> int:
    if rows_key:
        rows = payload.get(rows_key)
        if isinstance(rows, list):
            return len(rows)
    for key in (
        "sample_size",
        "total_rows",
        "total_pairs",
        "reviewed_row_count",
        "row_count",
        "case_count",
    ):
        value = payload.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            nested = value.get("reviewed_row_count") or value.get("case_count")
            if isinstance(nested, int):
                return nested
    aggregate = payload.get("aggregate")
    if isinstance(aggregate, dict):
        for key in ("reviewed_row_count", "case_count", "row_count"):
            value = aggregate.get(key)
            if isinstance(value, int):
                return value
    return 0


def _empty_section(source: str = "") -> dict[str, Any]:
    return {
        "payload": {},
        "source": source,
        "updated_at": "",
        "sample_size": 0,
        "stale": False,
    }


def _load_manifest_section(
    section_key: str,
    *,
    project_root: Path | None,
    env: Mapping[str, str],
    previous_data: Mapping[str, Any] | None,
    warnings: list[str],
) -> dict[str, Any]:
    ref = str(env.get(POSTTRAIN_ENV_KEYS[section_key], "")).strip()
    source = ref or (_latest_local_summary(project_root, LOCAL_SUMMARY_PREFIXES[section_key]) or "")
    if not source:
        previous = (previous_data or {}).get(section_key)
        if previous:
            return dict(previous)
        return _empty_section()
    try:
        payload = _read_json_ref(source)
        return {
            "payload": payload,
            "source": source,
            "updated_at": str(payload.get("generated_at", "")),
            "sample_size": _infer_sample_size(payload, rows_key="rows"),
            "stale": False,
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        previous = (previous_data or {}).get(section_key)
        if previous:
            fallback = dict(previous)
            fallback["stale"] = True
            warnings.append(f"{section_key} 更新失敗，保留上次成功資料：{exc}")
            return fallback
        warnings.append(f"{section_key} 載入失敗：{exc}")
        return _empty_section(source)


def _normalize_trackio_payload(payload: Any, stage: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for row in payload:
            if not isinstance(row, dict):
                continue
            rows.append(
                {
                    "stage": str(row.get("stage", stage)),
                    "metric_name": str(row.get("metric_name", "")),
                    "step": row.get("step"),
                    "value": row.get("value"),
                    "timestamp": row.get("timestamp", row.get("updated_at", "")),
                }
            )
        return rows

    if not isinstance(payload, dict):
        return rows

    if isinstance(payload.get("rows"), list):
        return _normalize_trackio_payload(payload.get("rows"), stage)

    metrics = payload.get("metrics") or payload.get("series") or {}
    if isinstance(metrics, dict):
        for metric_name, series in metrics.items():
            if isinstance(series, list):
                for point in series:
                    if isinstance(point, dict):
                        rows.append(
                            {
                                "stage": stage,
                                "metric_name": str(metric_name),
                                "step": point.get("step", point.get("global_step")),
                                "value": point.get("value"),
                                "timestamp": point.get("timestamp", point.get("updated_at", payload.get("updated_at", ""))),
                            }
                        )
                    else:
                        rows.append(
                            {
                                "stage": stage,
                                "metric_name": str(metric_name),
                                "step": None,
                                "value": point,
                                "timestamp": payload.get("updated_at", ""),
                            }
                        )
            else:
                rows.append(
                    {
                        "stage": stage,
                        "metric_name": str(metric_name),
                        "step": payload.get("global_step"),
                        "value": series,
                        "timestamp": payload.get("updated_at", ""),
                    }
                )

    latest_metrics = payload.get("latest_metrics")
    if isinstance(latest_metrics, dict):
        existing = {(row["metric_name"], row.get("step")) for row in rows}
        for metric_name, value in latest_metrics.items():
            candidate = (str(metric_name), payload.get("global_step"))
            if candidate in existing:
                continue
            rows.append(
                {
                    "stage": stage,
                    "metric_name": str(metric_name),
                    "step": payload.get("global_step"),
                    "value": value,
                    "timestamp": payload.get("updated_at", ""),
                }
            )
    return rows


def _load_trackio_section(
    *,
    stage: str,
    project_root: Path | None,
    env: Mapping[str, str],
    previous_data: Mapping[str, Any] | None,
    warnings: list[str],
) -> dict[str, Any]:
    section_key = f"trackio_{stage}"
    ref = str(env.get(POSTTRAIN_ENV_KEYS[section_key], "")).strip()
    source = ref
    if not source:
        previous = (previous_data or {}).get(section_key)
        if previous:
            return dict(previous)
        return {
            "rows": [],
            "source": "",
            "updated_at": "",
            "sample_size": 0,
            "stale": False,
        }
    try:
        payload = _read_json_ref(source)
        rows = _normalize_trackio_payload(payload, stage)
        updated_at_candidates = [str(row.get("timestamp", "")) for row in rows if str(row.get("timestamp", ""))]
        updated_at = max(updated_at_candidates) if updated_at_candidates else str(payload.get("updated_at", ""))
        return {
            "rows": rows,
            "source": source,
            "updated_at": updated_at,
            "sample_size": len(rows),
            "stale": False,
            "run_id": env.get(ARTIFACT_ENV_KEYS[f"latest_{stage}_run_id"], ""),
            "project": env.get(ARTIFACT_ENV_KEYS["trackio_project"], ""),
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        previous = (previous_data or {}).get(section_key)
        if previous:
            fallback = dict(previous)
            fallback["stale"] = True
            warnings.append(f"{section_key} 更新失敗，保留上次成功資料：{exc}")
            return fallback
        warnings.append(f"{section_key} 載入失敗：{exc}")
        return {
            "rows": [],
            "source": source,
            "updated_at": "",
            "sample_size": 0,
            "stale": False,
        }


def _artifact_registry(env: Mapping[str, str], dashboard: Mapping[str, Any]) -> dict[str, Any]:
    eval_payload = dashboard.get("eval_manifest", {}).get("payload", {})
    sft_payload = dashboard.get("sft_manifest", {}).get("payload", {})
    dpo_payload = dashboard.get("dpo_manifest", {}).get("payload", {})
    return {
        "base_model": env.get(ARTIFACT_ENV_KEYS["base_model"], eval_payload.get("base_model", "")),
        "sft_adapter_repo": env.get(ARTIFACT_ENV_KEYS["sft_adapter_repo"], ""),
        "sft_model_repo": env.get(ARTIFACT_ENV_KEYS["sft_model_repo"], eval_payload.get("sft_model", "")),
        "dpo_adapter_repo": env.get(ARTIFACT_ENV_KEYS["dpo_adapter_repo"], ""),
        "dpo_model_repo": env.get(ARTIFACT_ENV_KEYS["dpo_model_repo"], eval_payload.get("dpo_model", "")),
        "dataset_repo": env.get(ARTIFACT_ENV_KEYS["dataset_repo"], ""),
        "artifact_repo": env.get(ARTIFACT_ENV_KEYS["artifact_repo"], ""),
        "trackio_project": env.get(ARTIFACT_ENV_KEYS["trackio_project"], ""),
        "latest_sft_run_id": env.get(ARTIFACT_ENV_KEYS["latest_sft_run_id"], ""),
        "latest_dpo_run_id": env.get(ARTIFACT_ENV_KEYS["latest_dpo_run_id"], ""),
        "dataset_version": dpo_payload.get("dataset_version") or sft_payload.get("dataset_version", ""),
        "eval_manifest_version": eval_payload.get("generated_at", ""),
        "generated_at": max(
            [
                str(section.get("updated_at", ""))
                for key, section in dashboard.items()
                if key.endswith("_manifest") and isinstance(section, dict)
            ]
            or [""]
        ),
    }


def load_post_training_dashboard_data(
    project_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    previous_data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """載入 fine-tuning dashboard 需要的 manifests 與 live metrics。"""
    effective_env: Mapping[str, str] = env if env is not None else os.environ
    warnings: list[str] = []
    dashboard: dict[str, Any] = {
        "sft_manifest": _load_manifest_section(
            "sft_manifest",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
        "dpo_manifest": _load_manifest_section(
            "dpo_manifest",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
        "eval_manifest": _load_manifest_section(
            "eval_manifest",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
        "review_manifest": _load_manifest_section(
            "review_manifest",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
        "trackio_sft": _load_trackio_section(
            stage="sft",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
        "trackio_dpo": _load_trackio_section(
            stage="dpo",
            project_root=project_root,
            env=effective_env,
            previous_data=previous_data,
            warnings=warnings,
        ),
    }
    dashboard["artifact_registry"] = _artifact_registry(effective_env, dashboard)
    dashboard["warnings"] = warnings
    dashboard["loaded_at"] = datetime.now().isoformat(timespec="seconds")
    dashboard["has_any_data"] = any(
        bool(section.get("payload") or section.get("rows"))
        for key, section in dashboard.items()
        if isinstance(section, dict) and key != "artifact_registry"
    )
    return dashboard
