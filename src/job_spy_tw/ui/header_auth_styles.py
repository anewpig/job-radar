"""提供吸頂 Header 與登入對話框的 CSS 片段。"""

# 這個模組不是函式集合，而是把 Header 與登入相關的 CSS 片段集中管理。
# `styles.py` 會把這個字串和其他 style fragment 串起來，再一次注入到 Streamlit 頁面。
HEADER_AUTH_STYLES = """
/* Header 的 fixed 容器：負責讓整條導覽列吸頂。 */
.top-header-fixed {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    pointer-events: none;
}

/* Host 本身不占版面高度，只作為 fixed header 的掛載點。 */
.top-header-host {
    height: 0;
    line-height: 0;
    overflow: visible;
}

/* Header 主外框：控制背景、陰影、邊框與內距。 */
.top-header-shell {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--surface-content-gap);
    margin: 0;
    width: 100%;
    min-height: var(--top-header-height);
    padding: var(--space-2) var(--space-3);
    box-sizing: border-box;
    border-radius: 0;
    border: 1px solid var(--surface-floating-border);
    background: rgba(255,255,255,0.92);
    box-shadow: var(--surface-floating-shadow);
    backdrop-filter: blur(16px);
    pointer-events: auto;
}

/* Header 右上角的柔光裝飾。 */
.top-header-shell::after {
    content: "";
    position: absolute;
    top: -28px;
    right: -28px;
    width: 120px;
    height: 120px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.02) 70%, transparent 100%);
    pointer-events: none;
}

/* 品牌區塊：包含 JR logo、站名與副標。 */
.top-header-brand {
    display: flex;
    align-items: center;
    gap: var(--surface-content-gap-tight);
    min-width: 0;
    padding-left: 3.45rem;
}

/* Header 左側的品牌 logo。 */
.top-header-logo {
    width: 2.7rem;
    height: 2.7rem;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: 900;
    box-shadow: 0 14px 24px rgba(123, 97, 255, 0.20);
    flex-shrink: 0;
}

/* Header 主標文字。 */
.top-header-title {
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
}

/* Header 副標文字。 */
.top-header-subtitle {
    margin-top: var(--space-1);
    color: #756f97;
    font-size: 0.8rem;
    line-height: 1.35;
}

/* 右上角登入 trigger 的定位容器。 */
.st-key-header-auth-trigger-button {
    position: fixed;
    top: 0;
    right: 1rem;
    left: auto;
    transform: none;
    width: auto;
    height: 0;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1001;
    pointer-events: none;
    overflow: visible;
}

/* Streamlit 產生的 auth button wrapper。 */
.st-key-header-auth-trigger-button .stButton {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    min-height: var(--top-header-height);
    padding: 0 var(--space-1) 0 0;
}

/* 真正可點擊的登入文字按鈕。 */
.st-key-header-auth-trigger-button .stButton > button {
    min-height: auto;
    padding: var(--space-1);
    border: none;
    background: transparent;
    box-shadow: none;
    color: #756f97;
    border-radius: 0;
    font-size: 1rem;
    font-weight: 700;
    pointer-events: auto;
}

/* 登入按鈕 hover 保持極簡，不額外畫底色或邊框。 */
.st-key-header-auth-trigger-button .stButton > button:hover {
    color: #756f97;
    border: none;
    background: transparent;
    box-shadow: none;
}

/* Streamlit dialog 外框：控制登入 / 帳號面板的圓角與陰影。 */
[data-testid="stDialog"] [role="dialog"] {
    border-radius: var(--surface-radius-xl) !important;
    border: 1px solid var(--surface-floating-border) !important;
    box-shadow: var(--surface-floating-shadow) !important;
}

/* Dialog 內容的最外層排版容器。 */
.auth-dialog-shell {
    padding: var(--space-1) 0 var(--space-1);
    text-align: center;
}

/* Dialog 上方品牌列。 */
.auth-dialog-brand {
    display: inline-flex;
    align-items: center;
    gap: var(--surface-content-gap-tight);
    justify-content: center;
}

/* Dialog 內的品牌 logo。 */
.auth-dialog-logo {
    width: 3rem;
    height: 3rem;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--control-primary-bg);
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    box-shadow: var(--control-primary-shadow);
}

/* Dialog 主標。 */
.auth-dialog-title {
    font-size: 1.7rem;
    line-height: 1.1;
    font-weight: 800;
    color: var(--text);
}

/* Dialog 副標與說明文字。 */
.auth-dialog-subtitle {
    margin-top: var(--space-1);
    color: #6f6990;
    font-size: 0.92rem;
    line-height: 1.45;
}

/* Dialog 裡的 tab 元件間距與樣式。 */
[data-testid="stDialog"] [data-testid="stTabs"] {
    margin-top: var(--space-2);
}

[data-testid="stDialog"] .stTabs [role="tablist"] {
    gap: var(--space-1);
}

[data-testid="stDialog"] .stTabs [role="tab"] {
    border-radius: 999px;
    padding-inline: 1rem;
}

[data-testid="stDialog"] .stTabs [aria-selected="true"] {
    background: rgba(123, 97, 255, 0.10);
    color: #5e49cf;
}

/* 窄視窗下微調 header 高度、品牌區與登入按鈕位置。 */
@media (max-width: 960px) {
    :root {
        --top-header-height: var(--space-17);
    }

    .top-header-shell {
        width: 100%;
        padding-right: calc(var(--space-18) + var(--space-1));
    }

    .top-header-subtitle {
        font-size: 0.74rem;
        line-height: 1.3;
    }

    .top-header-brand {
        padding-left: 3.3rem;
    }

    .st-key-header-auth-trigger-button {
        right: var(--space-1);
        width: auto;
    }

    .st-key-header-auth-trigger-button .stButton {
        padding: 0 var(--space-1) 0 0;
    }

    .st-key-header-auth-trigger-button .stButton > button {
        font-size: 0.94rem;
    }
}
"""
