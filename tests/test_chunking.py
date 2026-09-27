import pytest

from mastering_rag.chunking import chunk_pages


def test_chunking_overlaps_and_tracks_pages():
    chunks = chunk_pages([(7, " ".join(f"w{i}" for i in range(12)))], chunk_words=5, overlap_words=2)
    assert [chunk.content.split()[0] for chunk in chunks] == ["w0", "w3", "w6", "w9"]
    assert all(chunk.page_start == 7 for chunk in chunks)


def test_overlap_must_be_smaller_than_chunk():
    with pytest.raises(ValueError):
        chunk_pages([(1, "text")], chunk_words=5, overlap_words=5)
