#!/usr/bin/env python3
"""執行 Job Radar 的真實模型評估。"""

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
from job_radar_eval.config import (
    build_config,
    build_model_config,
    ensure_project_importable,
    require_real_model_config,
)
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
from job_radar_eval.retrieval_eval import evaluate_retrieval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar 真實模型評估")
    parser.add_argument(
        "--profile",
        choices=["pilot", "full"],
        default="full",
        help="執行設定：pilot 走小樣本快速檢查，full 跑完整評估。",
    )
    parser.add_argument("--fixture-iterations", type=int, default=1, help="fixture eval 重跑次數")
    parser.add_argument("--real-iterations", type=int, default=1, help="real snapshot eval 重跑次數")
    parser.add_argument("--snapshot-path", type=Path, default=None, help="指定要評估的 jobs_latest.json 路徑")
    parser.add_argument(
        "--checks",
        type=str,
        default="assistant,resume,retrieval",
        help="要執行的檢查，逗號分隔：assistant,resume,retrieval",
    )
    parser.add_argument("--fixture-case-limit", type=int, default=None, help="限制 fixture case 數")
    parser.add_argument("--real-case-limit", type=int, default=None, help="限制 real snapshot case 數")
    return parser.parse_args()


def _resolve_case_limits(args: argparse.Namespace) -> tuple[int | None, int | None]:
    fixture_case_limit = args.fixture_case_limit
    real_case_limit = args.real_case_limit
    if args.profile == "pilot":
        if fixture_case_limit is None:
            fixture_case_limit = 18
        if real_case_limit is None:
            real_case_limit = 8
    return fixture_case_limit, real_case_limit


