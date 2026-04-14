"""Hybrid salary prediction helpers for specific job cards and assistant answers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
import sqlite3
from statistics import median
from typing import Any, Sequence

import pandas as pd

from .job_cleaning import canonicalize_company, canonicalize_salary, canonicalize_title
from .models import JobListing, SalaryEstimate
from .storage import load_snapshot
from .utils import normalize_text

try:
    import joblib
except Exception:  # noqa: BLE001
    joblib = None

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import Ridge
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    SKLEARN_AVAILABLE = True
except Exception:  # noqa: BLE001
    ColumnTransformer = None
    OneHotEncoder = None
    Pipeline = None
    Ridge = None
    TfidfVectorizer = None
    train_test_split = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False


SALARY_ESTIMATOR_MODEL_VERSION = "salary_estimator.v1"
SALARY_ESTIMATE_DISPLAY_CONFIDENCE = 0.35
MIN_REASONABLE_MONTHLY_SALARY = 20_000
MAX_REASONABLE_MONTHLY_SALARY = 500_000
SALARY_ROUNDING_STEP = 1_000
SALARY_EVIDENCE_LIMIT = 3
TEXT_FEATURE_MAX = 8_000
FEATURE_COLUMNS = [
    "text_blob",
    "source",
    "location",
    "matched_role",
    "skill_count",
    "task_count",
    "description_len",
]
TARGET_COLUMNS = [
    "monthly_salary_low",
    "monthly_salary_high",
]


@dataclass(slots=True)
class SalaryEstimator:
    artifact: dict[str, Any] | None = None
    enabled: bool = True
    disabled_reason: str = ""

    @property
    def available(self) -> bool:
        return bool(
            self.enabled
            and self.artifact is not None
            and self.artifact.get("low_pipeline") is not None
            and self.artifact.get("high_pipeline") is not None
        )

    @property
    def model_version(self) -> str:
        if not self.artifact:
            return ""
        return str(self.artifact.get("model_version") or "")

    def estimate_job(self, job: JobListing) -> SalaryEstimate:
        if job.salary.strip():
            return SalaryEstimate(
                model_version=self.model_version,
                fallback_reason="has_actual_salary",
            )
        if not self.enabled:
            return SalaryEstimate(fallback_reason=self.disabled_reason or "disabled")
        if not self.available:
            return SalaryEstimate(
                model_version=self.model_version,
                fallback_reason=self.disabled_reason or "model_unavailable",
            )

        row = build_feature_row(job)
        if not _has_enough_features(row):
            return SalaryEstimate(
                model_version=self.model_version,
                fallback_reason="insufficient_features",
            )

        frame = pd.DataFrame([row], columns=FEATURE_COLUMNS)
        low_pipeline = self.artifact["low_pipeline"]
        high_pipeline = self.artifact["high_pipeline"]
        predicted_low = float(low_pipeline.predict(frame)[0])
        predicted_high = float(high_pipeline.predict(frame)[0])
        monthly_low, monthly_high = normalize_predicted_salary_range(
            predicted_low,
            predicted_high,
        )
        if monthly_low <= 0 and monthly_high <= 0:
            return SalaryEstimate(
                model_version=self.model_version,
                fallback_reason="invalid_prediction",
            )

        evidence_rows = self._select_evidence_rows(frame.iloc[0]["text_blob"])
        evidence_job_urls = [str(item.get("url") or "").strip() for item in evidence_rows if str(item.get("url") or "").strip()]
        evidence_scores = [float(item.get("similarity") or 0.0) for item in evidence_rows]
        confidence = _confidence_score(
            monthly_low=monthly_low,
            monthly_high=monthly_high,
            evidence_scores=evidence_scores,
        )
        return SalaryEstimate(
            predicted_low=monthly_low,
            predicted_mid=((monthly_low + monthly_high) // 2),
            predicted_high=monthly_high,
            confidence=confidence,
            evidence_job_urls=evidence_job_urls[:SALARY_EVIDENCE_LIMIT],
            model_version=self.model_version,
            fallback_reason="" if confidence >= SALARY_ESTIMATE_DISPLAY_CONFIDENCE else "low_confidence",
        )

    def evidence_rows(self, urls: Sequence[str]) -> list[dict[str, Any]]:
        if not self.artifact:
            return []
        lookup = self.artifact.get("evidence_lookup") or {}
        rows: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for url in urls:
            normalized_url = str(url or "").strip()
            if not normalized_url or normalized_url in seen_urls:
                continue
            payload = lookup.get(normalized_url)
            if not payload:
                continue
            seen_urls.add(normalized_url)
            rows.append(dict(payload))
        return rows

    def _select_evidence_rows(self, text_blob: str) -> list[dict[str, Any]]:
        if not self.artifact or not text_blob.strip():
            return []
        vectorizer = self.artifact.get("evidence_vectorizer")
        evidence_matrix = self.artifact.get("evidence_matrix")
        evidence_rows = self.artifact.get("evidence_rows") or []
        if vectorizer is None or evidence_matrix is None or not evidence_rows:
            return []
        query_vector = vectorizer.transform([text_blob])
        similarities = cosine_similarity(query_vector, evidence_matrix)[0]
        ranked = sorted(
            enumerate(similarities),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        selected: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for index, score in ranked:
            if len(selected) >= SALARY_EVIDENCE_LIMIT:
                break
            if float(score) <= 0:
                break
            row = dict(evidence_rows[index])
            url = str(row.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            row["similarity"] = round(float(score), 4)
            selected.append(row)
        return selected


def parse_salary_to_monthly_range(
    salary: str,
    canonical_salary: str = "",
) -> tuple[int, int] | None:
    canonical = str(canonical_salary or "").strip().lower()
    if not canonical:
        canonical = canonicalize_salary(salary).strip().lower()
    if not canonical or canonical == "negotiable":
        return None
    if canonical.startswith("hourly:"):
        return None

    kind, _, numeric_payload = canonical.partition(":")
    if not numeric_payload:
        return None
    values = [int(chunk) for chunk in numeric_payload.split("-") if chunk.isdigit()]
    if not values:
        return None
    low_value = values[0]
    high_value = values[-1]
    if kind == "annual":
        low_value = round(low_value / 12)
        high_value = round(high_value / 12)
    elif kind != "monthly":
        return None
    low_value, high_value = normalize_predicted_salary_range(low_value, high_value)
    if low_value <= 0 and high_value <= 0:
        return None
    return (low_value, high_value)


def normalize_predicted_salary_range(
    predicted_low: float | int,
    predicted_high: float | int,
) -> tuple[int, int]:
    low_value = max(MIN_REASONABLE_MONTHLY_SALARY, int(round(float(predicted_low or 0))))
    high_value = max(MIN_REASONABLE_MONTHLY_SALARY, int(round(float(predicted_high or 0))))
    low_value = min(low_value, MAX_REASONABLE_MONTHLY_SALARY)
    high_value = min(high_value, MAX_REASONABLE_MONTHLY_SALARY)
    if low_value > high_value:
        low_value, high_value = high_value, low_value
    low_value = _round_salary(low_value)
    high_value = _round_salary(high_value)
    return low_value, max(low_value, high_value)


def format_salary_estimate_label(estimate: SalaryEstimate) -> str:
    if estimate.predicted_low <= 0 and estimate.predicted_high <= 0:
        return "AI 預估薪資"
    if estimate.predicted_low == estimate.predicted_high:
        return f"AI 預估月薪 {estimate.predicted_low:,}"
    return f"AI 預估月薪 {estimate.predicted_low:,}-{estimate.predicted_high:,}"


def should_display_salary_estimate(estimate: SalaryEstimate | None) -> bool:
    if estimate is None:
        return False
    return (
        estimate.fallback_reason == ""
        and float(estimate.confidence or 0.0) >= SALARY_ESTIMATE_DISPLAY_CONFIDENCE
        and estimate.predicted_high > 0
    )


def build_feature_row(job: JobListing) -> dict[str, Any]:
    summary = normalize_text(job.summary)
    description = normalize_text(job.description)
    skills = " ".join(str(item).strip() for item in job.extracted_skills if str(item).strip())
    work_content = " ".join(
        str(item).strip() for item in job.work_content_items if str(item).strip()
    )
    text_blob = normalize_text(
        "\n".join(
            filter(
                None,
                [
                    job.title,
                    job.company,
                    summary,
                    description,
                    skills,
                    work_content,
                ],
            )
        )
    )[:TEXT_FEATURE_MAX]
    return {
        "text_blob": text_blob,
        "source": normalize_text(job.source),
        "location": normalize_text(job.location),
        "matched_role": normalize_text(job.matched_role),
        "skill_count": len([item for item in job.extracted_skills if str(item).strip()]),
        "task_count": len([item for item in job.work_content_items if str(item).strip()]),
        "description_len": len(description),
    }


def build_salary_training_frame(jobs: Sequence[JobListing]) -> pd.DataFrame:
    deduped_rows: dict[str, dict[str, Any]] = {}
    for job in jobs:
        canonical_salary = str((job.metadata or {}).get("canonical_salary") or "").strip()
        salary_range = parse_salary_to_monthly_range(job.salary, canonical_salary)
        if salary_range is None:
            continue
        low_value, high_value = salary_range
        if low_value <= 0 or high_value <= 0:
            continue
        features = build_feature_row(job)
        if not _has_enough_features(features):
            continue
        identity_key = _training_identity(job)
        row = {
            **features,
            "title": job.title,
            "company": job.company,
            "url": job.url,
            "salary": job.salary,
            "monthly_salary_low": low_value,
            "monthly_salary_high": high_value,
            "salary_midpoint": (low_value + high_value) / 2,
        }
        current = deduped_rows.get(identity_key)
        if current is None or _row_richness_score(row) > _row_richness_score(current):
            deduped_rows[identity_key] = row
    return pd.DataFrame(list(deduped_rows.values()))


def load_salary_jobs_from_snapshot(snapshot_path: Path) -> list[JobListing]:
    snapshot = load_snapshot(snapshot_path)
    if snapshot is None:
        return []
    return list(snapshot.jobs)


def load_salary_jobs_from_history(history_db_path: Path) -> list[JobListing]:
    if not history_db_path.exists():
        return []
    jobs: list[JobListing] = []
    with sqlite3.connect(history_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT latest_payload_json
            FROM job_posts
            WHERE latest_payload_json IS NOT NULL
              AND latest_payload_json != ''
            ORDER BY last_seen_at DESC
            """
        ).fetchall()
    for row in rows:
        payload_raw = str(row["latest_payload_json"] or "").strip()
        if not payload_raw:
            continue
        try:
            payload = json.loads(payload_raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            jobs.append(JobListing(**payload))
    return jobs


def train_salary_estimator(
    training_frame: pd.DataFrame,
    *,
    random_state: int = 42,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn 不可用，無法訓練薪資預測模型。")
    if training_frame.empty:
        raise RuntimeError("找不到可訓練的薪資樣本。")

    frame = training_frame.copy().fillna("")
    evaluation = _evaluate_holdout(frame, random_state=random_state)
    low_pipeline = _build_pipeline()
    high_pipeline = _build_pipeline()
    low_pipeline.fit(frame[FEATURE_COLUMNS], frame["monthly_salary_low"])
    high_pipeline.fit(frame[FEATURE_COLUMNS], frame["monthly_salary_high"])

    evidence_vectorizer = TfidfVectorizer(
        max_features=6_000,
        ngram_range=(1, 2),
        min_df=1,
    )
    evidence_matrix = evidence_vectorizer.fit_transform(frame["text_blob"].tolist())
    evidence_rows = frame[
        [
            "url",
            "title",
            "company",
            "source",
            "location",
            "matched_role",
            "salary",
            "monthly_salary_low",
            "monthly_salary_high",
        ]
    ].to_dict(orient="records")
    artifact = {
        "model_version": SALARY_ESTIMATOR_MODEL_VERSION,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "sample_count": int(len(frame)),
        "feature_columns": list(FEATURE_COLUMNS),
        "target_columns": list(TARGET_COLUMNS),
        "low_pipeline": low_pipeline,
        "high_pipeline": high_pipeline,
        "evidence_vectorizer": evidence_vectorizer,
        "evidence_matrix": evidence_matrix,
        "evidence_rows": evidence_rows,
        "evidence_lookup": {
            str(row.get("url") or "").strip(): row
            for row in evidence_rows
            if str(row.get("url") or "").strip()
        },
    }
    metadata = {
        "model_version": SALARY_ESTIMATOR_MODEL_VERSION,
        "trained_at": artifact["trained_at"],
        "sample_count": int(len(frame)),
        "feature_columns": list(FEATURE_COLUMNS),
        "target_columns": list(TARGET_COLUMNS),
        "evaluation": evaluation,
    }
    return artifact, metadata


def save_salary_estimator(
    artifact: dict[str, Any],
    *,
    model_path: Path,
    meta_path: Path | None = None,
) -> None:
    if joblib is None:
        raise RuntimeError("joblib 不可用，無法保存薪資預測模型。")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    effective_meta_path = meta_path or model_path.with_name(f"{model_path.stem}_meta.json")
    metadata = {
        "model_version": artifact.get("model_version", SALARY_ESTIMATOR_MODEL_VERSION),
        "trained_at": artifact.get("trained_at", ""),
        "sample_count": int(artifact.get("sample_count") or 0),
        "feature_columns": artifact.get("feature_columns") or [],
        "target_columns": artifact.get("target_columns") or [],
    }
    effective_meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fit_and_save_salary_estimator(
    jobs: Sequence[JobListing],
    *,
    model_path: Path,
    meta_path: Path | None = None,
) -> dict[str, Any]:
    frame = build_salary_training_frame(jobs)
    artifact, metadata = train_salary_estimator(frame)
    save_salary_estimator(artifact, model_path=model_path, meta_path=meta_path)
    effective_meta_path = meta_path or model_path.with_name(f"{model_path.stem}_meta.json")
    effective_meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metadata


def enrich_jobs_with_salary_estimates(
    jobs: Sequence[JobListing],
    estimator: SalaryEstimator,
) -> int:
    enriched = 0
    if not estimator.available:
        for job in jobs:
            job.salary_estimate = None
        return enriched
    for job in jobs:
        if job.salary.strip():
            job.salary_estimate = None
            continue
        current = job.salary_estimate
        if current is not None and current.model_version == estimator.model_version:
            continue
        estimate = estimator.estimate_job(job)
        job.salary_estimate = estimate if should_display_salary_estimate(estimate) else None
        if job.salary_estimate is not None:
            enriched += 1
    return enriched


def find_specific_salary_job(
    question: str,
    jobs: Sequence[JobListing],
) -> JobListing | None:
    normalized_question = normalize_text(question)
    question_title = canonicalize_title(normalized_question)
    question_company = canonicalize_company(normalized_question)
    has_specific_hint = any(
        token in normalized_question
        for token in ("這個職缺", "這份職缺", "該職缺", "這份工作", "這個工作")
    ) or (
        "職缺" in normalized_question
        and any(token in normalized_question for token in ("這個", "這份", "該"))
    )
    if not normalized_question.strip():
        return None

    scored: list[tuple[float, bool, bool, JobListing]] = []
    for job in jobs:
        title_key = canonicalize_title(job.title)
        company_key = canonicalize_company(job.company)
        role_text = normalize_text(job.matched_role).lower()
        score = 0.0
        title_match = bool(title_key and title_key in question_title)
        company_match = bool(company_key and company_key in question_company)
        if title_match:
            score += 1.0
        if company_match:
            score += 0.6
        if role_text and role_text in normalized_question.lower():
            score += 0.15
        if score > 0:
            scored.append((score, title_match, company_match, job))

    if scored:
        scored.sort(key=lambda item: item[0], reverse=True)
        top_score, title_match, company_match, top_job = scored[0]
        if title_match and company_match:
            return top_job
        if has_specific_hint and title_match:
            return top_job
    if has_specific_hint and len(jobs) == 1:
        return jobs[0]
    return None


def load_salary_training_jobs(
    *,
    snapshot_path: Path,
    history_db_path: Path | None = None,
) -> list[JobListing]:
    jobs = load_salary_jobs_from_snapshot(snapshot_path)
    if history_db_path is not None and history_db_path.exists():
        jobs.extend(load_salary_jobs_from_history(history_db_path))
    return jobs


def load_salary_estimator(
    model_path: str | Path | None,
    *,
    enabled: bool = True,
) -> SalaryEstimator:
    normalized_path = str(Path(model_path).expanduser()) if model_path else ""
    return _load_salary_estimator_cached(normalized_path, bool(enabled))


@lru_cache(maxsize=4)
def _load_salary_estimator_cached(
    model_path: str,
    enabled: bool,
) -> SalaryEstimator:
    if not enabled:
        return SalaryEstimator(enabled=False, disabled_reason="disabled")
    if not model_path:
        return SalaryEstimator(enabled=False, disabled_reason="missing_model_path")
    if joblib is None:
        return SalaryEstimator(enabled=False, disabled_reason="joblib_unavailable")
    if not SKLEARN_AVAILABLE:
        return SalaryEstimator(enabled=False, disabled_reason="sklearn_unavailable")

    path = Path(model_path)
    if not path.exists():
        return SalaryEstimator(enabled=False, disabled_reason="model_not_found")
    try:
        artifact = joblib.load(path)
    except Exception:  # noqa: BLE001
        return SalaryEstimator(enabled=False, disabled_reason="model_load_failed")
    if not isinstance(artifact, dict):
        return SalaryEstimator(enabled=False, disabled_reason="invalid_model_artifact")
    return SalaryEstimator(
        artifact=artifact,
        enabled=True,
        disabled_reason="",
    )


def _build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "features",
                ColumnTransformer(
                    transformers=[
                        (
                            "text",
                            TfidfVectorizer(
                                max_features=8_000,
                                ngram_range=(1, 2),
                                min_df=1,
                            ),
                            "text_blob",
                        ),
                        (
                            "categorical",
                            OneHotEncoder(handle_unknown="ignore"),
                            ["source", "location", "matched_role"],
                        ),
                        (
                            "numeric",
                            "passthrough",
                            ["skill_count", "task_count", "description_len"],
                        ),
                    ]
                ),
            ),
            ("regressor", Ridge(alpha=1.0)),
        ]
    )


