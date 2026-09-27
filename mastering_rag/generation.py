from __future__ import annotations

from .models import SearchResult
from .ollama import OllamaClient


def format_context(results: list[SearchResult]) -> str:
    blocks = []
    for number, result in enumerate(results, start=1):
        context = f"{result.contextual_prefix}\n" if result.contextual_prefix else ""
        blocks.append(f"[S{number}] {result.citation}\n{context}{result.content}")
    return "\n\n".join(blocks)


def generate_answer(client: OllamaClient, query: str, results: list[SearchResult]) -> str:
    return client.chat(
        "You are a grounded RAG assistant. Use only the supplied sources. "
        "If evidence is insufficient, say so. Cite claims inline with [S1], [S2], etc. "
        "Synthesize across sources instead of copying long passages.",
        f"Question: {query}\n\nSources:\n{format_context(results)}",
    ).strip()


def validate_answer(client: OllamaClient, query: str, answer: str, results: list[SearchResult]) -> dict:
    return client.chat_json(
        "You are a strict factual auditor. Return JSON with keys supported (boolean), "
        "unsupported_claims (array of strings), citation_issues (array of strings), and notes (string).",
        f"Question: {query}\n\nAnswer:\n{answer}\n\nEvidence:\n{format_context(results)}",
    )
