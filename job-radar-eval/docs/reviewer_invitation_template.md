# Reviewer Invitation Template

下面這段可以直接發給 reviewer。  
只要把檔名與截止時間改掉就能用。

---

主旨：
`Job Radar assistant human review 邀請`

內容：

你好，

我目前在做一份和求職 AI 助理相關的研究，需要請你協助人工評分一小批回答品質樣本。

這次評分的重點是：
- 回答是否正確
- 回答是否有被引用證據支撐
- 回答是否對求職者有實際幫助
- 回答是否清楚易讀

你會收到兩個檔案：
- `assistant_review_<reviewer_id>.csv`
- `human_review_rubric.md`

請你只修改 CSV 裡這幾個欄位：
- `reviewer_id`
- `correctness_score`
- `grounding_score`
- `usefulness_score`
- `clarity_score`
- `overall_score`
- `verdict`
- `notes`

其餘欄位不要修改。

評分規則請直接看附件 `human_review_rubric.md`。

建議回傳方式：
- 保持 CSV 格式
- 保持 UTF-8
- 不要刪列
- 不要改欄位順序

回傳期限：
- `<deadline>`

如果有欄位看不懂，或你懷疑檔案格式有問題，直接回覆我即可。

謝謝。

---

建議附檔：
- `assistant_review_r1.csv` 或 `assistant_review_r2.csv`
- `human_review_rubric.md`
- 可選：`formal_human_review_workflow.md`
