"""Helpers for backend operations page formatting and row preparation."""

from __future__ import annotations

from datetime import datetime

from ..backend_operations_service import BackendOperationsSnapshot
from .common import _escape


def parse_iso(value: str) -> datetime | None:
    """Parse an ISO-ish timestamp string."""
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def format_relative_time(value: str) -> str:
    """Format timestamp into a relative Chinese label."""
    parsed = parse_iso(value)
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


def format_timestamp(value: str) -> str:
    """Format timestamp into a stable absolute string."""
    parsed = parse_iso(value)
    if parsed is None:
        return "尚未記錄"
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def short_signature(value: str, *, prefix: int = 10) -> str:
    """Shorten a long query signature for display."""
    cleaned = str(value or "").strip()
    if not cleaned:
        return "未建立"
    if len(cleaned) <= prefix + 4:
        return cleaned
    return f"{cleaned[:prefix]}..."


def metric_card(label: str, value: str, detail: str, tone: str = "neutral") -> str:
    """Render a metric card HTML snippet."""
    return f"""
<div class="ops-metric-card ops-metric-card--{_escape(tone)}">
  <div class="ops-metric-label">{_escape(label)}</div>
  <div class="ops-metric-value">{_escape(value)}</div>
  <div class="ops-metric-detail">{_escape(detail)}</div>
</div>
"""


def signal_card(kind: str, component_id: str, status: str, detail: str, freshness: str) -> str:
    """Render a runtime signal card HTML snippet."""
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


def status_tone(status: str) -> str:
    """Map AI budget status to a visual tone."""
    normalized = str(status or "").strip().upper()
    if normalized in {"FAIL", "FAILED", "BLOCKED"}:
        return "risk"
    if normalized in {"WARN", "NO_DATA", "DEFER"}:
        return "warn"
    return "good"


def build_summary_cards(snapshot: BackendOperationsSnapshot) -> list[str]:
    """Build top-level operations summary metric cards."""
    return [
        metric_card(
            "執行模式",
            snapshot.execution_mode or "inline",
            "目前 UI 觸發後端工作的執行模式。",
            tone="good" if snapshot.execution_mode == "worker" else "neutral",
        ),
        metric_card(
            "待刷新 Saved Searches",
            str(snapshot.due_saved_search_count),
            f"最近刷新：{format_relative_time(snapshot.last_saved_search_refresh_at)}",
            tone="warn" if snapshot.due_saved_search_count else "neutral",
        ),
        metric_card(
            "Pending Jobs",
            str(snapshot.pending_job_count),
            f"最近 job 活動：{format_relative_time(snapshot.last_job_activity_at)}",
            tone="warn" if snapshot.pending_job_count else "neutral",
        ),
        metric_card(
            "Leased Jobs",
            str(snapshot.leased_job_count),
            "已被 worker 接手，尚未完成。",
            tone="good" if snapshot.leased_job_count else "neutral",
        ),
        metric_card(
            "Failed Jobs",
            str(snapshot.failed_job_count),
            "需要回頭看錯誤訊息與 worker heartbeat。",
            tone="risk" if snapshot.failed_job_count else "good",
        ),
        metric_card(
            "Snapshot Cache",
            f"{snapshot.ready_snapshot_count} ready / {snapshot.partial_snapshot_count} partial",
            f"最近快照更新：{format_relative_time(snapshot.last_snapshot_update_at)}",
            tone="neutral",
        ),
    ]


