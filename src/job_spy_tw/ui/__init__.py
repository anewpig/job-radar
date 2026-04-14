"""UI package namespace.

The package intentionally avoids eager imports so submodules can be imported
independently without pulling the full Streamlit surface into every caller.
"""

from __future__ import annotations

__all__: list[str] = []
