"""提供職缺總覽頁的渲染函式。"""

from __future__ import annotations

from math import ceil

import streamlit as st

from .common import _escape, build_chip_row
from .dev_annotations import render_dev_card_annotation
from .frames import filter_jobs_frame
from .page_context import PageContext
from .renderers import render_job_cards


def _build_pagination_tokens(total_pages: int, current_page: int) -> list[int | str]:
    """建立帶省略號的精簡分頁序列。"""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))
    if current_page <= 4:
        return [1, 2, 3, 4, 5, "...", total_pages]
    if current_page >= total_pages - 3:
        return [1, "...", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
    return [1, "...", current_page - 1, current_page, current_page + 1, "...", total_pages]


def _clear_overview_filters() -> None:
    """清空總覽頁篩選器，並把分頁回到第一頁。"""
    st.session_state.overview_source_filter = []
    st.session_state.overview_role_filter = []
    st.session_state.overview_skill_filter = []
    st.session_state.overview_page = 1
    _queue_overview_scroll_to_top()


def _sorted_filter_options(values) -> list[str]:
    """把篩選選項整理成穩定、可顯示的字串清單。"""
    cleaned = {
        str(item).strip()
        for item in values
        if str(item).strip() and str(item).strip().lower() != "nan"
    }
    return sorted(cleaned)


def _queue_overview_scroll_to_top() -> None:
    """在下一輪 rerun 後把視窗捲回職缺總覽卡片頂部。"""
    st.session_state.overview_scroll_to_top = True


def _render_overview_scroll_script() -> None:
    """若本輪需要自動捲動，就把視窗對齊到 overview 卡片頂部。"""
    if not st.session_state.pop("overview_scroll_to_top", False):
        return
    with st.container(key="overview-scroll-shell"):
        st.html(
            """
<script>
const scrollToOverviewTop = () => {
  const target = window.parent.document.getElementById("overview-top-anchor");
  if (!target) {
    window.setTimeout(scrollToOverviewTop, 120);
    return;
  }
  target.scrollIntoView({ behavior: "auto", block: "start" });
};
scrollToOverviewTop();
</script>
            """,
            unsafe_allow_javascript=True,
        )


def _render_overview_dedupe_script() -> None:
    """清掉瀏覽器端殘留的舊 overview shell，只保留最後一張。"""
    return


def render_overview_page(ctx: PageContext) -> None:
    """渲染職缺總覽頁，包括篩選器、卡片列表與分頁。"""
    current_render_nonce = str(st.session_state.get("_app_render_nonce", ""))
    if current_render_nonce and st.session_state.get("_overview_rendered_nonce") == current_render_nonce:
        return
    st.session_state._overview_rendered_nonce = current_render_nonce

    _render_overview_scroll_script()
    st.markdown('<div id="overview-top-anchor"></div>', unsafe_allow_html=True)
    source_options = _sorted_filter_options(ctx.job_frame["source"].unique()) if not ctx.job_frame.empty else []
    role_options = _sorted_filter_options(ctx.job_frame["matched_role"].unique()) if not ctx.job_frame.empty else []
    skill_options = _sorted_filter_options(ctx.skill_frame["skill"].unique()) if not ctx.skill_frame.empty else []
    source_filter_state = [
        item for item in st.session_state.get("overview_source_filter", []) if item in source_options
    ]
    role_filter_state = [
        item for item in st.session_state.get("overview_role_filter", []) if item in role_options
    ]
    skill_filter_state = [
        item for item in st.session_state.get("overview_skill_filter", []) if item in skill_options
    ]
    sort_mode_state = st.session_state.get("overview_sort_mode", "relevance")
    st.session_state.overview_source_filter = source_filter_state
    st.session_state.overview_role_filter = role_filter_state
    st.session_state.overview_skill_filter = skill_filter_state
    st.session_state.overview_sort_mode = sort_mode_state
    active_filter_count = len(source_filter_state) + len(role_filter_state) + len(skill_filter_state)
    preview_filtered = filter_jobs_frame(
        ctx.job_frame,
        source_filter=source_filter_state,
        role_filter=role_filter_state,
        skill_filter=skill_filter_state,
        sort_mode=sort_mode_state,
    )
    st.markdown(
        f"""
<div class="section-shell overview-intro">
  <div class="overview-intro-main">
    <div class="section-kicker">{_escape("Job Overview")}</div>
    <div class="section-title">{_escape("職缺總覽")}</div>
    <div class="overview-intro-desc">{_escape("先縮小範圍，再比較值得深入看的職缺。")}</div>
  </div>
  <div class="overview-intro-stats">
    <div class="overview-intro-stat">
      <div class="overview-intro-stat-label">{_escape("符合條件")}</div>
      <div class="overview-intro-stat-value">{_escape(f"{len(preview_filtered)} 筆")}</div>
    </div>
    <div class="overview-intro-stat">
      <div class="overview-intro-stat-label">{_escape("已啟用篩選")}</div>
      <div class="overview-intro-stat-value">{_escape(f"{active_filter_count} 項")}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    filter_shell_cols = st.columns([1, 1], gap="medium")
    with filter_shell_cols[0]:
        with st.container(border=True, key="overview-filter-shell"):
            render_dev_card_annotation(
                "總覽篩選卡",
                element_id="overview-filter-shell",
                description="來源、匹配角色與技能的篩選控制區。",
                layers=[
                    "overview_source_filter",
                    "overview_role_filter",
                    "overview_skill_filter",
                ],
                text_nodes=[
                    ("來源", "來源 multiselect 標籤。"),
                    ("對應職缺", "角色 multiselect 標籤。"),
                    ("技能", "技能 multiselect 標籤。"),
                    ("清除篩選", "重置所有篩選條件的 ghost button。"),
                ],
                compact=True,
                show_popover=True,
                popover_key="overview-filter-shell",
            )
            toolbar_cols = st.columns(4, gap="small")
            source_filter = toolbar_cols[0].multiselect(
                "來源",
                source_options,
                key="overview_source_filter",
            )
            role_filter = toolbar_cols[1].multiselect(
                "對應職缺",
                role_options,
                key="overview_role_filter",
            )
            skill_filter = toolbar_cols[2].multiselect(
                "技能",
                skill_options,
                key="overview_skill_filter",
            )
            sort_mode = toolbar_cols[3].selectbox(
                "排序",
                options=["relevance", "posted_desc"],
                format_func=lambda value: {
                    "relevance": "相關度",
                    "posted_desc": "日期（新→舊）",
                }.get(value, value),
                key="overview_sort_mode",
            )
    filter_shell_cols[1].empty()

    filtered = filter_jobs_frame(
        ctx.job_frame,
        source_filter=source_filter,
        role_filter=role_filter,
        skill_filter=skill_filter,
        sort_mode=sort_mode,
    )
    active_filter_count = len(source_filter) + len(role_filter) + len(skill_filter)
    filter_signature = "|".join(
        [
            ctx.snapshot.generated_at,
            ",".join(sorted(source_filter)),
            ",".join(sorted(role_filter)),
            ",".join(sorted(skill_filter)),
            sort_mode,
            str(len(filtered)),
        ]
    )
    if st.session_state.get("overview_filter_signature") != filter_signature:
        st.session_state.overview_filter_signature = filter_signature
        st.session_state.overview_page = 1

    page_size = 10
    total_jobs = len(filtered)
    total_pages = max(1, ceil(total_jobs / page_size)) if total_jobs else 1
    current_page = int(st.session_state.get("overview_page", 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state.overview_page = current_page
    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size
    visible_frame = filtered.iloc[start_index:end_index]
    active_filter_labels = (
        [f"來源：{item}" for item in source_filter]
        + [f"對應職缺：{item}" for item in role_filter]
        + [f"技能：{item}" for item in skill_filter]
    )
    if active_filter_labels:
        meta_cols = st.columns([1, 0.2], gap="small")
        meta_cols[0].markdown(
            f"""
<div class="overview-filter-meta">
  <div class="chip-row">{build_chip_row(active_filter_labels, tone="soft", limit=12)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        meta_cols[1].button(
            "清除篩選",
            key="overview_clear_filters",
            use_container_width=True,
            type="secondary",
            on_click=_clear_overview_filters,
        )
    render_job_cards(
        visible_frame,
        jobs_by_url=ctx.jobs_by_url,
        product_store=ctx.product_store,
        favorite_urls=ctx.favorite_urls,
        current_user_id=None if ctx.current_user_is_guest else ctx.current_user_id,
        favorites_enabled=not ctx.current_user_is_guest,
        active_saved_search_id=ctx.active_saved_search.id if ctx.active_saved_search else None,
        active_saved_search_name=ctx.active_saved_search.name if ctx.active_saved_search else "",
        details_pending=ctx.crawl_phase == "finalizing",
    )
    if total_jobs > page_size:
        pagination_tokens = _build_pagination_tokens(total_pages, current_page)
        with st.container(key="overview-pagination-shell"):
            shown_start = start_index + 1
            shown_end = min(end_index, total_jobs)
            outer_cols = st.columns([1.15, 2.55], gap="small")
            outer_cols[0].markdown(
                f"""
<div class="overview-pagination-summary">
  第 {current_page} 頁，共 {total_pages} 頁
  <span>顯示 {shown_start}-{shown_end} / {total_jobs}</span>
</div>
                """,
                unsafe_allow_html=True,
            )
            with outer_cols[1]:
                inner_widths = [0.7] * (len(pagination_tokens) + 2)
                pagination_cols = st.columns(inner_widths, gap="small")
                with pagination_cols[0]:
                    if st.button(
                        "‹",
                        key="overview_prev_page",
                        use_container_width=True,
                        disabled=current_page <= 1,
                        type="secondary",
                    ):
                        st.session_state.overview_page = max(1, current_page - 1)
                        _queue_overview_scroll_to_top()
                        st.rerun()
                for index, token in enumerate(pagination_tokens, start=1):
                    with pagination_cols[index]:
                        if token == "...":
                            st.markdown("<div class='overview-pagination-ellipsis'>...</div>", unsafe_allow_html=True)
                        else:
                            is_current = int(token) == current_page
                            if st.button(
                                str(token),
                                key=f"overview-page-{token}",
                                use_container_width=True,
                                type="primary" if is_current else "secondary",
                            ):
                                if not is_current:
                                    st.session_state.overview_page = int(token)
                                    _queue_overview_scroll_to_top()
                                    st.rerun()
                with pagination_cols[-1]:
                    if st.button(
                        "›",
                        key="overview_next_page",
                        use_container_width=True,
                        disabled=current_page >= total_pages,
                        type="secondary",
                    ):
                        st.session_state.overview_page = min(total_pages, current_page + 1)
                        _queue_overview_scroll_to_top()
                        st.rerun()
    _render_overview_dedupe_script()
