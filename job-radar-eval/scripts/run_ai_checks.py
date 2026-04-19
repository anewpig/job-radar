#!/usr/bin/env python3
"""執行 Job Radar 的整合 AI checks。"""

from __future__ import annotations

import argparse
from datetime import datetime
import platform
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.assistant_eval import evaluate_assistant
from job_radar_eval.config import build_config, ensure_project_importable
from job_radar_eval.experiment_artifacts import (
    build_experiment_manifest,
    write_case_exports,
    write_experiment_manifest,
)
from job_radar_eval.real_snapshot_eval import (
    build_real_snapshot_report,
    build_snapshot_health,
    evaluate_real_assistant,
    evaluate_real_resume,
    evaluate_real_retrieval,
)
from job_radar_eval.reporting import (
    build_ai_checks_report,
    build_markdown_report,
    build_run_dir,
    build_snapshot_health_gate,
    write_json,
)
from job_radar_eval.resume_eval import evaluate_resume
from job_radar_eval.resume_label_eval import evaluate_resume_labels
from job_radar_eval.retrieval_eval import evaluate_retrieval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar 整合 AI checks")
    parser.add_argument("--baseline-iterations", type=int, default=5, help="fixture baseline 重跑次數")
    parser.add_argument("--real-iterations", type=int, default=3, help="real snapshot 重跑次數")
    parser.add_argument("--snapshot-path", type=Path, default=None, help="指定要評估的 jobs_latest.json 路徑")
    return parser.parse_args()


def _write_single_eval_bundle(
    run_dir: Path,
    name: str,
    summary: dict,
    report: str,
    *,
    config,
    cli_args: dict,
    source_paths: dict[str, Path | str] | None = None,
    snapshot_path: Path | None = None,
) -> dict:
    bundle_dir = run_dir / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    summary_path = bundle_dir / "summary.json"
    report_path = bundle_dir / "report.md"
    write_json(summary_path, summary)
    case_sections = {}
    if "assistant" in summary:
        case_sections["assistant"] = summary["assistant"]["rows"]
    if "resume" in summary:
        case_sections["resume"] = summary["resume"]["rows"]
    if "retrieval" in summary:
        case_sections["retrieval"] = summary["retrieval"]["rows"]
    if "resume_label" in summary:
        case_sections["resume_label"] = summary["resume_label"]["rows"]
    case_exports = write_case_exports(run_dir=bundle_dir, case_sections=case_sections)
    report_path.write_text(report, encoding="utf-8")
    bundle_manifest = build_experiment_manifest(
        config=config,
        run_name=f"ai_checks/{name}",
        run_dir=bundle_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=cli_args,
        source_paths=source_paths,
        snapshot_path=snapshot_path,
        case_exports=case_exports,
    )
    write_experiment_manifest(bundle_dir / "manifest.json", bundle_manifest)
    return {
        "name": name,
        "dir": str(bundle_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "report_path": str(report_path.resolve()),
        "case_exports": case_exports,
    }


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)
    snapshot_path = args.snapshot_path.resolve() if args.snapshot_path else config.snapshot_path
    run_dir = build_run_dir(config.results_dir, prefix="ai_checks")
    run_cache_dir = run_dir / ".cache"

    baseline_assistant = evaluate_assistant(
        config,
        iterations=args.baseline_iterations,
        cache_dir=run_cache_dir / "baseline" / "assistant",
    )
    baseline_resume = evaluate_resume(
        config,
        iterations=args.baseline_iterations,
        cache_dir=run_cache_dir / "baseline" / "resume",
    )
    baseline_retrieval = evaluate_retrieval(
        config,
        iterations=args.baseline_iterations,
        cache_dir=run_cache_dir / "baseline" / "retrieval",
    )
    baseline_resume_label = evaluate_resume_labels(
        config,
        iterations=args.baseline_iterations,
        cache_dir=run_cache_dir / "baseline" / "resume_label",
    )
    baseline_summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "baseline",
        "iterations": args.baseline_iterations,
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "assistant": baseline_assistant,
        "resume": baseline_resume,
        "resume_label": baseline_resume_label,
        "retrieval": baseline_retrieval,
    }

    real_health = build_snapshot_health(config, snapshot_path=snapshot_path)
    real_health_gate = build_snapshot_health_gate(real_health)
    real_assistant = evaluate_real_assistant(
        config,
        iterations=args.real_iterations,
        cache_dir=run_cache_dir / "real_snapshot" / "assistant",
        snapshot_path=snapshot_path,
    )
    real_resume = evaluate_real_resume(
        config,
        iterations=args.real_iterations,
        cache_dir=run_cache_dir / "real_snapshot" / "resume",
        snapshot_path=snapshot_path,
    )
    real_retrieval = evaluate_real_retrieval(
        config,
        iterations=args.real_iterations,
        cache_dir=run_cache_dir / "real_snapshot" / "retrieval",
        snapshot_path=snapshot_path,
    )
    real_summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "real_snapshot_eval",
        "iterations": args.real_iterations,
        "project_root": str(config.project_root),
        "snapshot_path": str(snapshot_path),
        "python_version": sys.version,
        "platform": platform.platform(),
        "snapshot_health": real_health,
        "snapshot_health_gate": real_health_gate,
        "assistant": real_assistant,
        "resume": real_resume,
        "retrieval": real_retrieval,
    }

    combined_summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "ai_checks",
        "project_root": str(config.project_root),
        "snapshot_path": str(snapshot_path),
        "python_version": sys.version,
        "platform": platform.platform(),
        "baseline_iterations": args.baseline_iterations,
        "real_snapshot_iterations": args.real_iterations,
        "baseline": baseline_summary,
        "real_snapshot": real_summary,
    }

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, combined_summary)
    report_path.write_text(build_ai_checks_report(combined_summary), encoding="utf-8")
    baseline_bundle = _write_single_eval_bundle(
        run_dir,
        "baseline",
        baseline_summary,
        build_markdown_report(baseline_summary),
        config=config,
        cli_args=vars(args),
        snapshot_path=snapshot_path,
    )
    real_bundle = _write_single_eval_bundle(
        run_dir,
        "real_snapshot",
        real_summary,
        build_real_snapshot_report(real_summary),
        config=config,
        cli_args=vars(args),
        snapshot_path=snapshot_path,
        source_paths={"snapshot_path": snapshot_path},
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name="ai_checks",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        snapshot_path=snapshot_path,
        bundle_manifests=[baseline_bundle, real_bundle],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
