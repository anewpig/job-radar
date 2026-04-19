"""Render the backend operations monitoring page compatibility entry."""

from __future__ import annotations

from ..backend_operations_service import collect_backend_operations_snapshot
from .page_context import PageContext
from .pages_backend_operations_sections import (
    inject_ops_styles,
    render_ai_monitoring_section,
    render_dead_letter_queue_section,
    render_due_saved_searches_section,
    render_operations_summary,
    render_queue_control_section,
    render_recent_jobs_section,
    render_runtime_signals_section,
    render_snapshot_cache_section,
)


def render_backend_operations_page(ctx: PageContext) -> None:
    """Render scheduler/worker operations status for developers/operators."""
    inject_ops_styles()
    snapshot = collect_backend_operations_snapshot(
        settings=ctx.settings,
        product_store=ctx.product_store,
    )
    render_operations_summary(snapshot)
    render_ai_monitoring_section(ctx)
    render_runtime_signals_section(snapshot)
    render_due_saved_searches_section(snapshot)
    render_recent_jobs_section(snapshot)
    render_queue_control_section(ctx=ctx, snapshot=snapshot)
    render_dead_letter_queue_section(snapshot)
    render_snapshot_cache_section(snapshot)
