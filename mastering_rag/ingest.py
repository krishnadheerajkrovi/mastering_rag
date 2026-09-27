from __future__ import annotations

import hashlib
from pathlib import Path

from .chunking import chunk_pages, extract_pdf
from .database import Database
from .ollama import OllamaClient


def contextual_prefix(client: OllamaClient, title: str, document_excerpt: str, chunk: str) -> str:
    return client.chat(
        "Write only a short retrieval context (maximum 70 words). Do not answer questions.",
        f"Document title: {title}\nDocument excerpt:\n{document_excerpt}\n\nChunk:\n{chunk}\n\n"
        "Explain where this chunk fits in the document and name its key topic."
    ).strip()


def ingest_pdf(path: Path, db: Database, client: OllamaClient, contextualize: bool = False) -> tuple[int, int]:
    raw = path.read_bytes()
    pages = extract_pdf(path)
    chunks = chunk_pages(pages)
    title = path.stem.replace("_", " ").title()
    if contextualize:
        excerpt = "\n".join(text for _, text in pages)[:6000]
        for chunk in chunks:
            chunk.contextual_prefix = contextual_prefix(client, title, excerpt, chunk.content)
    embedding_inputs = [
        f"search_document: {chunk.contextual_prefix}\n{chunk.content}" for chunk in chunks
    ]
    embeddings = client.embed(embedding_inputs)
    document_id = db.upsert_document(
        path, title, hashlib.sha256(raw).hexdigest(),
        {"pages": len(pages), "contextualized": contextualize}, chunks, embeddings
    )
    return document_id, len(chunks)
