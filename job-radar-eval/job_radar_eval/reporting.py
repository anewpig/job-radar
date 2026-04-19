"""結果落盤與 Markdown 報告生成。"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


SNAPSHOT_HEALTH_GATE = {
    "jobs_count": {"minimum": 30, "label": "職缺數", "critical": True},
    "sources_count": {"minimum": 3, "label": "來源數", "critical": True},
    "salary_coverage_rate": {"minimum": 0.10, "label": "薪資覆蓋率", "critical": True},
    "work_content_coverage_rate": {"minimum": 0.70, "label": "工作內容覆蓋率", "critical": False},
    "required_skill_coverage_rate": {"minimum": 0.60, "label": "必備技能覆蓋率", "critical": False},
}


def _aggregate_with_defaults(section: dict, defaults: dict) -> dict:
    aggregate = dict(defaults)
    aggregate.update(section.get("aggregate", {}))
    return aggregate


def _render_mode_breakdown_markdown(title: str, mode_breakdown: dict | None) -> str:
    if not mode_breakdown:
        return ""
    lines = [f"#### {title}"]
    for mode, bucket in mode_breakdown.items():
        lines.append(
            "- "
            f"`{mode}`："
            f"cases={bucket.get('case_count', 0)}，"
            f"avg_ms={bucket.get('total_ms_mean', 0.0)}，"
            f"p95_ms={bucket.get('total_ms_p95', 0.0)}，"
            f"quality={bucket.get('keyword_recall_mean', bucket.get('citation_keyword_recall_mean', bucket.get('structured_output_rate', 0.0)))}"
        )
    return "\n".join(lines) + "\n"


def build_run_dir(results_dir: Path, prefix: str = "baseline") -> Path:
    """建立本次評估的結果資料夾。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = results_dir / f"{prefix}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, payload: dict) -> None:
    """輸出 JSON。"""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    """輸出 CSV。"""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(summary: dict) -> str:
    """產生可直接放進論文或進度報告的 Markdown 摘要。"""
    assistant = _aggregate_with_defaults(summary["assistant"], {
        "total_ms_mean": 0.0,
        "total_ms_p95": 0.0,
        "build_chunks_ms_mean": 0.0,
        "retrieve_ms_mean": 0.0,
        "llm_ms_mean": 0.0,
        "keyword_recall_mean": 0.0,
        "citation_ok_rate": 0.0,
    })
    resume = _aggregate_with_defaults(summary["resume"], {
        "build_profile_ms_mean": 0.0,
        "match_jobs_ms_mean": 0.0,
        "total_ms_mean": 0.0,
        "total_ms_p95": 0.0,
        "top1_url_match_rate": 0.0,
        "top1_role_match_rate": 0.0,
        "matched_skill_recall_mean": 0.0,
        "missing_skill_recall_mean": 0.0,
    })
    retrieval = _aggregate_with_defaults(summary["retrieval"], {
        "cold_ms_mean": 0.0,
        "warm_ms_mean": 0.0,
        "speedup_ratio_mean": 0.0,
        "top1_hit_rate": 0.0,
        "recall_at_k_mean": 0.0,
        "mrr_mean": 0.0,
    })
    eval_mode = summary.get("eval_mode", "deterministic baseline")
    model_config = summary.get("model_config", {})
    model_lines = ""
    if model_config:
        model_lines = "\n".join(
            [
                f"- Assistant model：`{model_config.get('assistant_model', '')}`",
                f"- Embedding model：`{model_config.get('embedding_model', '')}`",
                f"- Resume LLM model：`{model_config.get('resume_llm_model', '')}`",
                f"- Title similarity model：`{model_config.get('title_similarity_model', '')}`",
            ]
        )
        model_lines = f"\n## 模型設定\n{model_lines}\n"
    assistant_mode_breakdown = _render_mode_breakdown_markdown(
        "Assistant 模式拆解",
        summary.get("assistant", {}).get("mode_breakdown"),
    )
    return f"""# Job Radar Eval Report

## 執行資訊
- 產生時間：{summary['generated_at']}
- 主專案：{summary['project_root']}
- 評估模式：{eval_mode}
- 迭代次數：{summary['iterations']}
{model_lines}

## AI 助理結果
- 平均總延遲：`{assistant['total_ms_mean']} ms`
- P95 總延遲：`{assistant['total_ms_p95']} ms`
- 平均 chunk 建立延遲：`{assistant['build_chunks_ms_mean']} ms`
- 平均檢索延遲：`{assistant['retrieve_ms_mean']} ms`
- 平均生成延遲：`{assistant['llm_ms_mean']} ms`
- 平均關鍵詞召回率：`{assistant['keyword_recall_mean']}`
- 平均引用命中率：`{assistant['citation_ok_rate']}`

{assistant_mode_breakdown}

## 履歷匹配結果
- 平均履歷解析延遲：`{resume['build_profile_ms_mean']} ms`
- 平均職缺匹配延遲：`{resume['match_jobs_ms_mean']} ms`
- 平均總延遲：`{resume['total_ms_mean']} ms`
- P95 總延遲：`{resume['total_ms_p95']} ms`
- Top1 URL 正確率：`{resume['top1_url_match_rate']}`
- Top1 角色正確率：`{resume['top1_role_match_rate']}`
- 平均命中技能召回率：`{resume['matched_skill_recall_mean']}`
- 平均缺口技能召回率：`{resume['missing_skill_recall_mean']}`

## Retrieval 結果
- 平均冷快取延遲：`{retrieval['cold_ms_mean']} ms`
- 平均熱快取延遲：`{retrieval['warm_ms_mean']} ms`
- 平均快取加速倍率：`{retrieval['speedup_ratio_mean']}`
- Top1 命中率：`{retrieval['top1_hit_rate']}`
- Recall@K：`{retrieval['recall_at_k_mean']}`
- MRR：`{retrieval['mrr_mean']}`

## 解讀建議
- 若未來優化後 `total_ms_mean` 下降，表示速度有改善。
- 若 `top1_url_match_rate`、`keyword_recall_mean` 下滑，表示品質可能退化。
- 建議每次改版後都把新的 `summary.json` 與前一版做 diff，比較速度與品質是否同步改善。
"""


