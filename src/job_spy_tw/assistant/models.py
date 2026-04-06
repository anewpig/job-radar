"""Assistant helpers for models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class KnowledgeChunk:
    chunk_id: str
    source_type: str
    label: str
    text: str
    url: str = ""
    metadata: dict[str, Any] | None = None

    def metadata_items(self) -> dict[str, Any]:
        return self.metadata or {}

    def combined_text(self) -> str:
        metadata_lines: list[str] = []
        for key, value in self.metadata_items().items():
            if value in ("", None, [], {}, ()):
                continue
            if isinstance(value, (list, tuple, set)):
                rendered = " ".join(str(item) for item in value if item not in ("", None))
            else:
                rendered = str(value)
            if rendered:
                metadata_lines.append(f"{key}:{rendered}")
        return "\n".join(filter(None, [self.label, self.text, "\n".join(metadata_lines)]))
