"""Ingestion API router — file upload with SSE pipeline progress."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, File, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.ingestion.chunker import chunk_elements
from app.ingestion.enricher import enrich_chunks
from app.ingestion.parser import parse_file
from app.retrieval.qdrant_store import index_chunks
from app.schemas import IngestionEvent, IngestionPhase, PhaseStatus

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".csv"}


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload and process a document through the ingestion pipeline.

    Streams SSE events reporting progress through each phase:
    1. Parsing — Layout-aware document parsing
    2. Chunking — Structure-aware chunking
    3. Enrichment — LLM metadata generation
    4. Indexing — Qdrant vector storage

    Accepted file types: PDF, Markdown, TXT, CSV
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    settings = get_settings()
    max_size = settings.max_file_size_mb * 1024 * 1024
    content = await file.read()

    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    async def event_stream() -> AsyncGenerator[dict, None]:
        """Generate SSE events as the pipeline processes the document."""
        filename = file.filename or "unknown"

        try:
            # Phase 1: Parsing
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.PARSING,
                status=PhaseStatus.IN_PROGRESS,
                message=f"Parsing {filename}...",
            ))

            elements = await parse_file(content, filename)

            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.PARSING,
                status=PhaseStatus.COMPLETE,
                message=f"Parsed {len(elements)} elements from {filename}",
            ))

            # Phase 2: Chunking
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.CHUNKING,
                status=PhaseStatus.IN_PROGRESS,
                message="Performing structure-aware chunking...",
            ))

            chunks = await chunk_elements(elements, filename)

            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.CHUNKING,
                status=PhaseStatus.COMPLETE,
                message=f"Created {len(chunks)} chunks",
                chunks=chunks,
            ))

            # Phase 3: Enrichment
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.ENRICHMENT,
                status=PhaseStatus.IN_PROGRESS,
                message="Generating summaries and hypothetical questions...",
            ))

            enriched = await enrich_chunks(chunks)

            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.ENRICHMENT,
                status=PhaseStatus.COMPLETE,
                message=f"Enriched {len(enriched)} chunks with metadata",
                enriched_chunks=enriched,
            ))

            # Phase 4: Indexing
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.INDEXING,
                status=PhaseStatus.IN_PROGRESS,
                message="Indexing into Qdrant with dense + sparse vectors...",
            ))

            point_ids = await index_chunks(enriched)

            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.INDEXING,
                status=PhaseStatus.COMPLETE,
                message=f"Indexed {len(point_ids)} vectors into Qdrant",
                point_ids=point_ids,
            ))

            # Complete
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.COMPLETE,
                status=PhaseStatus.COMPLETE,
                message=f"Successfully processed {filename}: {len(chunks)} chunks indexed",
                enriched_chunks=enriched,
                point_ids=point_ids,
            ))

        except Exception as e:
            yield _sse_event(IngestionEvent(
                phase=IngestionPhase.ERROR,
                status=PhaseStatus.ERROR,
                message="Pipeline failed",
                error=str(e),
            ))

    return EventSourceResponse(event_stream())


def _sse_event(event: IngestionEvent) -> dict:
    """Format an IngestionEvent as an SSE-compatible dict."""
    return {
        "event": event.phase.value,
        "data": event.model_dump_json(),
    }
