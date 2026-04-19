"""Sections for backend operations monitoring page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..backend_operations_service import (
    BackendOperationsSnapshot,
    replay_dead_letter,
    reprocess_failed_job,
)
from .common import render_section_header
from .page_context import PageContext
from .pages_backend_operations_helpers import (
    build_ai_budget_cards,
    build_budget_rows,
    build_cache_rows,
    build_dead_letter_rows,
    build_due_rows,
    build_event_rows,
    build_job_rows,
    build_mode_rows,
    build_snapshot_rows,
    build_summary_cards,
    build_version_breakdown_rows,
    format_relative_time,
    signal_card,
)

OPS_FEEDBACK_MESSAGE_KEY = "backend_ops_feedback_message"
OPS_FEEDBACK_STATUS_KEY = "backend_ops_feedback_status"


def _set_ops_feedback(*, status: str, message: str) -> None:
    st.session_state[OPS_FEEDBACK_STATUS_KEY] = status
    st.session_state[OPS_FEEDBACK_MESSAGE_KEY] = message


def _render_ops_feedback() -> None:
    message = str(st.session_state.get(OPS_FEEDBACK_MESSAGE_KEY, "")).strip()
    status = str(st.session_state.get(OPS_FEEDBACK_STATUS_KEY, "")).strip()
    if not message:
        return
    if status == "error":
        st.error(message)
    else:
        st.success(message)


def inject_ops_styles() -> None:
    """Inject backend operations page-local styles."""
    st.markdown(
        """
