"""Qdrant vector store — collection management and hybrid search."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings
from app.retrieval.embedder import get_dense_embedder, get_sparse_embedder
from app.schemas import EnrichedChunk, RetrievedChunk

# Module-level client (lazily initialized)
_client: Optional[AsyncQdrantClient] = None


def _get_client() -> AsyncQdrantClient:
    """Get or create the async Qdrant client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return _client


async def ensure_collection() -> None:
    """
    Ensure the Qdrant collection exists with hybrid vector configuration.

    Creates a collection with:
    - Dense vector: text-embedding-3-small (1536 dims, cosine distance)
    - Sparse vector: BM25 (for exact keyword matching)
    """
    settings = get_settings()
    client = _get_client()

    collections = await client.get_collections()
    existing_names = [c.name for c in collections.collections]

    if settings.qdrant_collection_name not in existing_names:
        await client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=settings.embedding_dim,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False),
                ),
            },
        )
        print(f"✓ Created Qdrant collection '{settings.qdrant_collection_name}'")
    else:
        print(f"✓ Qdrant collection '{settings.qdrant_collection_name}' already exists")


async def index_chunks(enriched_chunks: list[EnrichedChunk]) -> list[str]:
    """
    Index enriched chunks into Qdrant with both dense and sparse vectors.

    Each point contains:
    - Dense vector from the chunk content
    - Sparse vector from BM25 encoding
    - Rich payload with all metadata

    Args:
        enriched_chunks: List of enriched chunks to index.

    Returns:
        List of Qdrant point IDs.
    """
    settings = get_settings()
    client = _get_client()
    dense_embedder = get_dense_embedder()
    sparse_embedder = get_sparse_embedder()

    # Prepare texts for embedding (combine content + hypothetical questions for better recall)
    texts = []
    for chunk in enriched_chunks:
        combined = chunk.content
        if chunk.hypothetical_questions:
            combined += "\n" + "\n".join(chunk.hypothetical_questions)
        texts.append(combined)

    # Fit sparse embedder on this batch (for BM25 IDF)
    sparse_embedder.fit([c.content for c in enriched_chunks])

    # Generate embeddings
    dense_vectors = await dense_embedder.embed_texts(texts)
    sparse_vectors = sparse_embedder.encode_batch([c.content for c in enriched_chunks])

    # Build Qdrant points
    points = []
    point_ids = []

    for i, chunk in enumerate(enriched_chunks):
        point_id = str(uuid.uuid4())
        point_ids.append(point_id)

        sparse_indices, sparse_values = sparse_vectors[i]

        points.append(models.PointStruct(
            id=point_id,
            vector={
                "dense": dense_vectors[i],
                "sparse": models.SparseVector(
                    indices=sparse_indices,
                    values=sparse_values,
                ),
            },
            payload={
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "source_file": chunk.source_file,
                "section_header": chunk.section_header or "",
                "summary": chunk.summary,
                "keywords": chunk.keywords,
                "hypothetical_questions": chunk.hypothetical_questions,
            },
        ))

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        await client.upsert(
            collection_name=settings.qdrant_collection_name,
            points=batch,
        )

    return point_ids


async def hybrid_search(
    query: str,
    top_k: int = 20,
    final_k: int = 10,
    filters: Optional[dict[str, Any]] = None,
) -> list[RetrievedChunk]:
    """
    Perform hybrid search combining dense and sparse retrieval with RRF fusion.

    Strategy:
    1. Dense search (semantic understanding) — top_k results
    2. Sparse search (BM25 keyword matching) — top_k results
    3. Server-side RRF fusion to merge results
    4. Return top final_k results with all scores

    Args:
        query: User's search query.
        top_k: Number of results per retrieval method (before fusion).
        final_k: Final number of results after fusion.
        filters: Optional Qdrant payload filters.

    Returns:
        List of RetrievedChunk with dense, sparse, and RRF scores.
    """
    settings = get_settings()
    client = _get_client()
    dense_embedder = get_dense_embedder()
    sparse_embedder = get_sparse_embedder()

    # Generate query embeddings
    dense_query = await dense_embedder.embed_query(query)
    sparse_indices, sparse_values = sparse_embedder.encode(query)

    # Build filter if provided
    qdrant_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchAny(any=value),
                ))
            else:
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                ))
        qdrant_filter = models.Filter(must=conditions)

    # Hybrid search using Qdrant's Query API with prefetch + RRF fusion
    results = await client.query_points(
        collection_name=settings.qdrant_collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_query,
                using="dense",
                limit=top_k,
                filter=qdrant_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_indices,
                    values=sparse_values,
                ),
                using="sparse",
                limit=top_k,
                filter=qdrant_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=final_k,
        with_payload=True,
    )

    # Convert to RetrievedChunk objects
    retrieved: list[RetrievedChunk] = []
    for point in results.points:
        payload = point.payload or {}
        retrieved.append(RetrievedChunk(
            chunk_id=payload.get("chunk_id", ""),
            content=payload.get("content", ""),
            source_file=payload.get("source_file", ""),
            section_header=payload.get("section_header") or None,
            summary=payload.get("summary", ""),
            hypothetical_questions=payload.get("hypothetical_questions", []),
            rrf_score=point.score or 0.0,
            # Individual scores are set during reranking
            dense_score=0.0,
            sparse_score=0.0,
            reranker_score=0.0,
        ))

    return retrieved
