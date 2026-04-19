from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LATENCY_THRESHOLDS = {
    "assistant_total_ms_mean": {"maximum": 8000.0, "label": "Assistant total latency"},
    "retrieval_cold_ms_mean": {"maximum": 2000.0, "label": "Retrieval cold latency"},
    "retrieval_warm_ms_mean": {"maximum": 400.0, "label": "Retrieval warm latency"},
    "resume_build_profile_ms_mean": {"maximum": 6000.0, "label": "Resume build_profile latency"},
    "resume_match_jobs_ms_mean": {"maximum": 7000.0, "label": "Resume match_jobs latency"},
    "resume_total_ms_mean": {"maximum": 13000.0, "label": "Resume total latency"},
    "resume_warm_build_profile_ms_mean": {"maximum": 250.0, "label": "Resume warm build_profile latency"},
}

CONSISTENCY_THRESHOLDS = {
    "resume_output_consistency_rate": {"minimum": 1.0, "label": "Resume warm output consistency"},
}

WARN_RATIO = 0.9


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_latency_regression(
    *,
    assistant_summary_path: Path,
    retrieval_summary_path: Path,
    resume_summary_path: Path,
    resume_warm_summary_path: Path | None = None,
) -> dict[str, Any]:
    assistant_summary = _load_json(assistant_summary_path)
    retrieval_summary = _load_json(retrieval_summary_path)
    resume_summary = _load_json(resume_summary_path)
    resume_warm_summary = _load_json(resume_warm_summary_path) if resume_warm_summary_path else None

    assistant = assistant_summary["real_snapshot"]["assistant"]["aggregate"]
    retrieval = retrieval_summary["real_snapshot"]["retrieval"]["aggregate"]
    resume = resume_summary["real_snapshot"]["resume"]["aggregate"]
    resume_warm = (resume_warm_summary or {}).get("aggregate", {})

    metrics = {
        "assistant_total_ms_mean": float(assistant.get("total_ms_mean", 0.0)),
        "retrieval_cold_ms_mean": float(retrieval.get("cold_ms_mean", 0.0)),
        "retrieval_warm_ms_mean": float(retrieval.get("warm_ms_mean", 0.0)),
        "resume_build_profile_ms_mean": float(resume.get("build_profile_ms_mean", 0.0)),
        "resume_match_jobs_ms_mean": float(resume.get("match_jobs_ms_mean", 0.0)),
        "resume_total_ms_mean": float(resume.get("total_ms_mean", 0.0)),
        "resume_warm_build_profile_ms_mean": float(resume_warm.get("warm_build_profile_ms_mean", 0.0)),
    }
    consistency_metrics = {
        "resume_output_consistency_rate": float(resume_warm.get("output_consistency_rate", 0.0)),
    }

    checks: list[dict[str, Any]] = []
    has_fail = False
    has_warn = False
    for key, rule in LATENCY_THRESHOLDS.items():
        actual = metrics[key]
        maximum = rule["maximum"]
        passed = actual <= maximum
        warned = passed and actual > (maximum * WARN_RATIO)
        if not passed:
            has_fail = True
        elif warned:
            has_warn = True
        checks.append(
            {
                "key": key,
                "label": rule["label"],
                "actual": round(actual, 3),
                "maximum": maximum,
                "passed": passed,
                "warned": warned,
            }
        )

    for key, rule in CONSISTENCY_THRESHOLDS.items():
        actual = consistency_metrics[key]
        minimum = rule["minimum"]
        passed = actual >= minimum
        warned = passed and actual < (minimum + (1.0 - minimum) * WARN_RATIO)
        if not passed:
            has_fail = True
        elif warned:
            has_warn = True
        checks.append(
            {
                "key": key,
                "label": rule["label"],
                "actual": round(actual, 4),
                "minimum": minimum,
                "passed": passed,
                "warned": warned,
            }
        )

    if has_fail:
        status = "FAIL"
        verdict = "至少有一個核心延遲指標超過門檻，先修速度，再談新功能或訓練。"
    elif has_warn:
        status = "WARN"
        verdict = "延遲尚未超標，但已逼近門檻。下一輪修改需要優先關注效能回歸。"
    else:
        status = "PASS"
        verdict = "核心延遲指標都在可接受範圍內。"

    return {
        "status": status,
        "verdict": verdict,
        "assistant_summary_path": str(assistant_summary_path),
        "retrieval_summary_path": str(retrieval_summary_path),
        "resume_summary_path": str(resume_summary_path),
        "resume_warm_summary_path": str(resume_warm_summary_path) if resume_warm_summary_path else "",
        "checks": checks,
    }


def build_latency_regression_report(summary: dict[str, Any]) -> str:
    lines = []
    for item in summary["checks"]:
        state = "FAIL" if not item["passed"] else ("WARN" if item["warned"] else "PASS")
        if "maximum" in item:
            lines.append(
                f"- {item['label']}：`{item['actual']} ms` / 門檻 `<= {item['maximum']} ms` {state}"
            )
        else:
            lines.append(
                f"- {item['label']}：`{item['actual']}` / 門檻 `>= {item['minimum']}` {state}"
            )
    checks_text = "\n".join(lines)
    return f"""# Job Radar Latency Regression

## 結論
- Gate 狀態：`{summary['status']}`
- 判斷：{summary['verdict']}

## Checks
{checks_text}

## Source Summaries
- Assistant summary：`{summary['assistant_summary_path']}`
- Retrieval summary：`{summary['retrieval_summary_path']}`
- Resume summary：`{summary['resume_summary_path']}`
- Resume warm summary：`{summary['resume_warm_summary_path']}`
"""
