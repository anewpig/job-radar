"""Render backend architecture page compatibility entry."""

from __future__ import annotations

from .page_context import PageContext
from .pages_backend_architecture_helpers import build_backend_architecture_data
from .pages_backend_architecture_sections import (
    inject_backend_styles,
    render_ai_section,
    render_backend_section,
    render_database_section,
    render_flow_section,
    render_frontend_section,
    render_scaling_section,
    render_storage_section,
    render_summary_section,
    render_tables_expander,
    render_topology_section,
)


def render_backend_architecture_page(ctx: PageContext) -> None:
    """Render the current full-system architecture and runtime state."""
    inject_backend_styles()
    data = build_backend_architecture_data(ctx)
    render_summary_section(data)
    render_topology_section(data)
    render_frontend_section(data)
    render_backend_section(data)
    render_ai_section(data)
    render_database_section(data)
    render_flow_section(data)
    render_scaling_section(data)
    render_storage_section(data)
    render_tables_expander(data)