def _training_identity(job: JobListing) -> str:
    if job.canonical_identity_key:
        return str(job.canonical_identity_key)
    if job.url:
        return str(job.url)
    if job.source_record_id:
        return str(job.source_record_id)
    return "|".join(
        [
            canonicalize_company(job.company),
            canonicalize_title(job.title),
            normalize_text(job.location).lower(),
        ]
    )


def _row_richness_score(row: dict[str, Any]) -> tuple[int, int, float]:
    return (
        int(len(str(row.get("text_blob") or ""))),
        int(row.get("skill_count") or 0) + int(row.get("task_count") or 0),
        float(row.get("salary_midpoint") or 0.0),
    )


def _round_salary(value: int) -> int:
    return int(round(value / SALARY_ROUNDING_STEP) * SALARY_ROUNDING_STEP)


def _has_enough_features(row: dict[str, Any]) -> bool:
    text_length = len(str(row.get("text_blob") or "").strip())
    return text_length >= 12


def _confidence_score(
    *,
    monthly_low: int,
    monthly_high: int,
    evidence_scores: Sequence[float],
) -> float:
    if not evidence_scores:
        return 0.0
    bounded_scores = [max(0.0, min(1.0, float(score))) for score in evidence_scores]
    average_similarity = sum(bounded_scores) / len(bounded_scores)
    evidence_factor = min(1.0, len(bounded_scores) / SALARY_EVIDENCE_LIMIT)
    interval_width = max(0.0, float(monthly_high - monthly_low))
    midpoint = max(1.0, float(monthly_low + monthly_high) / 2)
    width_penalty = min(0.18, (interval_width / midpoint) * 0.12)
    confidence = (average_similarity * 0.72) + (evidence_factor * 0.23) - width_penalty
    return round(max(0.0, min(0.95, confidence)), 3)


