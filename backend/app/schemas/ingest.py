"""Pydantic schemas for the ingestion pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IngestionPhase(str, Enum):
    """Pipeline phases for document ingestion."""

    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    ENRICHMENT = "enrichment"
    INDEXING = "indexing"
    COMPLETE = "complete"
    ERROR = "error"


class PhaseStatus(str, Enum):
    """Status of a pipeline phase."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"


class ParsedElement(BaseModel):
    """A single parsed element from a document."""

    element_type: str = Field(..., description="Type: heading, paragraph, table, code, list")
    content: str = Field(..., description="Text content of the element")
    metadata: dict = Field(default_factory=dict, description="Element-level metadata")


class ChunkData(BaseModel):
    """A single chunk extracted from parsed elements."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Position in the document")
    source_file: str = Field(..., description="Original filename")
    section_header: Optional[str] = Field(None, description="Parent section heading")
    token_count: int = Field(0, description="Token count of the chunk")


class EnrichedChunk(BaseModel):
    """A chunk enriched with LLM-generated metadata."""

    chunk_id: str
    content: str
    chunk_index: int
    source_file: str
    section_header: Optional[str] = None
    summary: str = Field("", description="LLM-generated summary")
    keywords: list[str] = Field(default_factory=list, description="Extracted keywords")
    hypothetical_questions: list[str] = Field(
        default_factory=list, description="2-3 hypothetical questions this chunk answers"
    )


class IngestionEvent(BaseModel):
    """SSE event sent during ingestion pipeline."""

    phase: IngestionPhase
    status: PhaseStatus
    message: str = ""
    chunks: list[ChunkData] = Field(default_factory=list)
    enriched_chunks: list[EnrichedChunk] = Field(default_factory=list)
    point_ids: list[str] = Field(default_factory=list)
    error: Optional[str] = None