def build_snapshot_health_gate(health: dict) -> dict:
    """依照快照覆蓋率決定這批真實資料是否適合判讀模型品質。"""
    checks: list[dict] = []
    failed_critical = False
    failed_any = False
    dynamic_role_minimum = max(1, min(3, int(health.get("role_targets_count", 0) or 0)))
    role_rule = {
        "key": "roles_count",
        "label": "角色數",
        "actual": health.get("roles_count"),
        "minimum": dynamic_role_minimum,
        "passed": health.get("roles_count", 0) >= dynamic_role_minimum,
        "critical": True,
    }
    checks.append(role_rule)
    if not role_rule["passed"]:
        failed_any = True
        failed_critical = True

    for key, rule in SNAPSHOT_HEALTH_GATE.items():
        actual = health.get(key)
        minimum = rule["minimum"]
        passed = actual >= minimum
        checks.append(
            {
                "key": key,
                "label": rule["label"],
                "actual": actual,
                "minimum": minimum,
                "passed": passed,
                "critical": rule["critical"],
            }
        )
        if not passed:
            failed_any = True
            if rule["critical"]:
                failed_critical = True

    query_mode = "focused" if dynamic_role_minimum == 1 else "broad"
    if failed_critical:
        status = "BLOCKED"
        verdict = "這批真實快照不足以判讀模型品質，只適合做 smoke check。"
    elif failed_any:
        status = "WARN"
        verdict = "這批真實快照可做趨勢觀察，但不建議據此下模型優化結論。"
    else:
        status = "READY"
        verdict = "這批真實快照覆蓋率足夠，可用來判讀模型品質。"

    failing_labels = [item["label"] for item in checks if not item["passed"]]
    return {
        "status": status,
        "verdict": verdict,
        "query_mode": query_mode,
        "checks": checks,
        "failing_labels": failing_labels,
    }


