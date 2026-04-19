# 評估方法說明

## 目標
本評估框架用來回答兩個問題：
1. 系統是否變快
2. 系統是否變好

## 評估對象
- AI 助理問答流程
- 履歷解析與職缺匹配流程

## 為什麼使用 baseline fixture
若直接用真實 API 與即時職缺資料，結果會受以下因素干擾：
- 模型輸出隨機性
- 網路波動
- 快照內容每日變動
- OpenAI API 延遲波動

因此 baseline 評估先採用：
- 固定的 `MarketSnapshot`
- 固定的履歷文本
- 固定的問題集
- deterministic fake client

這樣可以把比較基準固定住，讓「程式改動本身」成為主要變因。

## 延遲指標
### AI 助理
- `build_chunks_ms`：建立知識片段耗時
- `retrieve_ms`：檢索耗時
- `llm_ms`：模型生成耗時
- `total_ms`：整體耗時

### 履歷分析
- `build_profile_ms`：履歷解析耗時
- `match_jobs_ms`：職缺匹配耗時
- `total_ms`：整體耗時

## 品質代理指標
### AI 助理
- `keyword_recall`：答案是否包含預期關鍵詞
- `citation_ok`：引用數是否達到最低門檻
- `used_chunks`：是否真的使用到檢索內容

### 履歷匹配
- `top1_url_match`：Top1 是否為預期職缺
- `top1_role_match`：Top1 是否為預期角色
- `matched_skill_recall`：命中技能召回率
- `missing_skill_recall`：缺口技能召回率

## 迭代策略
建議每次系統改動後：
1. 先跑一次 baseline
2. 保存 `results/<timestamp>`
3. 對照前一版的 `summary.json` 與 `report.md`
4. 確認沒有出現：
   - 明顯 latency 回退
   - top1 accuracy 下滑
   - keyword recall 明顯下降

## 延伸方向
之後可以再加兩層：
- 真實資料快照評估
- 人工標註題集評估


## Retrieval 評估
- 固定問題與固定知識片段
- 指標包含冷快取延遲、熱快取延遲、Top1 命中率、Recall@K、MRR
