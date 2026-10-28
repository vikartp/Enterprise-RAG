"""LLM-powered chunk enrichment: summaries, keywords, and hypothetical questions."""

from __future__ import annotations

import json
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import ChunkData, EnrichedChunk

# Prompt template for chunk enrichment
ENRICHMENT_PROMPT = """You are a document analysis assistant. Given a text chunk from a document, generate structured metadata.

## Input Chunk
{chunk_text}

## Instructions
Analyze the chunk and produce the following in JSON format:
1. **summary**: A concise 1-2 sentence summary of the chunk's key information.
2. **keywords**: A list of 3-7 important keywords/terms from the chunk.
3. **hypothetical_questions**: A list of 2-3 questions that this chunk would be the ideal answer for. These questions should be natural and diverse — imagine what a user might ask that would lead them to need this exact information.

## Output Format (strict JSON)
{{
  "summary": "...",
  "keywords": ["...", "..."],
  "hypothetical_questions": ["...", "...", "..."]
}}

Respond ONLY with the JSON object, no additional text."""


async def enrich_chunks(
    chunks: list[ChunkData],
    batch_size: int = 5,
) -> list[EnrichedChunk]:
    """
    Enrich chunks with LLM-generated metadata.

    For each chunk, an LLM call generates:
    - A concise summary
    - Extracted keywords
    - 2-3 hypothetical questions the chunk answers

    Args:
        chunks: List of raw chunks to enrich.
        batch_size: Number of concurrent LLM calls (for rate limiting).

    Returns:
        List of EnrichedChunk objects with generated metadata.
    """
    import asyncio

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    enriched: list[EnrichedChunk] = []

    # Process in batches to respect rate limits
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        tasks = [_enrich_single_chunk(client, chunk, settings.llm_model) for chunk in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for chunk, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                # Fallback: create enriched chunk without LLM metadata
                enriched.append(EnrichedChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    source_file=chunk.source_file,
                    section_header=chunk.section_header,
                    summary=f"Chunk from {chunk.source_file}, section: {chunk.section_header or 'N/A'}",
                    keywords=[],
                    hypothetical_questions=[],
                ))
            else:
                enriched.append(result)

    return enriched


async def _enrich_single_chunk(
    client: AsyncOpenAI,
    chunk: ChunkData,
    model: str,
) -> EnrichedChunk:
    """Enrich a single chunk via LLM call with structured output."""
    prompt = ENRICHMENT_PROMPT.format(chunk_text=chunk.content)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise document analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=500,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {}

    return EnrichedChunk(
        chunk_id=chunk.chunk_id,
        content=chunk.content,
        chunk_index=chunk.chunk_index,
        source_file=chunk.source_file,
        section_header=chunk.section_header,
        summary=data.get("summary", ""),
        keywords=data.get("keywords", []),
        hypothetical_questions=data.get("hypothetical_questions", []),
    )
