"""Agent tools — retrieval and metadata filter tools for the planner agent."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool

from app.retrieval.qdrant_store import hybrid_search
from app.retrieval.reranker import rerank


@tool
async def hybrid_search_tool(
    query: str,
    top_k: int = 10,
) -> str:
    """
    Search the knowledge base using hybrid retrieval (dense + sparse + reranking).

    Use this tool when you need to find information from the indexed documents.
    It combines semantic understanding with keyword matching for comprehensive results.

    Args:
        query: The search query to find relevant information.
        top_k: Number of results to return (default 10).

    Returns:
        Formatted string with retrieved chunks and their relevance scores.
    """
    # Stage 1: Hybrid retrieval
    chunks = await hybrid_search(query, top_k=20, final_k=top_k * 2)

    # Stage 2: Cross-Encoder reranking
    reranked = await rerank(query, chunks, top_n=top_k)

    if not reranked:
        return "No relevant documents found for the query."

    # Format results for the LLM
    results = []
    for i, chunk in enumerate(reranked, 1):
        results.append(
            f"[{i}] (Score: {chunk.reranker_score:.4f}) "
            f"Source: {chunk.source_file}"
            f"{f' | Section: {chunk.section_header}' if chunk.section_header else ''}\n"
            f"{chunk.content}\n"
        )

    return "\n---\n".join(results)


@tool
async def metadata_filter_tool(
    query: str,
    source_file: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    top_k: int = 5,
) -> str:
    """
    Search the knowledge base with metadata filters.

    Use this tool when the user's query references specific files, topics,
    or keywords that can narrow the search scope.

    Args:
        query: The search query.
        source_file: Filter by source filename (exact match).
        keywords: Filter by keyword tags.
        top_k: Number of results to return.

    Returns:
        Formatted string with filtered results.
    """
    filters: dict[str, Any] = {}
    if source_file:
        filters["source_file"] = source_file
    if keywords:
        filters["keywords"] = keywords

    chunks = await hybrid_search(query, top_k=20, final_k=top_k * 2, filters=filters or None)
    reranked = await rerank(query, chunks, top_n=top_k)

    if not reranked:
        return "No relevant documents found with the specified filters."

    results = []
    for i, chunk in enumerate(reranked, 1):
        results.append(
            f"[{i}] (Score: {chunk.reranker_score:.4f}) "
            f"Source: {chunk.source_file}\n"
            f"{chunk.content}\n"
        )

    return "\n---\n".join(results)


# Export available tools
AGENT_TOOLS = [hybrid_search_tool, metadata_filter_tool]
