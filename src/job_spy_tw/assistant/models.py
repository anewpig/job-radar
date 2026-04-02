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