def build_ai_budget_cards(ai_budget: dict, ai_summary: dict) -> list[str]:
    """Build AI monitoring metric cards."""
    return [
        metric_card(
            "延遲 / 穩定性 Budget",
            str(ai_budget.get("status", "NO_DATA")),
            "依最近 telemetry 判定整體 PASS / WARN / FAIL。",
            tone=status_tone(str(ai_budget.get("status", "NO_DATA"))),
        ),
        metric_card(
            "Token Budget",
            str(ai_budget.get("cost_tracking", {}).get("status", "NO_DATA")),
            "目前以 token budget 代替成本 gate，尚未折算美元。",
            tone=status_tone(str(ai_budget.get("cost_tracking", {}).get("status", "NO_DATA"))),
        ),
        metric_card(
            "最近事件數",
            str(sum(int(bucket.get("count", 0)) for bucket in ai_summary.values())),
            "來自 ai_monitoring_events 的最近事件視窗。",
            tone="neutral",
        ),
        metric_card(
            "涵蓋事件類型",
            str(len(ai_summary)),
            "問答、報告、履歷擷取、履歷匹配、完整履歷分析。",
            tone="neutral",
        ),
    ]


def build_budget_rows(ai_budget: dict) -> list[dict[str, object]]:
    """Build AI budget dataframe rows."""
    budget_rows: list[dict[str, object]] = []
    for event_type, latency_budget in ai_budget.get("event_budgets", {}).items():
        token_budget = ai_budget.get("cost_tracking", {}).get("event_budgets", {}).get(event_type, {})
        budget_rows.append(
            {
                "事件": event_type,
                "延遲狀態": latency_budget.get("status", "NO_DATA"),
                "平均延遲(ms)": latency_budget.get("avg_latency_ms", 0.0),
                "P95 延遲(ms)": latency_budget.get("p95_latency_ms", 0.0),
                "錯誤率": latency_budget.get("error_rate", 0.0),
                "Token 狀態": token_budget.get("status", "NO_DATA"),
                "平均 tokens": token_budget.get("avg_total_tokens", 0.0),
                "P95 tokens": token_budget.get("p95_total_tokens", 0.0),
                "樣本數": latency_budget.get("count", 0),
            }
        )
    return budget_rows


def build_mode_rows(assistant_mode_summary: dict) -> list[dict[str, object]]:
    """Build assistant mode dataframe rows."""
    mode_rows: list[dict[str, object]] = []
    for event_type, mode_buckets in assistant_mode_summary.items():
        for answer_mode, bucket in mode_buckets.items():
            mode_rows.append(
                {
                    "事件": event_type,
                    "模式": answer_mode,
                    "狀態": bucket.get("status", "NO_DATA"),
                    "延遲狀態": bucket.get("latency_status", "NO_DATA"),
                    "Token 狀態": bucket.get("token_status", "NO_DATA"),
                    "平均延遲(ms)": bucket.get("avg_latency_ms", 0.0),
                    "P95 延遲(ms)": bucket.get("p95_latency_ms", 0.0),
                    "平均 tokens": bucket.get("avg_total_tokens", 0.0),
                    "P95 tokens": bucket.get("p95_total_tokens", 0.0),
                    "錯誤率": bucket.get("error_rate", 0.0),
                    "樣本數": bucket.get("count", 0),
                }
            )
    return mode_rows


def build_event_rows(ai_events: list[dict]) -> list[dict[str, object]]:
    """Build recent AI events dataframe rows."""
    return [
        {
            "時間": format_timestamp(str(item.get("created_at", ""))),
            "事件": item.get("event_type", ""),
            "狀態": item.get("status", ""),
            "延遲(ms)": round(float(item.get("latency_ms", 0.0)), 3),
            "模型": item.get("model_name", ""),
            "tokens": int(item.get("metadata", {}).get("usage_total_tokens", 0) or 0),
            "requests": int(item.get("metadata", {}).get("usage_requests", 0) or 0),
            "chunks / matches": (
                item.get("metadata", {}).get("used_chunks")
                or item.get("metadata", {}).get("matches_count")
                or 0
            ),
            "query signature": short_signature(str(item.get("query_signature", ""))),
        }
        for item in ai_events
    ]


