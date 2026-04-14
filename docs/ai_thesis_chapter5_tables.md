# Chapter 5 論文表格版

這份文件將 `Chapter 5` 中最重要的結果整理成論文可直接使用的表格版本。用途包括：

- 直接貼入論文正文
- 後續轉成 Word / LaTeX 表格
- 作為口試簡報的數據表來源

---

## Table 5-1 主線總 Gate 結果

| Gate | Status | 說明 |
| --- | --- | --- |
| Snapshot health gate | `READY` | 真實快照覆蓋率足夠，可用於模型品質判讀 |
| Assistant mode gate | `PASS` | `market_summary`、`personalized_guidance`、`job_comparison` 三種模式皆達標 |
| Human review gate | `PASS` | 正式 reviewer 人評通過 |
| Latency regression | `PASS` | 核心延遲指標均在門檻內 |
| Training readiness | `DEFER` | 品質已達標，但目前沒有足夠證據支持 fine-tuning |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)

---

## Table 5-2 Snapshot Health 結果

| 指標 | 實際值 | 門檻 | 結果 |
| --- | ---: | ---: | --- |
| 角色數 | `1` | `>= 1` | PASS |
| 職缺數 | `34` | `>= 30` | PASS |
| 來源數 | `3` | `>= 3` | PASS |
| 薪資覆蓋率 | `0.3529` | `>= 0.1` | PASS |
| 工作內容覆蓋率 | `0.8824` | `>= 0.7` | PASS |
| 必備技能覆蓋率 | `0.7059` | `>= 0.6` | PASS |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)

---

## Table 5-3 Assistant Mode-Aware Real-Model 結果

| Mode | Case Count | Avg Latency (ms) | Structured Output | Citation Keyword Recall | Evidence Sufficiency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `market_summary` | `6` | `4739.479` | `1.0` | `1.0` | `1.0` |
| `personalized_guidance` | `1` | `4368.892` | `1.0` | `1.0` | `1.0` |
| `job_comparison` | `1` | `5262.343` | `1.0` | `1.0` | `1.0` |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)

---

## Table 5-4 Resume Matching 真實模型結果

| 指標 | 數值 |
| --- | ---: |
| `top3_url_hit_rate` | `1.0` |
| `top1_role_match_rate` | `1.0` |
| `matched_skill_recall_mean` | `0.9688` |
| `build_profile_ms_mean` | `5227.174` |
| `match_jobs_ms_mean` | `4547.125` |
| `total_ms_mean` | `9774.299` |
| `resume_warm_build_profile_ms_mean` | `2.041` |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)

---

## Table 5-5 Resume Label Ranking 結果

| 指標 | 數值 |
| --- | ---: |
| `top1_best_label_hit_rate` | `1.0` |
| `top3_relevant_recall_mean` | `0.8` |
| `top3_reject_free_rate` | `1.0` |
| `pairwise_order_accuracy_mean` | `0.9667` |
| `nDCG@3` | `0.8763` |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)

---

## Table 5-6 Latency Regression 結果

| 指標 | 實際值 (ms) | 門檻 (ms) | 結果 |
| --- | ---: | ---: | --- |
| Assistant total latency | `4758.514` | `<= 8000` | PASS |
| Retrieval cold latency | `1476.403` | `<= 2000` | PASS |
| Retrieval warm latency | `165.345` | `<= 400` | PASS |
| Resume build_profile latency | `5227.174` | `<= 6000` | PASS |
| Resume match_jobs latency | `4547.125` | `<= 7000` | PASS |
| Resume total latency | `9774.299` | `<= 13000` | PASS |
| Resume warm build_profile latency | `2.041` | `<= 250` | PASS |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)

---

## Table 5-7 Formal Human Review 結果

| 指標 | 數值 |
| --- | ---: |
| `reviewer_count` | `2` |
| `case_count` | `8` |
| `correctness_score_mean` | `4.9375` |
| `grounding_score_mean` | `5.0` |
| `usefulness_score_mean` | `5.0` |
| `clarity_score_mean` | `5.0` |
| `overall_score_mean` | `5.0` |
| `pairwise_verdict_agreement_rate` | `1.0` |
| `cohens_kappa_verdict` | `1.0` |

verdict 分布：

| Verdict | Count |
| --- | ---: |
| `accept` | `16` |
| `minor_issue` | `0` |
| `major_issue` | `0` |
| `reject` | `0` |

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)

---

## Table 5-8 評估資料集摘要

| Dataset | Size | 主要用途 |
| --- | ---: | --- |
| `assistant_questions` | `100` | 問答 regression 與 mode-aware 評估 |
| `resume_extraction_labels` | `30` | 履歷抽取與 profile schema 驗證 |
| `resume_match_labels` | `60` | 履歷匹配與排序品質評估 |

來源：

- [ai_mainline_summary.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_mainline_summary.md)
- [ai_eval_dataset_spec.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md)

---

## 論文使用建議

若要精簡 `Chapter 5`，建議至少保留：

1. `Table 5-1` 主線總 Gate 結果
2. `Table 5-3` Assistant Mode-Aware 結果
3. `Table 5-4` Resume Matching 結果
4. `Table 5-6` Latency Regression 結果
5. `Table 5-7` Formal Human Review 結果

若版面足夠，再補：

- `Table 5-2` Snapshot Health
- `Table 5-5` Resume Label Ranking
- `Table 5-8` 評估資料集摘要

---

## 對應章節

- [ai_thesis_chapter5_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_draft.md)
- [ai_thesis_figures_tables_plan.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figures_tables_plan.md)
