from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from .models import Chunk


def extract_pdf(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(path)
    pages: list[tuple[int, str]] = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((number, text))
    return pages


def chunk_pages(
    pages: list[tuple[int, str]], chunk_words: int = 180, overlap_words: int = 35
) -> list[Chunk]:
    if overlap_words >= chunk_words:
        raise ValueError("overlap_words must be smaller than chunk_words")
    chunks: list[Chunk] = []
    index = 0
    for page_number, text in pages:
        words = text.split()
        start = 0
        while start < len(words):
            content = " ".join(words[start : start + chunk_words])
            chunks.append(
                Chunk(
                    content=content,
                    chunk_index=index,
                    page_start=page_number,
                    page_end=page_number,
                    metadata={"word_start": start},
                )
            )
            index += 1
            if start + chunk_words >= len(words):
                break
            start += chunk_words - overlap_words
    return chunks
