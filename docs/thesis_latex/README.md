# Thesis LaTeX Scaffold

這個目錄提供目前論文草稿的 LaTeX 主稿骨架。

## 內容

- `main.tex`
  - 使用 `ctexbook` 作為中文主稿類別
  - 直接載入 `../ai_thesis_master_draft.md`
- `references.bib`
  - 提供 Chapter 2 與主稿引用用到的 BibTeX 基礎條目

## 目前做法

由於當前環境沒有 `pandoc`，也沒有額外的 Markdown 轉 LaTeX 工具，因此這份主稿採用：

1. 先維護 `../ai_thesis_master_draft.md`
2. 由 `main.tex` 透過 `markdown` 套件直接讀入 Markdown 主稿

這讓目前的論文章節、表格與圖插入點先能集中維護在單一主稿中。

## 使用說明

1. 先確認 TeX 發行版有 `ctex` 與 `markdown` 套件。
2. 在這個資料夾內編譯：

```bash
xelatex main.tex
```

若你的論文模板不支援 `markdown` 套件，則改用：

1. 參照 `../ai_thesis_master_draft_merge_order.md`
2. 手動把 `../ai_thesis_master_draft.md` 的內容拆進正式模板章節

## 圖檔

圖檔已放在：

- `../thesis_assets/figure_3_1_system_architecture.svg`
- `../thesis_assets/figure_4_1_evaluation_flow.svg`

## 後續建議

1. 補齊 Chapter 2 的正式文獻引用後，可再逐步把作者年格式轉成 BibTeX + `\cite{}`。
2. 若後續安裝 `pandoc`，可改成自動轉稿流程。
