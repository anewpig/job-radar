"""共用 UI helpers 的相容入口。"""

from .common_hero import render_hero
from .common_html import (
    _escape,
    _escape_multiline,
    _format_ranked_terms,
    build_chip_row,
    build_html_list,
    mask_identifier,
)
from .common_shells import (
    render_metrics_cta,
    render_newsletter_footer,
    render_section_header,
    render_top_header,
)

__all__ = [
    "_escape",
    "_escape_multiline",
    "_format_ranked_terms",
    "build_chip_row",
    "build_html_list",
    "mask_identifier",
    "render_hero",
    "render_metrics_cta",
    "render_newsletter_footer",
    "render_section_header",
    "render_top_header",
]
