#!/usr/bin/env python3
"""建立 post-training human review / failure analysis manifest。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest, write_jsonl
from job_radar_eval.post_training import REVIEW_RUN_PREFIX, build_review_manifest
from job_radar_eval.reporting import build_run_dir, write_csv, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="建立 post-training review manifest")
    parser.add_argument("--review-summary", type=Path, required=True, help="formal_human_review summary.json")
    parser.add_argument("--comparison-summary", type=Path, required=True, help="post-training eval comparison summary.json")
    parser.add_argument("--dpo-summary", type=Path, required=True, help="post-training dpo summary.json")
    parser.add_argument("--artifact-repo", type=str, default="", help="若提供，會把 review manifest 上傳到此 dataset repo")
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_report(summary: dict) -> str:
    aggregate = summary.get("aggregate", {})
    failure = summary.get("failure_analysis", {})
    return f"""# Post-Training Review Manifest

- Generated at: `{summary.get('generated_at', '')}`
- Dataset version: `{summary.get('dataset_version', '')}`
- Reviewed rows: `{aggregate.get('reviewed_row_count', 0)}`
- Case count: `{aggregate.get('case_count', 0)}`
- Overall score mean: `{aggregate.get('overall_score_mean', 0.0)}`
- Pairwise verdict agreement: `{aggregate.get('pairwise_verdict_agreement_rate', 0.0)}`
- Cohen's kappa: `{aggregate.get('cohens_kappa_verdict', 0.0)}`
- Worst delta mode: `{failure.get('mode_with_worst_delta', '')}`
"""


def _upload_review_artifacts(
    *,
    artifact_repo: str,
    dataset_version: str,
    files: dict[str, Path],
) -> dict[str, str]:
    from huggingface_hub import HfApi

    api = HfApi()
    uploads: dict[str, str] = {}
    for name, local_path in files.items():
        for remote_path in (
            f"review/{dataset_version}/{name}",
            f"review/latest/{name}",
        ):
            api.upload_file(
                path_or_fileobj=str(local_path.resolve()),
                path_in_repo=remote_path,
                repo_id=artifact_repo,
                repo_type="dataset",
                commit_message=f"Upload post-training review artifact {name}",
            )
            uploads[remote_path] = f"https://huggingface.co/datasets/{artifact_repo}/resolve/main/{remote_path}"
    return uploads


def main() -> None:
    args = parse_args()
    config = build_config()
    run_dir = build_run_dir(config.results_dir, prefix=REVIEW_RUN_PREFIX)

    summary = build_review_manifest(
        review_summary=_load_json(args.review_summary.resolve()),
        comparison_manifest=_load_json(args.comparison_summary.resolve()),
        dpo_manifest=_load_json(args.dpo_summary.resolve()),
    )

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    review_rows_jsonl_path = run_dir / "review_rows.jsonl"
    review_rows_csv_path = run_dir / "review_rows.csv"
    case_rows_jsonl_path = run_dir / "review_case_rows.jsonl"
    case_rows_csv_path = run_dir / "review_case_rows.csv"

    write_json(summary_path, summary)
    write_jsonl(review_rows_jsonl_path, summary.get("review_rows", []))
    write_csv(review_rows_csv_path, summary.get("review_rows", []))
    write_jsonl(case_rows_jsonl_path, summary.get("case_rows", []))
    write_csv(case_rows_csv_path, summary.get("case_rows", []))
    report_path.write_text(_build_report(summary), encoding="utf-8")

    manifest = build_experiment_manifest(
        config=config,
        run_name=REVIEW_RUN_PREFIX,
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args={key: str(value) for key, value in vars(args).items()},
        extra_artifacts=[
            {
                "name": "review_rows_jsonl",
                "path": str(review_rows_jsonl_path.resolve()),
                "row_count": len(summary.get("review_rows", [])),
            },
            {
                "name": "review_rows_csv",
                "path": str(review_rows_csv_path.resolve()),
                "row_count": len(summary.get("review_rows", [])),
            },
            {
                "name": "review_case_rows_jsonl",
                "path": str(case_rows_jsonl_path.resolve()),
                "row_count": len(summary.get("case_rows", [])),
            },
            {
                "name": "review_case_rows_csv",
                "path": str(case_rows_csv_path.resolve()),
                "row_count": len(summary.get("case_rows", [])),
            },
        ],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    upload_urls: dict[str, str] = {}
    if args.artifact_repo.strip():
        upload_urls = _upload_review_artifacts(
            artifact_repo=args.artifact_repo.strip(),
            dataset_version=str(summary.get("dataset_version", "")).strip() or "review-manifest",
            files={
                "summary.json": summary_path,
                "report.md": report_path,
                "manifest.json": run_dir / "manifest.json",
                review_rows_jsonl_path.name: review_rows_jsonl_path,
                review_rows_csv_path.name: review_rows_csv_path,
                case_rows_jsonl_path.name: case_rows_jsonl_path,
                case_rows_csv_path.name: case_rows_csv_path,
            },
        )

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] rows:    {review_rows_jsonl_path}")
    if upload_urls:
        print("[done] uploaded:")
        print(json.dumps(upload_urls, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
