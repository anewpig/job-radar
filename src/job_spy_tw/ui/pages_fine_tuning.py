"""Fine-tuning dashboard page."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from .common import render_section_header
from .page_context import PageContext
from .pages_fine_tuning_data import load_post_training_dashboard_data


SFT_TRAINING_METRICS = [
    "train_loss",
    "eval_loss",
    "learning_rate",
    "grad_norm",
    "epoch",
    "global_step",
    "tokens_per_second",
    "steps_per_second",
    "elapsed_time",
    "max_gpu_memory",
    "best_checkpoint",
]

DPO_TRAINING_METRICS = [
    "train_loss",
    "eval_loss",
    "rewards/chosen",
    "rewards/rejected",
    "rewards/accuracies",
    "rewards/margins",
    "logps/chosen",
    "logps/rejected",
    "learning_rate",
    "grad_norm",
    "epoch",
    "global_step",
    "elapsed_time",
    "max_gpu_memory",
]


def _is_url(value: str) -> bool:
    return str(value or "").startswith(("http://", "https://"))


def _source_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "N/A"
    if _is_url(text):
        return f"[link]({text})"
    return f"`{text}`"


def _render_data_caption(*, sample_size: int, source: str, updated_at: str) -> None:
    source_text = _source_text(source)
    updated_label = updated_at or "N/A"
    st.caption(f"sample_size={sample_size} | source={source_text} | updated_at={updated_label}")


def _to_frame(rows: Any) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    if isinstance(rows, list):
        return pd.DataFrame(rows)
    if isinstance(rows, dict):
        return pd.DataFrame([rows])
    return pd.DataFrame()


def _distribution_frame(mapping: dict[str, Any], *, label_key: str, value_key: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {label_key: str(key), value_key: value}
            for key, value in mapping.items()
        ]
    )


def _metric_table_from_stage_map(stage_map: dict[str, dict[str, Any]]) -> pd.DataFrame:
    records = []
    for metric_name in sorted(
        {
            metric
            for stage_metrics in stage_map.values()
            for metric in stage_metrics.keys()
        }
    ):
        record = {"metric": metric_name}
        for stage_name in ("base", "sft", "dpo"):
            record[stage_name] = stage_map.get(stage_name, {}).get(metric_name)
        records.append(record)
    return pd.DataFrame(records)


def _chart_frame(rows: list[dict[str, Any]], metric_name: str) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "metric_name": row.get("metric_name"),
                "step": row.get("step"),
                "value": row.get("value"),
                "timestamp": row.get("timestamp"),
            }
            for row in rows
            if row.get("metric_name") == metric_name
        ]
    )
    if frame.empty:
        return frame
    frame["step"] = pd.to_numeric(frame["step"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna(subset=["value"])


def _latest_metrics_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        metric_name = str(row.get("metric_name", "")).strip()
        if not metric_name:
            continue
        current = buckets.get(metric_name)
        current_step = current.get("step") if current else None
        next_step = row.get("step")
        if current is None or (next_step is not None and (current_step is None or next_step >= current_step)):
            buckets[metric_name] = row
    latest_rows = [
        {
            "metric_name": metric_name,
            "value": row.get("value"),
            "step": row.get("step"),
            "timestamp": row.get("timestamp"),
        }
        for metric_name, row in sorted(buckets.items())
    ]
    return pd.DataFrame(latest_rows)


def _failure_rows_with_pairs(case_rows: list[dict[str, Any]], dpo_rows: list[dict[str, Any]]) -> pd.DataFrame:
    pair_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in dpo_rows:
        key = (str(row.get("question", "")), str(row.get("answer_mode", "")))
        pair_lookup.setdefault(key, row)

    records = []
    for row in case_rows:
        key = (str(row.get("question", "")), str(row.get("answer_mode", "")))
        pair = pair_lookup.get(key, {})
        record = dict(row)
        record["base_to_dpo_keyword_f1_delta"] = (
            float(row.get("dpo_keyword_f1", 0.0) or 0.0)
            - float(row.get("base_keyword_f1", 0.0) or 0.0)
        )
        record["chosen"] = pair.get("chosen", "")
        record["rejected"] = pair.get("rejected", "")
        record["pair_rule"] = pair.get("pair_rule", "")
        record["chosen_artifact"] = pair.get("chosen_artifact", "")
        record["rejected_artifact"] = pair.get("rejected_artifact", "")
        records.append(record)
    return pd.DataFrame(records)


def _render_bar_chart(frame: pd.DataFrame, x: str, y: str, title: str) -> None:
    if frame.empty:
        st.info("目前沒有資料。")
        return
    chart = (
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{x}:N", sort="-y", title=""),
            y=alt.Y(f"{y}:Q", title=""),
            tooltip=list(frame.columns),
        )
        .properties(height=260, title=title)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_line_chart(frame: pd.DataFrame, metric_name: str) -> None:
    if frame.empty:
        st.info(f"`{metric_name}` 暫無資料。")
        return
    x_field = "step" if frame["step"].notna().any() else "timestamp"
    chart = (
        alt.Chart(frame)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{x_field}:Q" if x_field == "step" else f"{x_field}:T", title=x_field),
            y=alt.Y("value:Q", title="value"),
            tooltip=["metric_name", "step", "value", "timestamp"],
        )
        .properties(height=180, title=metric_name)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_overview_section(dashboard: dict[str, Any]) -> None:
    eval_payload = dashboard["eval_manifest"]["payload"]
    artifact_registry = dashboard["artifact_registry"]
    overall = eval_payload.get("assistant_metrics_overall", {})
    latest_stage = "DPO" if overall.get("dpo") else "SFT" if overall.get("sft") else "Base"
    latest_metrics = overall.get("dpo") or overall.get("sft") or overall.get("base") or {}
    latest_updated_at = max(
        [
            dashboard[key].get("updated_at", "")
            for key in ("sft_manifest", "dpo_manifest", "eval_manifest", "review_manifest", "trackio_sft", "trackio_dpo")
        ]
        or [""]
    )

    cards = st.columns(5, gap="small")
    cards[0].metric("Latest Stage", latest_stage)
    cards[1].metric("Dataset Version", artifact_registry.get("dataset_version", "") or "N/A")
    cards[2].metric("Keyword F1", f"{float(latest_metrics.get('keyword_f1_mean', 0.0) or 0.0):.4f}")
    cards[3].metric("Evidence Sufficiency", f"{float(latest_metrics.get('evidence_sufficiency_rate', 0.0) or 0.0):.4f}")
    cards[4].metric("Latency Mean (ms)", f"{float(latest_metrics.get('total_ms_mean', 0.0) or 0.0):.1f}")

    _render_data_caption(
        sample_size=int(eval_payload.get("sample_size", 0) or 0),
        source=dashboard["eval_manifest"].get("source", ""),
        updated_at=latest_updated_at,
    )

    lineage_rows = [
        {"item": "base_model", "value": artifact_registry.get("base_model", "") or eval_payload.get("base_model", "")},
        {"item": "sft_model", "value": artifact_registry.get("sft_model_repo", "") or eval_payload.get("sft_model", "")},
        {"item": "dpo_model", "value": artifact_registry.get("dpo_model_repo", "") or eval_payload.get("dpo_model", "")},
        {"item": "trackio_project", "value": artifact_registry.get("trackio_project", "")},
        {"item": "latest_sft_run_id", "value": artifact_registry.get("latest_sft_run_id", "")},
        {"item": "latest_dpo_run_id", "value": artifact_registry.get("latest_dpo_run_id", "")},
        {"item": "updated_at", "value": latest_updated_at},
    ]
    st.dataframe(pd.DataFrame(lineage_rows), use_container_width=True, hide_index=True)


def _render_dataset_block(title: str, section: dict[str, Any], *, is_dpo: bool) -> None:
    payload = section.get("payload", {})
    st.subheader(title)
    if not payload:
        st.info("目前沒有可展示的 manifest。")
        return

    if is_dpo:
        metrics = st.columns(4, gap="small")
        metrics[0].metric("Total Pairs", payload.get("total_pairs", 0))
        metrics[1].metric("Unique Prompts", payload.get("unique_prompts", 0))
        metrics[2].metric("Avg Score Gap", payload.get("score_gap_stats", {}).get("avg_score_gap", 0.0))
        metrics[3].metric("Near-Duplicate Rejected", payload.get("near_duplicate_rejected_count", 0))
    else:
        metrics = st.columns(4, gap="small")
        metrics[0].metric("Total Rows", payload.get("total_rows", 0))
        metrics[1].metric("Unique Questions", payload.get("unique_questions", 0))
        metrics[2].metric("Human Review Gold", payload.get("gold_counts", {}).get("human_review_gold_count", 0))
        metrics[3].metric("Avg Answer Chars", payload.get("avg_answer_chars", 0))

    _render_data_caption(
        sample_size=int(section.get("sample_size", 0) or 0),
        source=section.get("source", ""),
        updated_at=section.get("updated_at", ""),
    )

    left, right = st.columns(2, gap="large")
    with left:
        if is_dpo:
            _render_bar_chart(
                _distribution_frame(payload.get("pair_rule_counts", {}), label_key="pair_rule", value_key="count"),
                "pair_rule",
                "count",
                "Pair Rule Distribution",
            )
            _render_bar_chart(
                _distribution_frame(payload.get("chosen_source_distribution", {}), label_key="chosen_source", value_key="count"),
                "chosen_source",
                "count",
                "Chosen Source Distribution",
            )
        else:
            _render_bar_chart(
                _distribution_frame(payload.get("mode_counts", {}), label_key="answer_mode", value_key="count"),
                "answer_mode",
                "count",
                "Mode Distribution",
            )
            _render_bar_chart(
                _distribution_frame(payload.get("citation_count_distribution", {}), label_key="citation_count", value_key="count"),
                "citation_count",
                "count",
                "Citation Count Distribution",
            )
    with right:
        st.dataframe(
            pd.DataFrame(
                [
                    {"metric": "train", "value": payload.get("split_counts", {}).get("train", 0)},
                    {"metric": "val", "value": payload.get("split_counts", {}).get("val", 0)},
                    {"metric": "test", "value": payload.get("split_counts", {}).get("test", 0)},
                    {"metric": "source_artifact_count", "value": payload.get("source_artifact_count", 0)},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("Raw Table", expanded=False):
            st.dataframe(_to_frame(payload.get("rows", [])), use_container_width=True, hide_index=True)


def _render_training_stage(title: str, section: dict[str, Any], metric_names: list[str]) -> None:
    st.subheader(title)
    rows = section.get("rows", [])
    if not rows:
        st.info("目前沒有 live metrics。")
        return
    _render_data_caption(
        sample_size=int(section.get("sample_size", 0) or 0),
        source=section.get("source", ""),
        updated_at=section.get("updated_at", ""),
    )
    st.dataframe(_latest_metrics_table(rows), use_container_width=True, hide_index=True)
    columns = st.columns(3, gap="medium")
    for index, metric_name in enumerate(metric_names):
        with columns[index % 3]:
            _render_line_chart(_chart_frame(rows, metric_name), metric_name)


def _render_evaluation_section(dashboard: dict[str, Any]) -> None:
    payload = dashboard["eval_manifest"]["payload"]
    if not payload:
        st.info("目前沒有 evaluation comparison manifest。")
        return
    overall_frame = _metric_table_from_stage_map(payload.get("assistant_metrics_overall", {}))
    st.subheader("Overall Comparison")
    _render_data_caption(
        sample_size=int(payload.get("sample_size", 0) or 0),
        source=dashboard["eval_manifest"].get("source", ""),
        updated_at=dashboard["eval_manifest"].get("updated_at", ""),
    )
    st.dataframe(overall_frame, use_container_width=True, hide_index=True)

    st.subheader("By Answer Mode")
    mode_rows = []
    for answer_mode, stage_map in payload.get("assistant_metrics_by_mode", {}).items():
        frame = _metric_table_from_stage_map(stage_map)
        if frame.empty:
            continue
        frame.insert(0, "answer_mode", answer_mode)
        mode_rows.extend(frame.to_dict("records"))
    st.dataframe(pd.DataFrame(mode_rows), use_container_width=True, hide_index=True)

    st.subheader("Stage Deltas")
    delta_rows = []
    for delta_name, metrics in payload.get("stage_deltas", {}).items():
        for metric_name, value in metrics.items():
            delta_rows.append({"delta": delta_name, "metric": metric_name, "value": value})
    st.dataframe(pd.DataFrame(delta_rows), use_container_width=True, hide_index=True)

    with st.expander("Per-Case Raw Table", expanded=False):
        st.dataframe(_to_frame(payload.get("assistant_case_rows", [])), use_container_width=True, hide_index=True)


def _render_review_section(dashboard: dict[str, Any]) -> None:
    payload = dashboard["review_manifest"]["payload"]
    if not payload:
        st.info("目前沒有 human review manifest。")
        return
    aggregate = payload.get("aggregate", {})
    cards = st.columns(6, gap="small")
    cards[0].metric("Correctness", aggregate.get("correctness_score_mean", 0.0))
    cards[1].metric("Grounding", aggregate.get("grounding_score_mean", 0.0))
    cards[2].metric("Usefulness", aggregate.get("usefulness_score_mean", 0.0))
    cards[3].metric("Clarity", aggregate.get("clarity_score_mean", 0.0))
    cards[4].metric("Overall", aggregate.get("overall_score_mean", 0.0))
    cards[5].metric("Cohen's Kappa", aggregate.get("cohens_kappa_verdict", 0.0))

    _render_data_caption(
        sample_size=int(aggregate.get("reviewed_row_count", payload.get("sample_size", 0)) or 0),
        source=dashboard["review_manifest"].get("source", ""),
        updated_at=dashboard["review_manifest"].get("updated_at", ""),
    )

    verdict_distribution = aggregate.get("verdict_distribution", {})
    _render_bar_chart(
        _distribution_frame(verdict_distribution, label_key="verdict", value_key="count"),
        "verdict",
        "count",
        "Verdict Distribution",
    )
    with st.expander("Case Rows", expanded=False):
        st.dataframe(_to_frame(payload.get("case_rows", [])), use_container_width=True, hide_index=True)
    with st.expander("Review Rows", expanded=False):
        st.dataframe(_to_frame(payload.get("review_rows", [])), use_container_width=True, hide_index=True)


def _render_failure_section(dashboard: dict[str, Any]) -> None:
    review_payload = dashboard["review_manifest"]["payload"]
    dpo_payload = dashboard["dpo_manifest"]["payload"]
    failure = review_payload.get("failure_analysis", {})
    if not failure:
        st.info("目前沒有 failure analysis。")
        return
    st.metric("Mode with Worst Delta", failure.get("mode_with_worst_delta", "") or "N/A")
    _render_data_caption(
        sample_size=int(review_payload.get("sample_size", 0) or 0),
        source=dashboard["review_manifest"].get("source", ""),
        updated_at=dashboard["review_manifest"].get("updated_at", ""),
    )

    sections = [
        ("Lowest F1 Cases", failure.get("lowest_f1_cases", [])),
        ("Lowest Grounding Cases", failure.get("lowest_grounding_cases", [])),
        ("Lowest Evidence Cases", failure.get("lowest_evidence_cases", [])),
        ("Largest Regression Cases", failure.get("largest_regression_cases", [])),
    ]
    for title, rows in sections:
        with st.expander(title, expanded=False):
            st.dataframe(
                _failure_rows_with_pairs(rows, dpo_payload.get("rows", [])),
                use_container_width=True,
                hide_index=True,
            )

    left, right = st.columns(2, gap="large")
    with left:
        rejection_rows = [
            {"pair_rule": item[0], "count": item[1]}
            for item in failure.get("most_common_rejection_rules", [])
        ]
        st.dataframe(pd.DataFrame(rejection_rows), use_container_width=True, hide_index=True)
    with right:
        note_rows = [
            {"note": item[0], "count": item[1]}
            for item in failure.get("most_common_human_review_notes", [])
        ]
        st.dataframe(pd.DataFrame(note_rows), use_container_width=True, hide_index=True)


def _render_artifacts_section(dashboard: dict[str, Any]) -> None:
    artifact_registry = dashboard["artifact_registry"]
    artifact_rows = [{"artifact": key, "value": value} for key, value in artifact_registry.items()]
    st.dataframe(pd.DataFrame(artifact_rows), use_container_width=True, hide_index=True)

    source_rows = [
        {"name": "sft_manifest", "source": dashboard["sft_manifest"].get("source", "")},
        {"name": "dpo_manifest", "source": dashboard["dpo_manifest"].get("source", "")},
        {"name": "eval_manifest", "source": dashboard["eval_manifest"].get("source", "")},
        {"name": "review_manifest", "source": dashboard["review_manifest"].get("source", "")},
        {"name": "trackio_sft", "source": dashboard["trackio_sft"].get("source", "")},
        {"name": "trackio_dpo", "source": dashboard["trackio_dpo"].get("source", "")},
    ]
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

    raw_tabs = st.tabs(["SFT Rows", "DPO Pairs", "Eval Cases", "Review Rows"])
    with raw_tabs[0]:
        st.dataframe(_to_frame(dashboard["sft_manifest"].get("payload", {}).get("rows", [])), use_container_width=True, hide_index=True)
    with raw_tabs[1]:
        st.dataframe(_to_frame(dashboard["dpo_manifest"].get("payload", {}).get("rows", [])), use_container_width=True, hide_index=True)
    with raw_tabs[2]:
        st.dataframe(_to_frame(dashboard["eval_manifest"].get("payload", {}).get("assistant_case_rows", [])), use_container_width=True, hide_index=True)
    with raw_tabs[3]:
        st.dataframe(_to_frame(dashboard["review_manifest"].get("payload", {}).get("review_rows", [])), use_container_width=True, hide_index=True)


def _render_dashboard_content(ctx: PageContext) -> None:
    _ = ctx
    cache_key = "fine_tuning_dashboard_cache"
    previous = st.session_state.get(cache_key)
    dashboard = load_post_training_dashboard_data(previous_data=previous)
    if dashboard.get("has_any_data"):
        st.session_state[cache_key] = dashboard
    elif previous:
        dashboard = dict(previous)
        dashboard["warnings"] = list(previous.get("warnings", [])) + ["目前抓取不到新資料，顯示上次成功結果。"]

    for warning in dashboard.get("warnings", []):
        st.warning(warning)

    if not dashboard.get("has_any_data") and not dashboard["sft_manifest"].get("payload"):
        st.info("尚未找到 post-training manifests 或 Trackio live metrics。")
        return

    tabs = st.tabs(
        [
            "Overview",
            "Datasets",
            "Training",
            "Evaluation",
            "Human Review",
            "Failure Analysis",
            "Artifacts & Raw Tables",
        ]
    )
    with tabs[0]:
        _render_overview_section(dashboard)
    with tabs[1]:
        _render_dataset_block("SFT Dataset", dashboard["sft_manifest"], is_dpo=False)
        st.divider()
        _render_dataset_block("DPO Dataset", dashboard["dpo_manifest"], is_dpo=True)
    with tabs[2]:
        _render_training_stage("SFT Live Metrics", dashboard["trackio_sft"], SFT_TRAINING_METRICS)
        st.divider()
        _render_training_stage("DPO Live Metrics", dashboard["trackio_dpo"], DPO_TRAINING_METRICS)
    with tabs[3]:
        _render_evaluation_section(dashboard)
    with tabs[4]:
        _render_review_section(dashboard)
    with tabs[5]:
        _render_failure_section(dashboard)
    with tabs[6]:
        _render_artifacts_section(dashboard)


def render_fine_tuning_page(ctx: PageContext) -> None:
    """渲染 LLM post-training dashboard 頁。"""
    render_section_header(
        "LLM Post-Training Results",
        "把 SFT → DPO 的資料集、訓練曲線、benchmark、人評、失敗案例與 artifacts 全量攤開，讓每個數字都能追到來源。",
        "Fine-Tuning",
    )
    st.caption(f"自動刷新：每 30 秒 | page_rendered_at={datetime.now().isoformat(timespec='seconds')}")
    fragment = getattr(st, "fragment", None)
    if callable(fragment):
        @fragment(run_every=30.0)
        def _render_fragment() -> None:
            _render_dashboard_content(ctx)

        _render_fragment()
        return
    _render_dashboard_content(ctx)