def _evaluate_holdout(
    frame: pd.DataFrame,
    *,
    random_state: int,
) -> dict[str, Any]:
    if len(frame) < 12:
        return {
            "holdout_evaluated": False,
            "reason": "insufficient_samples",
            "sample_count": int(len(frame)),
        }

    train_frame, test_frame = train_test_split(
        frame,
        test_size=0.2,
        random_state=random_state,
    )
    if len(train_frame) < 8 or len(test_frame) < 2:
        return {
            "holdout_evaluated": False,
            "reason": "insufficient_split_samples",
            "sample_count": int(len(frame)),
        }

    low_pipeline = _build_pipeline()
    high_pipeline = _build_pipeline()
    low_pipeline.fit(train_frame[FEATURE_COLUMNS], train_frame["monthly_salary_low"])
    high_pipeline.fit(train_frame[FEATURE_COLUMNS], train_frame["monthly_salary_high"])
    predicted_low = low_pipeline.predict(test_frame[FEATURE_COLUMNS])
    predicted_high = high_pipeline.predict(test_frame[FEATURE_COLUMNS])

    midpoint_errors: list[float] = []
    overlap_hits = 0
    containment_hits = 0
    baseline_errors: list[float] = []

    for index, row in enumerate(test_frame.to_dict(orient="records")):
        pred_low, pred_high = normalize_predicted_salary_range(
            predicted_low[index],
            predicted_high[index],
        )
        actual_low = int(row["monthly_salary_low"])
        actual_high = int(row["monthly_salary_high"])
        actual_mid = (actual_low + actual_high) / 2
        pred_mid = (pred_low + pred_high) / 2
        midpoint_errors.append(abs(pred_mid - actual_mid))
        if max(pred_low, actual_low) <= min(pred_high, actual_high):
            overlap_hits += 1
        if pred_low <= actual_mid <= pred_high:
            containment_hits += 1

        baseline_low, baseline_high = _baseline_salary_prediction(
            train_frame=train_frame,
            matched_role=str(row.get("matched_role") or ""),
            location=str(row.get("location") or ""),
        )
        baseline_mid = (baseline_low + baseline_high) / 2
        baseline_errors.append(abs(baseline_mid - actual_mid))

    midpoint_mae = sum(midpoint_errors) / len(midpoint_errors)
    baseline_mae = sum(baseline_errors) / len(baseline_errors)
    return {
        "holdout_evaluated": True,
        "sample_count": int(len(frame)),
        "train_samples": int(len(train_frame)),
        "test_samples": int(len(test_frame)),
        "midpoint_mae": round(midpoint_mae, 3),
        "baseline_midpoint_mae": round(baseline_mae, 3),
        "interval_overlap_rate": round(overlap_hits / len(test_frame), 4),
        "containment_rate": round(containment_hits / len(test_frame), 4),
        "beats_baseline": bool(midpoint_mae <= baseline_mae),
    }


def _baseline_salary_prediction(
    *,
    train_frame: pd.DataFrame,
    matched_role: str,
    location: str,
) -> tuple[int, int]:
    role_filtered = train_frame[
        train_frame["matched_role"].astype(str) == str(matched_role or "")
    ]
    role_location_filtered = role_filtered[
        role_filtered["location"].astype(str) == str(location or "")
    ]
    baseline_frame = role_location_filtered
    if baseline_frame.empty:
        baseline_frame = role_filtered
    if baseline_frame.empty:
        baseline_frame = train_frame
    low_value = int(median(baseline_frame["monthly_salary_low"].tolist()))
    high_value = int(median(baseline_frame["monthly_salary_high"].tolist()))
    return normalize_predicted_salary_range(low_value, high_value)
