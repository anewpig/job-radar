"""Render the backend operations monitoring page."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from ..backend_operations_service import collect_backend_operations_snapshot
from .common import _escape, render_section_header
from .page_context import PageContext


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def _format_relative_time(value: str) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return "尚未記錄"
    delta = datetime.now() - parsed
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return f"{seconds} 秒前"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分鐘前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小時前"
    days = hours // 24
    return f"{days} 天前"


def _format_timestamp(value: str) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return "尚未記錄"
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _short_signature(value: str, *, prefix: int = 10) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return "未建立"
    if len(cleaned) <= prefix + 4:
        return cleaned
    return f"{cleaned[:prefix]}..."


def _metric_card(label: str, value: str, detail: str, tone: str = "neutral") -> str:
    return f"""
<div class="ops-metric-card ops-metric-card--{_escape(tone)}">
  <div class="ops-metric-label">{_escape(label)}</div>
  <div class="ops-metric-value">{_escape(value)}</div>
  <div class="ops-metric-detail">{_escape(detail)}</div>
</div>
"""


def _signal_card(kind: str, component_id: str, status: str, detail: str, freshness: str) -> str:
    tone = "stale" if freshness == "stale" else ("warn" if status in {"failed"} else "good")
    return f"""
<div class="ops-signal-card ops-signal-card--{_escape(tone)}">
  <div class="ops-signal-head">
    <span class="ops-signal-kind">{_escape(kind)}</span>
    <span class="ops-signal-status">{_escape(status)}</span>
  </div>
  <div class="ops-signal-id">{_escape(component_id)}</div>
  <div class="ops-signal-detail">{_escape(detail)}</div>
  <div class="ops-signal-meta">{_escape(freshness)}</div>
