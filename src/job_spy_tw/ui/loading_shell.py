"""提供瀏覽器 refresh 首屏的 boot loading overlay。"""

from __future__ import annotations

import json
from collections.abc import Mapping

import streamlit as st

_BOOT_LOADER_ID = "job-radar-boot-loader"
_BOOT_LOADER_STYLE_ID = "job-radar-boot-loader-styles"
_BOOT_LOADER_AUTO_DISMISS_MS = 3200

_BOOT_LOADER_HTML = """
<div class="jr-boot-loader__backdrop"></div>
<div class="jr-boot-loader__card" role="status" aria-live="polite" aria-label="正在整理你的求職工作台">
  <div class="jr-boot-loader__brand-row">
    <div class="jr-boot-loader__logo">JR</div>
    <div class="jr-boot-loader__brand-copy">
      <div class="jr-boot-loader__eyebrow">Job Radar</div>
      <div class="jr-boot-loader__title">職缺雷達</div>
    </div>
  </div>
  <div class="jr-boot-loader__headline">正在整理你的求職工作台</div>
  <div class="jr-boot-loader__subhead">同步搜尋條件、快照與頁面元件</div>
  <div class="jr-boot-loader__radar" aria-hidden="true">
    <div class="jr-boot-loader__radar-ring jr-boot-loader__radar-ring--one"></div>
    <div class="jr-boot-loader__radar-ring jr-boot-loader__radar-ring--two"></div>
    <div class="jr-boot-loader__radar-ring jr-boot-loader__radar-ring--three"></div>
    <div class="jr-boot-loader__radar-sweep"></div>
    <div class="jr-boot-loader__radar-dot"></div>
    <div class="jr-boot-loader__radar-core"></div>
  </div>
</div>
""".strip()

