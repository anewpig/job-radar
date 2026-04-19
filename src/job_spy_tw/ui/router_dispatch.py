"""提供主應用頁面 surface 包裝與 dispatch helper。"""

from __future__ import annotations

from .dev_annotations import render_dev_card_annotation
from .router_config import PAGE_SHELL_METADATA, PAGE_SURFACE_KEYS


def _render_page_in_surface(shell_key: str, body_key: str, render_fn, page_context) -> None:
    """用共用 surface shell 包住頁面內容，讓各功能頁有一致的大卡片底板。"""
    import streamlit as st

    with st.container(border=True, key=shell_key):
        metadata = PAGE_SHELL_METADATA.get(shell_key)
        if metadata is not None:
            render_dev_card_annotation(
                metadata["name"],
                element_id=shell_key,
                description=metadata["description"],
                layers=metadata["layers"],
                text_nodes=metadata["text_nodes"],
                show_popover=True,
                popover_key=shell_key,
            )
        with st.container(key=body_key):
            render_fn(page_context)


def dispatch_main_tab(selected_main_tab: str, page_context) -> None:
    """依目前主頁籤把控制權分派到對應頁面渲染函式。"""
    if selected_main_tab == "backend_console" and not bool(
        getattr(page_context, "backend_console_allowed", False)
    ):
        import streamlit as st

        st.warning("目前帳號沒有後端控制台權限。")
        selected_main_tab = "overview"
    if selected_main_tab == "overview":
        from .pages_market import render_overview_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["overview"], render_overview_page, page_context)
    elif selected_main_tab == "resume":
        from .pages_resume_assistant import render_resume_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["resume"], render_resume_page, page_context)
    elif selected_main_tab == "assistant":
        from .pages_resume_assistant import render_assistant_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["assistant"], render_assistant_page, page_context)
    elif selected_main_tab == "tasks":
        from .pages_market import render_tasks_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tasks"], render_tasks_page, page_context)
    elif selected_main_tab == "skills":
        from .pages_market import render_tasks_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tasks"], render_tasks_page, page_context)
    elif selected_main_tab == "sources":
        from .pages_market import render_sources_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["sources"], render_sources_page, page_context)
    elif selected_main_tab == "fine_tuning":
        from .pages_fine_tuning import render_fine_tuning_page

        _render_page_in_surface(
            *PAGE_SURFACE_KEYS["fine_tuning"],
            render_fine_tuning_page,
            page_context,
        )
    elif selected_main_tab == "tracking":
        from .pages_product import render_tracking_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tracking"], render_tracking_page, page_context)
    elif selected_main_tab == "board":
        from .pages_product import render_board_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["board"], render_board_page, page_context)
    elif selected_main_tab == "notifications":
        from .pages_product import render_notifications_page

        render_notifications_page(page_context)
    elif selected_main_tab == "database":
        from .pages_database import render_database_page

        render_database_page(page_context)
    elif selected_main_tab == "backend_console":
        from .pages_backend_console import render_backend_console_page

        _render_page_in_surface(
            *PAGE_SURFACE_KEYS["backend_console"],
            render_backend_console_page,
            page_context,
        )
    elif selected_main_tab == "backend_ops":
        from .pages_backend_operations import render_backend_operations_page

        _render_page_in_surface(
            *PAGE_SURFACE_KEYS["backend_ops"],
            render_backend_operations_page,
            page_context,
        )
    elif selected_main_tab == "backend":
        from .pages_backend_architecture import render_backend_architecture_page

        _render_page_in_surface(
            *PAGE_SURFACE_KEYS["backend"],
            render_backend_architecture_page,
            page_context,
        )
    elif selected_main_tab == "export":
        from .pages_market import render_export_page

        render_export_page(page_context)
