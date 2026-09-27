from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import psycopg
from pgvector.psycopg import register_vector

from .models import Chunk, SearchResult


class Database:
    def __init__(self, url: str):
        self.url = url

    def connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self.url)
        register_vector(conn)
        return conn

    def upsert_document(
        self, source: Path, title: str, checksum: str, metadata: dict, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have one embedding")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents(source, title, checksum, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(source) DO UPDATE SET
                      title = EXCLUDED.title, checksum = EXCLUDED.checksum,
                      metadata = EXCLUDED.metadata, indexed_at = now()
                    RETURNING id
                    """,
                    (source.name, title, checksum, json.dumps(metadata)),
                )
                document_id = cur.fetchone()[0]
                cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
                cur.executemany(
                    """
                    INSERT INTO chunks(
                      document_id, chunk_index, content, contextual_prefix,
                      token_estimate, page_start, page_end, embedding, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            document_id, chunk.chunk_index, chunk.content,
                            chunk.contextual_prefix, chunk.token_estimate,
                            chunk.page_start, chunk.page_end, embedding,
                            json.dumps(chunk.metadata),
                        )
                        for chunk, embedding in zip(chunks, embeddings)
                    ],
                )
        return document_id

    @staticmethod
    def _rows(rows: Iterable[tuple]) -> list[SearchResult]:
        return [SearchResult(*row) for row in rows]

    def vector_search(self, embedding: list[float], limit: int = 8) -> list[SearchResult]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.document_id, d.source, d.title, c.chunk_index,
                       c.content, c.contextual_prefix,
                       1 - (c.embedding <=> %s::vector) AS score,
                       c.page_start, c.page_end
                FROM chunks c JOIN documents d ON d.id = c.document_id
                ORDER BY c.embedding <=> %s::vector LIMIT %s
                """,
                (embedding, embedding, limit),
            )
            return self._rows(cur.fetchall())

    def keyword_search(self, query: str, limit: int = 8) -> list[SearchResult]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.document_id, d.source, d.title, c.chunk_index,
                       c.content, c.contextual_prefix,
                       ts_rank_cd(c.search_vector, websearch_to_tsquery('english', %s)) AS score,
                       c.page_start, c.page_end
                FROM chunks c JOIN documents d ON d.id = c.document_id
                WHERE c.search_vector @@ websearch_to_tsquery('english', %s)
                ORDER BY score DESC LIMIT %s
                """,
                (query, query, limit),
            )
            return self._rows(cur.fetchall())

    def neighboring_chunks(
        self, document_id: int, center: int, radius: int = 2
    ) -> list[SearchResult]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.document_id, d.source, d.title, c.chunk_index,
                       c.content, c.contextual_prefix, 1.0 AS score,
                       c.page_start, c.page_end
                FROM chunks c JOIN documents d ON d.id = c.document_id
                WHERE c.document_id = %s AND c.chunk_index BETWEEN %s AND %s
                ORDER BY c.chunk_index
                """,
                (document_id, max(0, center - radius), center + radius),
            )
            return self._rows(cur.fetchall())
