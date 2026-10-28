"""Tests for the retrieval pipeline — embedder, qdrant store, reranker."""

from __future__ import annotations

import pytest

from app.schemas import RetrievedChunk


# ---------------------------------------------------------------------------
# Embedder tests
# ---------------------------------------------------------------------------

class TestSparseEmbedder:
    """Tests for the BM25 sparse embedder."""

    def test_sparse_encoding(self):
        """Sparse embedder should produce indices and values."""
        from app.retrieval.embedder import SparseEmbedder

        embedder = SparseEmbedder()
        embedder.fit(["hello world", "foo bar baz"])

        indices, values = embedder.encode("hello world")
        assert len(indices) > 0
        assert len(indices) == len(values)
        assert all(v > 0 for v in values)

    def test_sparse_vocabulary_growth(self):
        """Vocabulary should grow as new terms are encountered."""
        from app.retrieval.embedder import SparseEmbedder

        embedder = SparseEmbedder()
        embedder.fit(["hello world"])

        idx1, _ = embedder.encode("hello world")
        idx2, _ = embedder.encode("new unseen tokens")

        # New tokens should get new indices
        assert len(set(idx2) - set(idx1)) > 0

    def test_empty_input(self):
        """Empty input should return empty vectors."""
        from app.retrieval.embedder import SparseEmbedder

        embedder = SparseEmbedder()
        indices, values = embedder.encode("")
        assert indices == []
        assert values == []


# ---------------------------------------------------------------------------
# Reranker tests (structure only)
# ---------------------------------------------------------------------------

class TestReranker:
    """Tests for reranker data structures."""

    def test_retrieved_chunk_model(self):
        """RetrievedChunk should correctly hold all score types."""
        chunk = RetrievedChunk(
            chunk_id="test-1",
            content="Test document content",
            source_file="test.pdf",
            dense_score=0.85,
            sparse_score=0.72,
            rrf_score=0.78,
            reranker_score=0.91,
        )

        assert chunk.dense_score == 0.85
        assert chunk.reranker_score == 0.91
        assert chunk.source_file == "test.pdf"


# ---------------------------------------------------------------------------
# Integration tests (require Qdrant to be running)
# ---------------------------------------------------------------------------

class TestQdrantIntegration:
    """Integration tests requiring a running Qdrant instance."""

    @pytest.mark.skip(reason="Requires running Qdrant instance")
    @pytest.mark.asyncio
    async def test_ensure_collection(self):
        """Collection should be created if it doesn't exist."""
        from app.retrieval.qdrant_store import ensure_collection
        await ensure_collection()

    @pytest.mark.skip(reason="Requires running Qdrant + OpenAI API key")
    @pytest.mark.asyncio
    async def test_index_and_search(self):
        """End-to-end: index chunks then search."""
        from app.retrieval.qdrant_store import ensure_collection, index_chunks, hybrid_search
        from app.schemas import EnrichedChunk

        await ensure_collection()

        chunks = [
            EnrichedChunk(
                chunk_id="e2e-1",
                content="Python is a programming language.",
                chunk_index=0,
                source_file="test.md",
                summary="About Python",
                keywords=["python", "programming"],
                hypothetical_questions=["What is Python?"],
            ),
        ]

        point_ids = await index_chunks(chunks)
        assert len(point_ids) == 1

        results = await hybrid_search("What is Python?", top_k=5, final_k=3)
        assert len(results) > 0
