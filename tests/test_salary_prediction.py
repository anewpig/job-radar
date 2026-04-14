"""Tests for salary prediction helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.job_cleaning import canonicalize_salary
from job_spy_tw.models import JobListing
from job_spy_tw.salary_prediction import (
    SKLEARN_AVAILABLE,
    build_salary_training_frame,
    load_salary_estimator,
    normalize_predicted_salary_range,
    parse_salary_to_monthly_range,
    save_salary_estimator,
    train_salary_estimator,
)


def _build_job(
    *,
    index: int,
    title: str = "AI工程師",
    company: str | None = None,
    location: str = "台北市",
    salary: str | None = None,
    matched_role: str = "AI工程師",
    canonical_identity_key: str = "",
    summary: str = "",
    description: str = "",
) -> JobListing:
    company_name = company or f"Example {index}"
    effective_salary = (
        f"月薪 {60_000 + index * 1_000:,} - {75_000 + index * 1_000:,}"
        if salary is None
        else salary
    )
    return JobListing(
        source="104" if index % 2 == 0 else "1111",
        title=title,
        company=company_name,
        location=location,
        url=f"https://example.com/jobs/{index}",
        salary=effective_salary,
        matched_role=matched_role,
        summary=summary or f"負責 {title} 與 RAG/LLM 功能開發 {index}",
        description=description or f"Python LLM RAG API 整合與部署經驗 {index}",
        extracted_skills=["Python", "LLM", f"Skill{index}"],
        work_content_items=["模型服務串接", f"資料流程維運 {index}"],
        metadata={"canonical_salary": canonicalize_salary(effective_salary)},
        canonical_identity_key=canonical_identity_key,
    )


class SalaryPredictionTests(unittest.TestCase):
    def test_parse_salary_to_monthly_range_supports_monthly_and_annual(self) -> None:
        self.assertEqual(
            parse_salary_to_monthly_range("月薪 60,000 - 80,000"),
            (60_000, 80_000),
        )
        self.assertEqual(
            parse_salary_to_monthly_range("年薪 1,200,000 - 1,800,000"),
            (100_000, 150_000),
        )

    def test_parse_salary_to_monthly_range_excludes_negotiable_and_hourly(self) -> None:
        self.assertIsNone(parse_salary_to_monthly_range("待遇面議"))
        self.assertIsNone(parse_salary_to_monthly_range("時薪 250 - 350"))
        self.assertIsNone(parse_salary_to_monthly_range(""))

    def test_build_salary_training_frame_dedupes_by_canonical_identity(self) -> None:
        jobs = [
            _build_job(
                index=1,
                canonical_identity_key="company|ai|taipei",
                summary="短摘要",
                description="短描述",
            ),
            _build_job(
                index=2,
                canonical_identity_key="company|ai|taipei",
                summary="這是一份更完整的摘要，涵蓋 AI 平台、RAG 與資料流程協作。",
                description="這是一份更完整的描述，文字較長，應該保留下來當訓練樣本。",
            ),
        ]

        frame = build_salary_training_frame(jobs)

        self.assertEqual(len(frame), 1)
        self.assertIn("更完整的摘要", frame.iloc[0]["text_blob"])

    def test_normalize_predicted_salary_range_orders_low_high(self) -> None:
        self.assertEqual(
            normalize_predicted_salary_range(88_800, 66_200),
            (66_000, 89_000),
        )

    @unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn unavailable")
    def test_train_save_load_round_trip(self) -> None:
        jobs = [_build_job(index=index) for index in range(1, 14)]
        frame = build_salary_training_frame(jobs)

        artifact, metadata = train_salary_estimator(frame)
        self.assertEqual(metadata["model_version"], "salary_estimator.v1")
        self.assertGreaterEqual(int(metadata["sample_count"]), 12)

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "salary_estimator.joblib"
            meta_path = Path(temp_dir) / "salary_estimator_meta.json"
            save_salary_estimator(
                artifact,
                model_path=model_path,
                meta_path=meta_path,
            )
            estimator = load_salary_estimator(model_path, enabled=True)
            estimate = estimator.estimate_job(
                _build_job(
                    index=101,
                    salary="",
                    summary="AI平台工程，負責 RAG、LLM API 與資料整理。",
                    description="需要 Python、向量檢索、模型服務整合能力。",
                )
            )

        self.assertTrue(estimator.available)
        self.assertLessEqual(estimate.predicted_low, estimate.predicted_high)
        self.assertEqual(estimate.model_version, "salary_estimator.v1")
        self.assertGreaterEqual(estimate.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