</div>
"""


def _inject_ops_styles() -> None:
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


def render_backend_operations_page(ctx: PageContext) -> None:
    """Render scheduler/worker operations status for developers/operators."""
    _inject_ops_styles()
    snapshot = collect_backend_operations_snapshot(
        settings=ctx.settings,
        product_store=ctx.product_store,
    )

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

    summary_cards = [
        _metric_card(
            "執行模式",
            snapshot.execution_mode or "inline",
            "目前 UI 觸發後端工作的執行模式。",
            tone="good" if snapshot.execution_mode == "worker" else "neutral",
        ),
        _metric_card(
            "待刷新 Saved Searches",
            str(snapshot.due_saved_search_count),
            f"最近刷新：{_format_relative_time(snapshot.last_saved_search_refresh_at)}",
            tone="warn" if snapshot.due_saved_search_count else "neutral",
        ),
        _metric_card(
            "Pending Jobs",
            str(snapshot.pending_job_count),
            f"最近 job 活動：{_format_relative_time(snapshot.last_job_activity_at)}",
            tone="warn" if snapshot.pending_job_count else "neutral",
        ),
        _metric_card(
            "Leased Jobs",
            str(snapshot.leased_job_count),
            "已被 worker 接手，尚未完成。",
            tone="good" if snapshot.leased_job_count else "neutral",
        ),
        _metric_card(
            "Failed Jobs",
            str(snapshot.failed_job_count),
            "需要回頭看錯誤訊息與 worker heartbeat。",
            tone="risk" if snapshot.failed_job_count else "good",
        ),
        _metric_card(
            "Snapshot Cache",
            f"{snapshot.ready_snapshot_count} ready / {snapshot.partial_snapshot_count} partial",
            f"最近快照更新：{_format_relative_time(snapshot.last_snapshot_update_at)}",
            tone="neutral",
        ),
    ]
    st.markdown(
        f'<div class="ops-metric-grid">{"".join(summary_cards)}</div>',
        unsafe_allow_html=True,
    )

    render_section_header(
        "Scheduler / Worker Heartbeats",
        "從 runtime signal store 讀最近一次 heartbeat。若顯示 stale，通常代表 loop 沒在持續更新，或更新間隔已超過預期。",
        "Runtime Signals",
    )
    if snapshot.runtime_components:
        signal_cards = "".join(
            _signal_card(
                kind=item.component_kind,
                component_id=item.component_id,
                status=item.status,
                detail=item.message or "無額外訊息",
                freshness=(
                    f"{'stale' if item.is_stale else 'fresh'} · { _format_relative_time(item.updated_at) }"
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

    render_section_header(
        "Due Saved Searches",
        "這些搜尋已超過 refresh window，scheduler 應該把它們 enqueue 進 queue。",
        "Scheduler Queue Feed",
    )
    due_rows = [
        {
            "使用者": item.user_label,
            "Search ID": item.search_id,
            "搜尋名稱": item.search_name,
            "頻率": item.frequency,
            "上次刷新": _format_timestamp(item.last_run_at),
            "角色": " / ".join(item.role_labels) if item.role_labels else "未設定",
            "自訂查詢數": item.custom_query_count,
        }
        for item in snapshot.due_saved_searches
    ]
    with st.container(border=True, key="backend-ops-due-shell"):
        if due_rows:
            st.dataframe(pd.DataFrame(due_rows), use_container_width=True, hide_index=True)
        else:
            st.success("目前沒有到期的 saved search。")

    render_section_header(
        "Recent Queue Jobs",
        "看最近 queue activity，確認 job 是不是卡在 pending、已被 lease，或已經 failed。",
        "Queue Runtime",
    )
    job_rows = [
        {
            "Job ID": item.job_id,
            "狀態": item.status,
            "Priority": item.priority,
            "Query": ", ".join(item.query_labels) if item.query_labels else _short_signature(item.query_signature),
            "Subscribers": item.subscriber_count,
            "Attempts": (
                f"{item.attempt_count}/{item.max_attempts}"
                if item.max_attempts
                else str(item.attempt_count)
            ),
            "建立時間": _format_timestamp(item.created_at),
            "最後更新": _format_timestamp(item.updated_at),
            "Next Retry": (
                _format_timestamp(item.next_retry_at)
                if item.next_retry_at
                else "未排程"
            ),
            "Lease Owner": item.lease_owner or "未租用",
            "Lease 到期": _format_timestamp(item.lease_expires_at) if item.lease_expires_at else "未租用",
            "錯誤": item.error_message or "",
        }
        for item in snapshot.recent_jobs
    ]
    with st.container(border=True, key="backend-ops-jobs-shell"):
        if job_rows:
            st.dataframe(pd.DataFrame(job_rows), use_container_width=True, hide_index=True)
        else:
            st.info("目前 queue 內還沒有 job 紀錄。")

    render_section_header(
        "Snapshot Cache",
        "看 query snapshot registry 最近更新了哪些快照，是否還停留在 partial，或已經 ready 可被 UI 直接使用。",
        "Snapshot Registry",
    )
    snapshot_rows = [
        {
            "Signature": _short_signature(item.query_signature, prefix=14),
            "狀態": item.status,
            "Partial": "是" if item.is_partial else "否",
            "生成時間": _format_timestamp(item.generated_at),
            "最後更新": _format_timestamp(item.updated_at),
            "Fresh Until": _format_timestamp(item.fresh_until),
            "Queries": item.query_count,
            "Jobs": item.job_count,
            "錯誤": item.error_message or "",
        }
        for item in snapshot.recent_snapshots
    ]
    with st.container(border=True, key="backend-ops-snapshots-shell"):
        if snapshot_rows:
            st.dataframe(pd.DataFrame(snapshot_rows), use_container_width=True, hide_index=True)
        else:
            st.info("目前 snapshot registry 還沒有資料。")

    st.caption(
        "面板更新時點以頁面刷新當下為準；若要讓 scheduler / worker heartbeat 持續更新，需另外啟動背景程序。"
    )