_BOOT_LOADER_CSS = """
#job-radar-boot-loader {
    position: fixed;
    inset: 0;
    z-index: 2147483646;
    display: flex;
    align-items: center;
    justify-content: center;
    padding:
        calc(env(safe-area-inset-top, 0px) + 1.5rem)
        calc(env(safe-area-inset-right, 0px) + 1rem)
        calc(env(safe-area-inset-bottom, 0px) + 1.5rem)
        calc(env(safe-area-inset-left, 0px) + 1rem);
    box-sizing: border-box;
    pointer-events: auto;
    opacity: 1;
    visibility: visible;
    transition: opacity 180ms ease, visibility 180ms ease;
}

#job-radar-boot-loader.is-ready {
    opacity: 0;
    visibility: hidden;
}

#job-radar-boot-loader .jr-boot-loader__backdrop {
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 12% 10%, rgba(255, 215, 126, 0.20) 0%, rgba(255, 215, 126, 0.04) 20%, transparent 42%),
        radial-gradient(circle at 86% 16%, rgba(123, 97, 255, 0.18) 0%, rgba(123, 97, 255, 0.04) 22%, transparent 44%),
        radial-gradient(circle at 50% 100%, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.00) 38%),
        linear-gradient(180deg, #faf7ff 0%, #f3efff 100%);
}

#job-radar-boot-loader .jr-boot-loader__card {
    position: relative;
    z-index: 1;
    width: min(28rem, calc(100vw - 2rem));
    padding: 1.35rem 1.35rem 1.55rem;
    border-radius: 1.9rem;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 245, 255, 0.92) 100%);
    box-shadow:
        0 22px 50px rgba(31, 27, 77, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(18px);
    overflow: hidden;
}

#job-radar-boot-loader .jr-boot-loader__card::before {
    content: "";
    position: absolute;
    inset: auto -3.2rem -4.2rem auto;
    width: 12rem;
    height: 12rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.18) 0%, rgba(123, 97, 255, 0.02) 56%, transparent 78%);
    pointer-events: none;
}

#job-radar-boot-loader .jr-boot-loader__brand-row {
    display: flex;
    align-items: center;
    gap: 0.9rem;
}

#job-radar-boot-loader .jr-boot-loader__logo {
    width: 3.1rem;
    height: 3.1rem;
    border-radius: 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    box-shadow: 0 16px 26px rgba(123, 97, 255, 0.24);
    flex-shrink: 0;
}

#job-radar-boot-loader .jr-boot-loader__brand-copy {
    min-width: 0;
}

#job-radar-boot-loader .jr-boot-loader__eyebrow {
    font-size: 0.72rem;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8a84af;
}

#job-radar-boot-loader .jr-boot-loader__title {
    margin-top: 0.18rem;
    font-size: 1.42rem;
    line-height: 1.1;
    font-weight: 900;
    color: #1f1b4d;
}

#job-radar-boot-loader .jr-boot-loader__headline {
    margin-top: 1.2rem;
    font-size: 1.14rem;
    line-height: 1.35;
    font-weight: 800;
    color: #2b255d;
}

#job-radar-boot-loader .jr-boot-loader__subhead {
    margin-top: 0.38rem;
    font-size: 0.95rem;
    line-height: 1.55;
    font-weight: 600;
    color: #706a96;
}

#job-radar-boot-loader .jr-boot-loader__radar {
    position: relative;
    width: 7rem;
    height: 7rem;
    margin: 1.35rem auto 0;
}

#job-radar-boot-loader .jr-boot-loader__radar-ring {
    position: absolute;
    inset: 0;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.18);
    background: radial-gradient(circle, rgba(123, 97, 255, 0.04) 0%, rgba(123, 97, 255, 0.00) 66%);
}

#job-radar-boot-loader .jr-boot-loader__radar-ring--one {
    animation: jr-boot-loader-pulse 2.1s ease-out infinite;
}

#job-radar-boot-loader .jr-boot-loader__radar-ring--two {
    inset: 0.7rem;
    animation: jr-boot-loader-pulse 2.1s ease-out infinite 0.35s;
}

#job-radar-boot-loader .jr-boot-loader__radar-ring--three {
    inset: 1.4rem;
    animation: jr-boot-loader-pulse 2.1s ease-out infinite 0.7s;
}

#job-radar-boot-loader .jr-boot-loader__radar-sweep {
    position: absolute;
    inset: 0.35rem;
    border-radius: 999px;
    background:
        conic-gradient(
            from 220deg,
            rgba(123, 97, 255, 0.00) 0deg,
            rgba(123, 97, 255, 0.00) 290deg,
            rgba(255, 215, 126, 0.08) 320deg,
            rgba(255, 215, 126, 0.26) 344deg,
            rgba(123, 97, 255, 0.00) 360deg
        );
    filter: blur(0.2px);
    animation: jr-boot-loader-spin 2.4s linear infinite;
}

#job-radar-boot-loader .jr-boot-loader__radar-dot {
    position: absolute;
    top: 1.05rem;
    right: 1.15rem;
    width: 0.7rem;
    height: 0.7rem;
    border-radius: 999px;
    background: #ffd77e;
    box-shadow:
        0 0 0 0 rgba(255, 215, 126, 0.36),
        0 0 20px rgba(255, 215, 126, 0.32);
    animation: jr-boot-loader-dot 1.8s ease-out infinite;
}

#job-radar-boot-loader .jr-boot-loader__radar-core {
    position: absolute;
    inset: calc(50% - 0.55rem);
    border-radius: 999px;
    background: linear-gradient(135deg, #6f56f6 0%, #8c6dff 100%);
    box-shadow:
        0 0 0 0.4rem rgba(123, 97, 255, 0.10),
        0 12px 20px rgba(123, 97, 255, 0.20);
}

@keyframes jr-boot-loader-spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

@keyframes jr-boot-loader-pulse {
    0%,
    100% {
        opacity: 0.4;
        transform: scale(0.98);
    }
    50% {
        opacity: 1;
        transform: scale(1.02);
    }
}

@keyframes jr-boot-loader-dot {
    0% {
        box-shadow:
            0 0 0 0 rgba(255, 215, 126, 0.34),
            0 0 16px rgba(255, 215, 126, 0.24);
    }
    70% {
        box-shadow:
            0 0 0 0.75rem rgba(255, 215, 126, 0.00),
            0 0 22px rgba(255, 215, 126, 0.30);
    }
    100% {
        box-shadow:
            0 0 0 0 rgba(255, 215, 126, 0.00),
            0 0 16px rgba(255, 215, 126, 0.18);
    }
}

@media (max-width: 640px) {
    #job-radar-boot-loader .jr-boot-loader__card {
        width: min(100vw - 1.5rem, 25rem);
        padding: 1.15rem 1.05rem 1.3rem;
        border-radius: 1.5rem;
    }

    #job-radar-boot-loader .jr-boot-loader__logo {
        width: 2.85rem;
        height: 2.85rem;
        border-radius: 0.9rem;
    }

    #job-radar-boot-loader .jr-boot-loader__title {
        font-size: 1.26rem;
    }

    #job-radar-boot-loader .jr-boot-loader__headline {
        font-size: 1.04rem;
    }

    #job-radar-boot-loader .jr-boot-loader__subhead {
        font-size: 0.9rem;
    }

    #job-radar-boot-loader .jr-boot-loader__radar {
        width: 6.4rem;
        height: 6.4rem;
        margin-top: 1.15rem;
    }
}
""".strip()


def should_show_boot_loader(session_state: Mapping[str, object]) -> bool:
    """只在同一個瀏覽器 session 的第一次完整載入顯示 boot loader。"""
    return not bool(session_state.get("_boot_loader_complete"))