<style>
.ops-metric-grid,
.ops-signal-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:0.9rem;
}
.ops-metric-card,
.ops-signal-card,
.ops-note-card {
  border:1px solid rgba(24, 55, 66, 0.12);
  border-radius:22px;
  padding:1rem 1.05rem;
  background:
    radial-gradient(circle at top right, rgba(204, 230, 224, 0.55), transparent 38%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(245,248,248,0.98));
  box-shadow:0 18px 34px rgba(17, 35, 42, 0.06);
}
.ops-metric-card--warn,
.ops-signal-card--warn {
  background:
    radial-gradient(circle at top right, rgba(245, 227, 201, 0.62), transparent 38%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(252,248,241,0.98));
}
.ops-metric-card--risk,
.ops-signal-card--stale {
  background:
    radial-gradient(circle at top right, rgba(245, 214, 209, 0.62), transparent 38%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(252,246,245,0.98));
}
.ops-metric-label,
.ops-metric-detail,
.ops-signal-detail,
.ops-signal-meta {
  color:rgba(60, 75, 81, 0.86);
  font-size:0.85rem;
}
.ops-metric-value {
  color:#16333d;
  font-size:1.5rem;
  font-weight:800;
  margin:0.18rem 0 0.35rem;
}
.ops-signal-head {
  display:flex;
  justify-content:space-between;
  gap:0.75rem;
  align-items:center;
  margin-bottom:0.55rem;
}
.ops-signal-kind,
.ops-signal-status {
  font-size:0.8rem;
  letter-spacing:0.02em;
  text-transform:uppercase;
  font-weight:700;
  color:#17333d;
}
.ops-signal-id {
  color:#16333d;
  font-weight:700;
  margin-bottom:0.45rem;
  word-break:break-all;
}
.ops-dataframe-shell {
  border:1px solid rgba(24, 55, 66, 0.1);
  border-radius:22px;
  padding:0.8rem;
  background:linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,250,0.98));
}
.ops-note-card {
  margin-bottom:1rem;
}
.ops-note-title {
  color:#16333d;
  font-weight:700;
  margin-bottom:0.3rem;
}
.ops-note-body {
  color:rgba(60, 75, 81, 0.88);
  line-height:1.56;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_operations_summary(snapshot: BackendOperationsSnapshot) -> None:
    """Render top-level backend operations summary cards."""
    render_section_header(
        "後端營運面板",
        "這頁是給開發與維運看的，集中看 scheduler、worker、queue、snapshot cache 與 saved-search refresh 的即時狀態。",
        "Backend Operations",
    )
    st.markdown(
        """
<div class="ops-note-card">
  <div class="ops-note-title">用途</div>
  <div class="ops-note-body">一般使用者不需要看 lease、queue 與 runtime heartbeat。這裡保留的是後端執行細節，方便你判斷排程是否有跑、worker 有沒有接手、queue 是否卡住，以及最近一次刷新落在哪個時間點。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ops-metric-grid">{"".join(build_summary_cards(snapshot))}</div>',
        unsafe_allow_html=True,
    )


def render_ai_monitoring_section(ctx: PageContext) -> None:
    """Render AI monitoring, budgets, and recent events."""
    ai_summary = ctx.product_store.summarize_recent_ai_monitoring(
        user_id=ctx.current_user_id,
        limit=200,
    )
    assistant_mode_summary = ctx.product_store.summarize_assistant_modes(
        user_id=ctx.current_user_id,
        limit=500,
    )
    cache_summary = ctx.product_store.summarize_ai_cache_efficiency(
        user_id=ctx.current_user_id,
        limit=500,
    )
    ai_budget = ctx.product_store.evaluate_ai_latency_budgets(
        user_id=ctx.current_user_id,
        limit=500,
    )
    ai_events = ctx.product_store.list_recent_ai_monitoring_events(
        user_id=ctx.current_user_id,
        limit=24,
    )

    render_section_header(
        "AI 監控與 Budget",
        "這裡看 AI 助理與履歷分析的產品級監控。現在已經會記錄事件、延遲、錯誤率與 token budget，可用來做回歸檢查與後續論文實驗紀錄。",
        "AI Monitoring",
    )
    st.markdown(
        f'<div class="ops-metric-grid">{"".join(build_ai_budget_cards(ai_budget, ai_summary))}</div>',
        unsafe_allow_html=True,
    )

    budget_rows = build_budget_rows(ai_budget)
    if budget_rows:
        with st.container(border=True, key="backend-ops-ai-budget-shell"):
            st.markdown("**AI Budget 狀態表**")
            st.dataframe(
                pd.DataFrame(budget_rows),
                use_container_width=True,
                hide_index=True,
            )

    mode_rows = build_mode_rows(assistant_mode_summary)
    if mode_rows:
        with st.container(border=True, key="backend-ops-ai-mode-shell"):
            st.markdown("**Assistant 模式拆解**")
            st.caption("把市場摘要、個人化建議、職缺比較分開看，才能知道哪一種模式還在拖延遲或品質。")
            st.dataframe(
                pd.DataFrame(mode_rows),
                use_container_width=True,
                hide_index=True,
            )

    if ai_events:
        with st.container(border=True, key="backend-ops-ai-events-shell"):
            st.markdown("**最近 AI 事件**")
            st.dataframe(
                pd.DataFrame(build_event_rows(ai_events)),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("目前還沒有 AI telemetry。先使用 AI 助理或履歷分析，這裡才會有資料。")

    cache_rows = build_cache_rows(cache_summary)
    if cache_rows:
        with st.container(border=True, key="backend-ops-ai-cache-shell"):
            st.markdown("**AI Cache / ANN 效率**")
            st.caption("把 chunk cache、embedding cache、remote embedding 與 ANN 候選數拆開看，才能知道延遲是卡在檢索還是模型。")
            st.dataframe(
                pd.DataFrame(cache_rows),
                use_container_width=True,
                hide_index=True,
            )

    version_rows = build_version_breakdown_rows(cache_summary)
    if version_rows:
        with st.container(border=True, key="backend-ops-ai-version-shell"):
            st.markdown("**Prompt / Retrieval / Model 版本分布**")
            st.caption("這塊用來看最近事件實際吃到哪個 prompt variant、prompt version、retrieval policy、chunking policy 與模型。")
            st.dataframe(
                pd.DataFrame(version_rows),
                use_container_width=True,
                hide_index=True,
            )


def render_runtime_signals_section(snapshot: BackendOperationsSnapshot) -> None:
    """Render scheduler / worker heartbeat signals."""
    render_section_header(
        "Scheduler / Worker Heartbeats",
        "從 runtime signal store 讀最近一次 heartbeat。若顯示 stale，通常代表 loop 沒在持續更新，或更新間隔已超過預期。",
        "Runtime Signals",
    )
    if snapshot.runtime_components:
        signal_cards = "".join(
            signal_card(
                kind=item.component_kind,
                component_id=item.component_id,
                status=item.status,
                detail=(
                    f"{item.error_code} · {item.message}"
                    if item.error_code and item.message
                    else (item.message or item.error_user_message or "無額外訊息")
                ),
                freshness=(
                    f"{'stale' if item.is_stale else 'fresh'} · {format_relative_time(item.updated_at)}"
                ),
            )
            for item in snapshot.runtime_components
        )
        st.markdown(
            f'<div class="ops-signal-grid">{signal_cards}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("目前還沒有 scheduler / worker heartbeat。啟動背景 worker 或 scheduler 後，這裡會開始出現狀態。")


def render_due_saved_searches_section(snapshot: BackendOperationsSnapshot) -> None:
    """Render due saved searches table."""
    render_section_header(
        "Due Saved Searches",
        "這些搜尋已超過 refresh window，scheduler 應該把它們 enqueue 進 queue。",
        "Scheduler Queue Feed",
    )
    due_rows = build_due_rows(snapshot)
    with st.container(border=True, key="backend-ops-due-shell"):
        if due_rows:
            st.dataframe(pd.DataFrame(due_rows), use_container_width=True, hide_index=True)
        else:
            st.success("目前沒有到期的 saved search。")


def render_recent_jobs_section(snapshot: BackendOperationsSnapshot) -> None:
    """Render recent queue jobs table."""
    render_section_header(
        "Recent Queue Jobs",
        "看最近 queue activity，確認 job 是不是卡在 pending、已被 lease，或已經 failed。",
        "Queue Runtime",
    )
    job_rows = build_job_rows(snapshot)
    with st.container(border=True, key="backend-ops-jobs-shell"):
        _render_ops_feedback()
        if job_rows:
            st.dataframe(pd.DataFrame(job_rows), use_container_width=True, hide_index=True)
        else:
            st.info("目前 queue 內還沒有 job 紀錄。")


def render_queue_control_section(
    *,
    ctx: PageContext,
    snapshot: BackendOperationsSnapshot,
) -> None:
    """Render replay/reprocess tools for failed jobs and dead letters."""
    render_section_header(
        "Queue Recovery",
        "這裡提供維運級 reprocess / replay。failed job 會先透過 dead-letter queue 保留，再由你手動重放。",
        "Recovery Tools",
    )
    with st.container(border=True, key="backend-ops-recovery-shell"):
        _render_ops_feedback()
        failed_jobs = [item for item in snapshot.recent_jobs if item.status == "failed"]
        dead_letters = snapshot.recent_dead_letters
        action_cols = st.columns(2, gap="small")

        with action_cols[0]:
            if failed_jobs:
                options = {
                    f"Job #{item.job_id} · {item.error_code or item.status}": int(item.job_id)
                    for item in failed_jobs
                }
                with st.form("backend-ops-reprocess-job-form"):
                    selected_label = st.selectbox(
                        "選擇 failed job",
                        options=list(options.keys()),
                        key="backend-ops-reprocess-job-select",
                    )
                    submitted = st.form_submit_button(
                        "重新排入 Queue",
                        use_container_width=True,
                        type="primary",
                    )
                if submitted:
                    result = reprocess_failed_job(
                        settings=ctx.settings,
                        job_id=int(options[selected_label]),
                    )
                    _set_ops_feedback(status=result.status, message=result.message)
                    st.rerun()
            else:
                st.caption("目前沒有 failed job 可 reprocess。")

        with action_cols[1]:
            if dead_letters:
                options = {
                    f"DLQ #{item.dead_letter_id} · {item.error_code or item.status}": int(item.dead_letter_id)
                    for item in dead_letters
                }
                with st.form("backend-ops-replay-dlq-form"):
                    selected_label = st.selectbox(
                        "選擇 dead letter",
                        options=list(options.keys()),
                        key="backend-ops-replay-dlq-select",
                    )
                    submitted = st.form_submit_button(
                        "Replay Dead Letter",
                        use_container_width=True,
                    )
                if submitted:
                    result = replay_dead_letter(
                        settings=ctx.settings,
                        dead_letter_id=int(options[selected_label]),
                    )
                    _set_ops_feedback(status=result.status, message=result.message)
                    st.rerun()
            else:
                st.caption("目前 dead-letter queue 是空的。")


def render_dead_letter_queue_section(snapshot: BackendOperationsSnapshot) -> None:
    """Render dead-letter queue table."""
    render_section_header(
        "Dead Letter Queue",
        "終態失敗工作會留在這裡，保留 payload、錯誤代碼、retryable 判斷與 replay 紀錄。",
        "DLQ",
    )
    dead_letter_rows = build_dead_letter_rows(snapshot)
    with st.container(border=True, key="backend-ops-dlq-shell"):
        if dead_letter_rows:
            st.dataframe(
                pd.DataFrame(dead_letter_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("目前沒有 dead-letter job。")


def render_snapshot_cache_section(snapshot: BackendOperationsSnapshot) -> None:
    """Render recent snapshot registry table."""
    render_section_header(
        "Snapshot Cache",
        "看 query snapshot registry 最近更新了哪些快照，是否還停留在 partial，或已經 ready 可被 UI 直接使用。",
        "Snapshot Registry",
    )
    snapshot_rows = build_snapshot_rows(snapshot)
    with st.container(border=True, key="backend-ops-snapshots-shell"):
        if snapshot_rows:
            st.dataframe(pd.DataFrame(snapshot_rows), use_container_width=True, hide_index=True)
        else:
            st.info("目前 snapshot registry 還沒有資料。")
