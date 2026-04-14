"""導覽抽屜的前端互動 script。"""

from __future__ import annotations

import streamlit as st


def render_drawer_auto_close_script() -> None:
    """在 drawer 打開時注入 mouseleave 自動收合行為。"""
    st.html(
        """
<script>
(function () {
  const rootWindow = window.parent;
  const doc = rootWindow.document;
  const panelSelector = ".st-key-nav-drawer-panel-shell";
  const toggleSelector = ".st-key-nav-drawer-toggle-shell .stButton > button";
  const closeDelayMs = 90;

  const bindAutoClose = () => {
    const panel = doc.querySelector(panelSelector);
    const toggle = doc.querySelector(toggleSelector);
    if (!panel || !toggle) {
      rootWindow.setTimeout(bindAutoClose, 120);
      return;
    }
    if (panel.dataset.jobRadarAutoCloseBound === "true") {
      return;
    }

    panel.dataset.jobRadarAutoCloseBound = "true";
    let closeTimer = null;

    const clearCloseTimer = () => {
      if (closeTimer !== null) {
        rootWindow.clearTimeout(closeTimer);
        closeTimer = null;
      }
    };

    panel.addEventListener("mouseenter", clearCloseTimer);
    panel.addEventListener("mouseleave", () => {
      clearCloseTimer();
      closeTimer = rootWindow.setTimeout(() => {
        const activePanel = doc.querySelector(panelSelector);
        const activeToggle = doc.querySelector(toggleSelector);
        if (!activePanel || !activeToggle) {
          return;
        }
        activeToggle.click();
      }, closeDelayMs);
    });
  };

  bindAutoClose();
})();
</script>
        """.strip(),
        unsafe_allow_javascript=True,
    )
