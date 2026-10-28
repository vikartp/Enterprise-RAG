"""Cross-Encoder reranker for hybrid search results."""

from __future__ import annotations

from typing import Optional

from app.config import get_settings
from app.schemas import RetrievedChunk

# Lazy-loaded model
_reranker = None


def _get_reranker():
    """Lazy-load the Cross-Encoder model."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder

        settings = get_settings()
        _reranker = CrossEncoder(settings.reranker_model)
        print(f"✓ Loaded reranker model: {settings.reranker_model}")
    return _reranker


async def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_n: Optional[int] = None,
) -> list[RetrievedChunk]:
    """
    Rerank retrieved chunks using a Cross-Encoder model.

    The Cross-Encoder processes (query, document) pairs jointly, providing
    deeper semantic understanding than bi-encoder similarity. This is the
    stage-2 refinement after hybrid retrieval.

    Args:
        query: The user's search query.
        chunks: Retrieved chunks from hybrid search.
        top_n: Number of top results to return. Defaults to len(chunks).

    Returns:
        Reranked list of RetrievedChunk with reranker_score populated.
    """
    if not chunks:
        return []

    top_n = top_n or len(chunks)
    reranker = _get_reranker()

    # Prepare query-document pairs
    pairs = [[query, chunk.content] for chunk in chunks]

    # Score all pairs
    scores = reranker.predict(pairs)

    # Attach scores and sort
    scored_chunks: list[RetrievedChunk] = []
    for chunk, score in zip(chunks, scores):
        updated_chunk = chunk.model_copy(update={"reranker_score": float(score)})
        scored_chunks.append(updated_chunk)

    # Sort by reranker score (descending) and take top_n
    scored_chunks.sort(key=lambda c: c.reranker_score, reverse=True)
    return scored_chunks[:top_n]