def _write_single_eval_bundle(
    run_dir: Path,
    name: str,
    summary: dict,
    report: str,
    *,
    config,
    cli_args: dict,
    model_config: dict,
    snapshot_path: Path | None = None,
) -> dict:
    bundle_dir = run_dir / name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    summary_path = bundle_dir / "summary.json"
    report_path = bundle_dir / "report.md"
    write_json(summary_path, summary)
    case_exports = write_case_exports(
        run_dir=bundle_dir,
        case_sections={
            "assistant": summary["assistant"]["rows"],
            "resume": summary["resume"]["rows"],
            "retrieval": summary["retrieval"]["rows"],
        },
    )
    report_path.write_text(report, encoding="utf-8")
    bundle_manifest = build_experiment_manifest(
        config=config,
        run_name=f"real_model_eval/{name}",
        run_dir=bundle_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=cli_args,
        model_config=model_config,
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
    model_config = build_model_config(config.project_root)
    require_real_model_config(model_config)
    snapshot_path = args.snapshot_path.resolve() if args.snapshot_path else config.snapshot_path
    requested_checks = {
        item.strip()
        for item in args.checks.split(",")
        if item.strip()
    }
    fixture_case_limit, real_case_limit = _resolve_case_limits(args)
    run_dir = build_run_dir(config.results_dir, prefix="real_model_eval")
    run_cache_dir = run_dir / ".cache"

    fixture_assistant = {"rows": [], "summary": [], "aggregate": {}}
    fixture_resume = {"rows": [], "summary": [], "aggregate": {}}
    fixture_resume_label = {"rows": [], "summary": [], "aggregate": {}}
    fixture_retrieval = {"rows": [], "summary": [], "aggregate": {}}
    if "assistant" in requested_checks:
        fixture_assistant = evaluate_assistant(
            config,
            iterations=args.fixture_iterations,
            cache_dir=run_cache_dir / "fixture" / "assistant",
            case_limit=fixture_case_limit,
            answer_model=model_config.assistant_model,
            embedding_model=model_config.embedding_model,
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            use_fake_client=False,
        )
    if "resume" in requested_checks:
        fixture_resume = evaluate_resume(
            config,
            iterations=args.fixture_iterations,
            cache_dir=run_cache_dir / "fixture" / "resume",
            case_limit=fixture_case_limit,
            openai_api_key=model_config.openai_api_key,
            openai_base_url=model_config.openai_base_url,
            llm_model=model_config.resume_llm_model,
            title_model=model_config.title_similarity_model,
            embedding_model=model_config.embedding_model,
            use_fake_client=False,
            use_llm=True,
        )
    if "retrieval" in requested_checks:
        fixture_retrieval = evaluate_retrieval(
            config,
            iterations=args.fixture_iterations,
            cache_dir=run_cache_dir / "fixture" / "retrieval",
            case_limit=fixture_case_limit,
            embedding_model=model_config.embedding_model,
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            use_fake_client=False,
        )
    fixture_summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "fixture_real_model_eval",
        "eval_mode": "real model fixture eval",
        "eval_profile": args.profile,
        "iterations": args.fixture_iterations,
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "model_config": {
            "assistant_model": model_config.assistant_model,
            "embedding_model": model_config.embedding_model,
            "resume_llm_model": model_config.resume_llm_model,
            "title_similarity_model": model_config.title_similarity_model,
        },
        "assistant": fixture_assistant,
        "resume": fixture_resume,
        "resume_label": fixture_resume_label,
        "retrieval": fixture_retrieval,
    }

    real_health = build_snapshot_health(config, snapshot_path=snapshot_path)
    real_health_gate = build_snapshot_health_gate(real_health)
    real_assistant = {"rows": [], "summary": [], "aggregate": {}}
    real_resume = {"rows": [], "summary": [], "aggregate": {}}
    real_retrieval = {"rows": [], "summary": [], "aggregate": {}}
    if "assistant" in requested_checks:
        real_assistant = evaluate_real_assistant(
            config,
            iterations=args.real_iterations,
            cache_dir=run_cache_dir / "real_snapshot" / "assistant",
            snapshot_path=snapshot_path,
            case_limit=real_case_limit,
            answer_model=model_config.assistant_model,
            embedding_model=model_config.embedding_model,
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            use_fake_client=False,
        )
    if "resume" in requested_checks:
        real_resume = evaluate_real_resume(
            config,
            iterations=args.real_iterations,
            cache_dir=run_cache_dir / "real_snapshot" / "resume",
            snapshot_path=snapshot_path,
            case_limit=real_case_limit,
            openai_api_key=model_config.openai_api_key,
            openai_base_url=model_config.openai_base_url,
            llm_model=model_config.resume_llm_model,
            title_model=model_config.title_similarity_model,
            embedding_model=model_config.embedding_model,
            use_fake_client=False,
            use_llm=True,
        )
    if "retrieval" in requested_checks:
        real_retrieval = evaluate_real_retrieval(
            config,
            iterations=args.real_iterations,
            cache_dir=run_cache_dir / "real_snapshot" / "retrieval",
            snapshot_path=snapshot_path,
            case_limit=real_case_limit,
            embedding_model=model_config.embedding_model,
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            use_fake_client=False,
        )
    real_summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "real_snapshot_real_model_eval",
        "eval_profile": args.profile,
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
        "mode": "real_model_eval",
        "eval_profile": args.profile,
        "project_root": str(config.project_root),
        "snapshot_path": str(snapshot_path),
        "python_version": sys.version,
        "platform": platform.platform(),
        "fixture_iterations": args.fixture_iterations,
        "real_snapshot_iterations": args.real_iterations,
        "requested_checks": sorted(requested_checks),
        "baseline_label": "Fixture Real-Model Eval",
        "real_snapshot_label": "Real Snapshot Real-Model Eval",
        "model_config": {
            "assistant_model": model_config.assistant_model,
            "embedding_model": model_config.embedding_model,
            "resume_llm_model": model_config.resume_llm_model,
            "title_similarity_model": model_config.title_similarity_model,
            "openai_base_url_configured": bool(model_config.openai_base_url),
        },
        "baseline": fixture_summary,
        "real_snapshot": real_summary,
    }

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, combined_summary)
    report_path.write_text(build_ai_checks_report(combined_summary), encoding="utf-8")
    manifest_model_config = combined_summary["model_config"]
    fixture_bundle = _write_single_eval_bundle(
        run_dir,
        "fixture",
        fixture_summary,
        build_markdown_report(fixture_summary),
        config=config,
        cli_args=vars(args),
        model_config=manifest_model_config,
        snapshot_path=snapshot_path,
    )
    real_bundle = _write_single_eval_bundle(
        run_dir,
        "real_snapshot",
        real_summary,
        build_real_snapshot_report(real_summary),
        config=config,
        cli_args=vars(args),
        model_config=manifest_model_config,
        snapshot_path=snapshot_path,
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name="real_model_eval",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        model_config=manifest_model_config,
        snapshot_path=snapshot_path,
        bundle_manifests=[fixture_bundle, real_bundle],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
