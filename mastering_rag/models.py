from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    content: str
    chunk_index: int
    page_start: int | None = None
    page_end: int | None = None
    contextual_prefix: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        return max(1, len(self.content.split()) * 4 // 3)


@dataclass
class SearchResult:
    chunk_id: int
    document_id: int
    source: str
    title: str
    chunk_index: int
    content: str
    contextual_prefix: str
    score: float
    page_start: int | None = None
    page_end: int | None = None

    @property
    def citation(self) -> str:
        page = f", p. {self.page_start}" if self.page_start else ""
        return f"{self.source}{page}, chunk {self.chunk_index}"
