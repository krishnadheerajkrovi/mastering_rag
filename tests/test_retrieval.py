from mastering_rag.models import SearchResult
from mastering_rag.retrieval import reciprocal_rank_fusion


def result(chunk_id: int, score: float = 1.0) -> SearchResult:
    return SearchResult(chunk_id, 1, "x.pdf", "X", chunk_id, "body", "", score)


def test_rrf_rewards_results_found_by_both_retrievers():
    fused = reciprocal_rank_fusion([[result(1), result(2)], [result(2), result(3)]])
    assert fused[0].chunk_id == 2
    assert len({item.chunk_id for item in fused}) == 3
