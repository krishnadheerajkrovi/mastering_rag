from __future__ import annotations

from collections import defaultdict

from .database import Database
from .models import SearchResult
from .ollama import OllamaClient


def reciprocal_rank_fusion(
    ranked_lists: list[list[SearchResult]], k: int = 60
) -> list[SearchResult]:
    scores: dict[int, float] = defaultdict(float)
    by_id: dict[int, SearchResult] = {}
    for results in ranked_lists:
        for rank, result in enumerate(results, start=1):
            scores[result.chunk_id] += 1.0 / (k + rank)
            by_id[result.chunk_id] = result
    fused = []
    for chunk_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        result = by_id[chunk_id]
        result.score = score
        fused.append(result)
    return fused


class Retriever:
    def __init__(self, db: Database, ollama: OllamaClient):
        self.db = db
        self.ollama = ollama

    def vector(self, query: str, top_k: int = 5) -> list[SearchResult]:
        embedding = self.ollama.embed([f"search_query: {query}"])[0]
        return self.db.vector_search(embedding, top_k)

    def hybrid(self, query: str, top_k: int = 5) -> list[SearchResult]:
        embedding = self.ollama.embed([f"search_query: {query}"])[0]
        pool = max(top_k * 3, 10)
        return reciprocal_rank_fusion([
            self.db.vector_search(embedding, pool),
            self.db.keyword_search(query, pool),
        ])[:top_k]

    def long_context(
        self, query: str, top_k: int = 4, token_budget: int = 6000, radius: int = 2
    ) -> list[SearchResult]:
        seeds = self.hybrid(query, top_k)
        expanded: dict[int, SearchResult] = {}
        for seed in seeds:
            for result in self.db.neighboring_chunks(seed.document_id, seed.chunk_index, radius):
                expanded[result.chunk_id] = result
        ordered = sorted(expanded.values(), key=lambda item: (item.document_id, item.chunk_index))
        selected: list[SearchResult] = []
        used = 0
        for result in ordered:
            estimate = max(1, len(result.content.split()) * 4 // 3)
            if used + estimate > token_budget:
                continue
            selected.append(result)
            used += estimate
        return selected