def build_ai_checks_report(summary: dict) -> str:
    """產生整合 fixture baseline 與 real snapshot 的總報告。"""
    baseline = summary["baseline"]
    real_snapshot = summary["real_snapshot"]
    baseline_label = summary.get("baseline_label", "Fixture Baseline")
    real_snapshot_label = summary.get("real_snapshot_label", "Real Snapshot Smoke")
    model_config = summary.get("model_config", {})
    b_assistant = _aggregate_with_defaults(baseline["assistant"], {
        "keyword_recall_mean": 0.0,
        "citation_ok_rate": 0.0,
        "total_ms_mean": 0.0,
    })
    b_resume = _aggregate_with_defaults(baseline["resume"], {
        "top1_url_match_rate": 0.0,
        "top1_role_match_rate": 0.0,
        "matched_skill_recall_mean": 0.0,
    })
    b_retrieval = _aggregate_with_defaults(baseline["retrieval"], {
        "top1_hit_rate": 0.0,
        "recall_at_k_mean": 0.0,
        "mrr_mean": 0.0,
    })
    b_resume_label = _aggregate_with_defaults(baseline.get("resume_label", {"aggregate": {}}), {
        "top1_best_label_hit_rate": 0.0,
        "top3_relevant_recall_mean": 0.0,
        "top3_reject_free_rate": 0.0,
        "pairwise_order_accuracy_mean": 0.0,
        "ndcg_at_3_mean": 0.0,
    })
    r_assistant = _aggregate_with_defaults(real_snapshot["assistant"], {
        "structured_output_rate": 0.0,
        "citation_ok_rate": 0.0,
        "top_citation_type_hit_rate": 0.0,
        "citation_keyword_recall_mean": 0.0,
        "evidence_sufficiency_rate": 0.0,
        "total_ms_mean": 0.0,
    })
    r_resume = _aggregate_with_defaults(real_snapshot["resume"], {
        "top3_url_hit_rate": 0.0,
        "top1_role_match_rate": 0.0,
        "matched_skill_recall_mean": 0.0,
        "case_count": 0,
    })
    r_retrieval = _aggregate_with_defaults(real_snapshot["retrieval"], {
        "top1_type_hit_rate": 0.0,
        "expected_type_recall_mean": 0.0,
        "cold_ms_mean": 0.0,
        "warm_ms_mean": 0.0,
    })
    health = real_snapshot["snapshot_health"]
    gate = real_snapshot["snapshot_health_gate"]
    gate_lines = "\n".join(
        f"- {item['label']}：`{item['actual']}` / 門檻 `>= {item['minimum']}` {'PASS' if item['passed'] else 'FAIL'}"
        for item in gate["checks"]
    )
    model_lines = ""
    if model_config:
        model_lines = "\n".join(
            [
                f"- Assistant model：`{model_config.get('assistant_model', '')}`",
                f"- Embedding model：`{model_config.get('embedding_model', '')}`",
                f"- Resume LLM model：`{model_config.get('resume_llm_model', '')}`",
                f"- Title similarity model：`{model_config.get('title_similarity_model', '')}`",
            ]
        )
        model_lines = f"\n## 模型設定\n{model_lines}\n"
    baseline_mode_breakdown = _render_mode_breakdown_markdown(
        "Baseline Assistant 模式拆解",
        baseline.get("assistant", {}).get("mode_breakdown"),
    )
    real_mode_breakdown = _render_mode_breakdown_markdown(
        "Real Snapshot Assistant 模式拆解",
        real_snapshot.get("assistant", {}).get("mode_breakdown"),
    )

    baseline_iterations = summary.get("baseline_iterations", summary.get("fixture_iterations", ""))
    real_iterations = summary.get("real_snapshot_iterations", summary.get("real_iterations", ""))

    return f"""# Job Radar AI Checks Report

## 執行資訊
- 產生時間：{summary['generated_at']}
- 主專案：{summary['project_root']}
- Baseline 迭代次數：`{baseline_iterations}`
- Real snapshot 迭代次數：`{real_iterations}`
- 真實快照：{summary['snapshot_path']}
{model_lines}

## {baseline_label}
### Assistant
- 關鍵詞召回率：`{b_assistant['keyword_recall_mean']}`
- 引用命中率：`{b_assistant['citation_ok_rate']}`
- 平均總延遲：`{b_assistant['total_ms_mean']} ms`

{baseline_mode_breakdown}

### Resume
- Top1 URL 正確率：`{b_resume['top1_url_match_rate']}`
- Top1 角色正確率：`{b_resume['top1_role_match_rate']}`
- 命中技能召回率：`{b_resume['matched_skill_recall_mean']}`

### Retrieval
- Top1 命中率：`{b_retrieval['top1_hit_rate']}`
- Recall@K：`{b_retrieval['recall_at_k_mean']}`
- MRR：`{b_retrieval['mrr_mean']}`

### Resume Label Ranking
- Top1 最佳標註命中率：`{b_resume_label['top1_best_label_hit_rate']}`
- Top3 相關職缺召回率：`{b_resume_label['top3_relevant_recall_mean']}`
- Top3 排除 reject 比率：`{b_resume_label['top3_reject_free_rate']}`
- Pairwise 排序正確率：`{b_resume_label['pairwise_order_accuracy_mean']}`
- nDCG@3：`{b_resume_label['ndcg_at_3_mean']}`

## {real_snapshot_label}
### Snapshot Health
- 職缺數：`{health['jobs_count']}`
- 查詢數：`{health['queries_count']}`
- 目標角色數：`{health['role_targets_count']}`
- 來源數：`{health['sources_count']}`
- 角色數：`{health['roles_count']}`
- 薪資覆蓋率：`{health['salary_coverage_rate']}`
- 工作內容覆蓋率：`{health['work_content_coverage_rate']}`
- 必備技能覆蓋率：`{health['required_skill_coverage_rate']}`

### Snapshot Health Gate
- 判定：`{gate['status']}`
- Query 模式：`{gate['query_mode']}`
- 結論：{gate['verdict']}
{gate_lines}

### Assistant
- 結構化輸出率：`{r_assistant['structured_output_rate']}`
- 引用命中率：`{r_assistant['citation_ok_rate']}`
- Top1 引用型別命中率：`{r_assistant['top_citation_type_hit_rate']}`
- 引用關鍵詞召回率：`{r_assistant['citation_keyword_recall_mean']}`
- 證據充分率：`{r_assistant['evidence_sufficiency_rate']}`
- 平均總延遲：`{r_assistant['total_ms_mean']} ms`

{real_mode_breakdown}

### Resume
- Top3 URL 命中率：`{r_resume['top3_url_hit_rate']}`
- Top1 角色命中率：`{r_resume['top1_role_match_rate']}`
- 命中技能召回率：`{r_resume['matched_skill_recall_mean']}`
- 測例數：`{r_resume['case_count']}`

### Retrieval
- Top1 型別命中率：`{r_retrieval['top1_type_hit_rate']}`
- 預期型別召回率：`{r_retrieval['expected_type_recall_mean']}`
- 冷快取平均延遲：`{r_retrieval['cold_ms_mean']} ms`
- 熱快取平均延遲：`{r_retrieval['warm_ms_mean']} ms`

## 判讀
- `fixture baseline` 用來防止 prompt / retrieval / matcher 回歸。
- `real snapshot smoke` 用來驗證真實資料下的 chunk、metadata、citation 與 matching 是否仍成立。
- 若 `Snapshot Health Gate = BLOCKED`，先補資料覆蓋率，不要直接進 fine-tuning。
- 若 `citation_keyword_recall_mean` 或 `evidence_sufficiency_rate` 偏低，優先檢查 citation 是否真的抓到支撐答案的 chunk。
- 若 baseline 漂亮但 real snapshot 差，優先檢查資料覆蓋率與 chunk schema，不要直接進 fine-tuning。
"""


