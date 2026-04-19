#!/usr/bin/env python3
"""執行 Job Radar resume warm-path latency probe。"""

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
from job_radar_eval.reporting import build_run_dir, write_json
from job_radar_eval.resume_warm_probe import evaluate_resume_warm_probe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar resume warm-path probe")
    parser.add_argument("--case-limit", type=int, default=None, help="限制測例數")
    parser.add_argument("--use-fake-client", action="store_true", help="使用 fake client，不打真實模型 API")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)
    model_config = build_model_config(config.project_root)
    if not args.use_fake_client:
        require_real_model_config(model_config)

    run_dir = build_run_dir(config.results_dir, prefix="resume_warm_probe")
    summary = evaluate_resume_warm_probe(
        config,
        cache_dir=run_dir / ".cache" / "resume_warm_probe",
        case_limit=args.case_limit,
        openai_api_key=model_config.openai_api_key,
        openai_base_url=model_config.openai_base_url,
        llm_model=model_config.resume_llm_model,
        title_model=model_config.title_similarity_model,
        embedding_model=model_config.embedding_model,
        use_fake_client=args.use_fake_client,
    )
    summary.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_root": str(config.project_root),
            "python_version": sys.version,
            "platform": platform.platform(),
            "model_config": {
                "resume_llm_model": model_config.resume_llm_model,
                "title_similarity_model": model_config.title_similarity_model,
                "embedding_model": model_config.embedding_model,
                "use_fake_client": args.use_fake_client,
            },
        }
    )

    summary_path = run_dir / "summary.json"
    write_json(summary_path, summary)
    case_exports = write_case_exports(
        run_dir=run_dir,
        case_sections={"resume_warm_probe": summary["rows"]},
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name="resume_warm_probe",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=summary_path,
        cli_args=vars(args),
        model_config=summary.get("model_config", {}),
        case_exports=case_exports,
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] cases:   {run_dir / 'resume_warm_probe_cases.csv'}")


if __name__ == "__main__":
    main()