def render_boot_loading_overlay() -> None:
    """把 boot loading overlay 注入到 parent document。"""
    st.html(_build_boot_loader_injector(), unsafe_allow_javascript=True)


def dismiss_boot_loading_overlay() -> None:
    """通知前面注入的 boot loading overlay 退場。"""
    st.html(
        """
<script>
(function () {
  const rootWindow = window.parent;
  rootWindow.__jobRadarBootLoaderReady = true;
  if (typeof rootWindow.__jobRadarDismissBootLoader === "function") {
    rootWindow.__jobRadarDismissBootLoader();
  }
})();
</script>
        """.strip(),
        unsafe_allow_javascript=True,
    )


def _build_boot_loader_injector() -> str:
    overlay_html = json.dumps(_BOOT_LOADER_HTML, ensure_ascii=False)
    overlay_css = json.dumps(_BOOT_LOADER_CSS, ensure_ascii=False)
    loader_id = json.dumps(_BOOT_LOADER_ID)
    style_id = json.dumps(_BOOT_LOADER_STYLE_ID)
    auto_dismiss_ms = int(_BOOT_LOADER_AUTO_DISMISS_MS)
    return f"""
<script>
(function () {{
  const rootWindow = window.parent;
  const doc = rootWindow.document;
  const loaderId = {loader_id};
  const styleId = {style_id};
  const overlayHtml = {overlay_html};
  const overlayCss = {overlay_css};
  const autoDismissMs = {auto_dismiss_ms};

  const clearAutoDismissTimer = () => {{
    if (rootWindow.__jobRadarBootLoaderFallbackTimer) {{
      rootWindow.clearTimeout(rootWindow.__jobRadarBootLoaderFallbackTimer);
      rootWindow.__jobRadarBootLoaderFallbackTimer = null;
    }}
  }};

  const ensureStyle = () => {{
    let style = doc.getElementById(styleId);
    if (!style) {{
      style = doc.createElement("style");
      style.id = styleId;
      style.textContent = overlayCss;
      doc.head.appendChild(style);
    }}
    return style;
  }};

  const lockScroll = () => {{
    if (!rootWindow.__jobRadarBootScrollState) {{
      rootWindow.__jobRadarBootScrollState = {{
        htmlOverflow: doc.documentElement.style.overflow,
        bodyOverflow: doc.body ? doc.body.style.overflow : ""
      }};
    }}
    doc.documentElement.style.overflow = "hidden";
    if (doc.body) {{
      doc.body.style.overflow = "hidden";
    }}
  }};

  const unlockScroll = () => {{
    const scrollState = rootWindow.__jobRadarBootScrollState;
    if (!scrollState) {{
      return;
    }}
    doc.documentElement.style.overflow = scrollState.htmlOverflow || "";
    if (doc.body) {{
      doc.body.style.overflow = scrollState.bodyOverflow || "";
    }}
    delete rootWindow.__jobRadarBootScrollState;
  }};

  rootWindow.__jobRadarDismissBootLoader = function () {{
    clearAutoDismissTimer();
    rootWindow.__jobRadarBootLoaderReady = true;
    const overlay = doc.getElementById(loaderId);
    if (!overlay) {{
      unlockScroll();
      const style = doc.getElementById(styleId);
      if (style) {{
        style.remove();
      }}
      return;
    }}
    if (overlay.dataset.dismissed === "true") {{
      return;
    }}
    overlay.dataset.dismissed = "true";
    overlay.classList.add("is-ready");
    rootWindow.setTimeout(function () {{
      const currentOverlay = doc.getElementById(loaderId);
      if (currentOverlay) {{
        currentOverlay.remove();
      }}
      const style = doc.getElementById(styleId);
      if (style) {{
        style.remove();
      }}
      unlockScroll();
    }}, 220);
  }};

  const scheduleAutoDismiss = () => {{
    clearAutoDismissTimer();
    rootWindow.__jobRadarBootLoaderFallbackTimer = rootWindow.setTimeout(function () {{
      if (typeof rootWindow.__jobRadarDismissBootLoader === "function") {{
        rootWindow.__jobRadarDismissBootLoader();
      }}
    }}, autoDismissMs);
  }};

  ensureStyle();
  lockScroll();

  let overlay = doc.getElementById(loaderId);
  if (!overlay) {{
    overlay = doc.createElement("div");
    overlay.id = loaderId;
    overlay.innerHTML = overlayHtml;
    doc.body.appendChild(overlay);
  }}

  overlay.classList.remove("is-ready");
  overlay.dataset.dismissed = "false";
  scheduleAutoDismiss();

  if (rootWindow.__jobRadarBootLoaderReady === true) {{
    rootWindow.__jobRadarDismissBootLoader();
  }}
}})();
</script>
    """.strip()