def build_resume_label_report(summary: dict) -> str:
    """產生 resume_match_labels 排序評估報告。"""
    resume = _aggregate_with_defaults(summary["resume_label"], {
        "case_count": 0,
        "label_count": 0,
        "build_profile_ms_mean": 0.0,
        "match_jobs_ms_mean": 0.0,
        "total_ms_mean": 0.0,
        "total_ms_p95": 0.0,
        "top1_best_label_hit_rate": 0.0,
        "top3_relevant_recall_mean": 0.0,
        "top3_reject_free_rate": 0.0,
        "pairwise_order_accuracy_mean": 0.0,
        "ndcg_at_3_mean": 0.0,
    })
    return f"""# Job Radar Resume Label Eval Report

## 執行資訊
- 產生時間：{summary['generated_at']}
- 主專案：{summary['project_root']}
- 迭代次數：{summary['iterations']}

## Resume Label Ranking
- 測例數：`{resume['case_count']}`
- 標註數：`{resume['label_count']}`
- 平均履歷解析延遲：`{resume['build_profile_ms_mean']} ms`
- 平均職缺匹配延遲：`{resume['match_jobs_ms_mean']} ms`
- 平均總延遲：`{resume['total_ms_mean']} ms`
- P95 總延遲：`{resume['total_ms_p95']} ms`
- Top1 最佳標註命中率：`{resume['top1_best_label_hit_rate']}`
- Top3 相關職缺召回率：`{resume['top3_relevant_recall_mean']}`
- Top3 排除 reject 比率：`{resume['top3_reject_free_rate']}`
- Pairwise 排序正確率：`{resume['pairwise_order_accuracy_mean']}`
- nDCG@3：`{resume['ndcg_at_3_mean']}`

## 判讀
- `top1_best_label_hit_rate`：Top1 是否命中同一份履歷下最高等級標註職缺。
- `top3_relevant_recall_mean`：Top3 是否有把 `high/medium` 的相關職缺召回進來。
- `top3_reject_free_rate`：Top3 是否避免把明確 `reject` 的職缺排到前段。
- `pairwise_order_accuracy_mean`：對同一份履歷的標註配對，較高等級職缺是否穩定排在較低等級之前。
- `nDCG@3`：整體前段排序品質的綜合指標，越接近 `1.0` 越好。
"""