def build_cache_rows(cache_summary: dict) -> list[dict[str, object]]:
    """Build cache / ANN efficiency rows grouped by event type."""
    rows: list[dict[str, object]] = []
    for event_type, bucket in (cache_summary.get("event_breakdown") or {}).items():
        rows.append(
            {
                "事件": event_type,
                "requests": int(bucket.get("requests", 0) or 0),
                "chunk cache hit rate": float(bucket.get("chunk_cache_hit_rate", 0.0) or 0.0),
                "embedding memory hits": int(bucket.get("embedding_memory_hits", 0) or 0),
                "embedding disk hits": int(bucket.get("embedding_disk_hits", 0) or 0),
                "embedding remote texts": int(bucket.get("embedding_remote_texts", 0) or 0),
                "profile mem / disk": (
                    f"{int(bucket.get('profile_cache_memory_hits', 0) or 0)} / "
                    f"{int(bucket.get('profile_cache_disk_hits', 0) or 0)}"
                ),
                "title mem / disk": (
                    f"{int(bucket.get('title_cache_memory_hits', 0) or 0)} / "
                    f"{int(bucket.get('title_cache_disk_hits', 0) or 0)}"
                ),
                "avg ANN candidates": float(bucket.get("avg_persistent_ann_candidates", 0.0) or 0.0),
            }
        )
    return rows


def build_version_breakdown_rows(cache_summary: dict) -> list[dict[str, object]]:
    """Build prompt / retrieval / model version usage rows."""
    rows: list[dict[str, object]] = []
    for field_name, bucket in (cache_summary.get("version_breakdown") or {}).items():
        if not bucket:
            continue
        for value, count in sorted(bucket.items(), key=lambda item: (-int(item[1]), item[0])):
            rows.append(
                {
                    "欄位": field_name,
                    "值": value,
                    "樣本數": int(count),
                }
            )
    return rows


def build_due_rows(snapshot: BackendOperationsSnapshot) -> list[dict[str, object]]:
    """Build due saved searches dataframe rows."""
    return [
        {
            "使用者": item.user_label,
            "Search ID": item.search_id,
            "搜尋名稱": item.search_name,
            "頻率": item.frequency,
            "上次刷新": format_timestamp(item.last_run_at),
            "角色": " / ".join(item.role_labels) if item.role_labels else "未設定",
            "自訂查詢數": item.custom_query_count,
        }
        for item in snapshot.due_saved_searches
    ]


def build_job_rows(snapshot: BackendOperationsSnapshot) -> list[dict[str, object]]:
    """Build recent queue jobs dataframe rows."""
    return [
        {
            "Job ID": item.job_id,
            "狀態": item.status,
            "Priority": item.priority,
            "Query": ", ".join(item.query_labels) if item.query_labels else short_signature(item.query_signature),
            "Subscribers": item.subscriber_count,
            "Attempts": (
                f"{item.attempt_count}/{item.max_attempts}"
                if item.max_attempts
                else str(item.attempt_count)
            ),
            "建立時間": format_timestamp(item.created_at),
            "最後更新": format_timestamp(item.updated_at),
            "Next Retry": (
                format_timestamp(item.next_retry_at)
                if item.next_retry_at
                else "未排程"
            ),
            "Lease Owner": item.lease_owner or "未租用",
            "Lease 到期": format_timestamp(item.lease_expires_at) if item.lease_expires_at else "未租用",
            "錯誤": item.error_message or "",
        }
        for item in snapshot.recent_jobs
    ]


def build_snapshot_rows(snapshot: BackendOperationsSnapshot) -> list[dict[str, object]]:
    """Build recent snapshot cache dataframe rows."""
    return [
        {
            "Signature": short_signature(item.query_signature, prefix=14),
            "狀態": item.status,
            "Partial": "是" if item.is_partial else "否",
            "生成時間": format_timestamp(item.generated_at),
            "最後更新": format_timestamp(item.updated_at),
            "Fresh Until": format_timestamp(item.fresh_until),
            "Queries": item.query_count,
            "Jobs": item.job_count,
            "錯誤": item.error_message or "",
        }
        for item in snapshot.recent_snapshots
    ]
