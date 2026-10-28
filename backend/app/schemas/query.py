"""Pydantic schemas for query / chat pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: MessageRole
    content: str


class QueryRequest(BaseModel):
    """Incoming query request from the frontend."""

    query: str = Field(..., description="User's question")
    history: list[ChatMessage] = Field(default_factory=list, description="Conversation history")
    filters: dict[str, Any] = Field(default_factory=dict, description="Optional metadata filters")


class RetrievedChunk(BaseModel):
    """A retrieved chunk with hybrid search scores."""

    chunk_id: str
    content: str
    source_file: str
    section_header: Optional[str] = None
    summary: str = ""
    hypothetical_questions: list[str] = Field(default_factory=list)
    dense_score: float = Field(0.0, description="Dense (semantic) similarity score")
    sparse_score: float = Field(0.0, description="Sparse (BM25) score")
    rrf_score: float = Field(0.0, description="Reciprocal Rank Fusion score")
    reranker_score: float = Field(0.0, description="Cross-Encoder reranker score")


class PlanStep(BaseModel):
    """A single step in the agent's reasoning plan."""

    step_index: int
    description: str
    tool: Optional[str] = None
    tool_input: Optional[dict] = None
    status: str = "pending"  # pending | executing | complete | error
    result: Optional[str] = None


class ValidationResult(BaseModel):
    """Result from a validation node."""

    validator: str = Field(..., description="gatekeeper | auditor | strategist")
    passed: bool
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reason: str = ""


class QueryEventType(str, Enum):
    """Types of SSE events emitted during query processing."""

    PLAN = "plan"
    RETRIEVAL = "retrieval"
    TOKEN = "token"
    VALIDATION = "validation"
    COMPLETE = "complete"
    ERROR = "error"


class QueryEvent(BaseModel):
    """SSE event sent during query processing."""

    type: QueryEventType
    plan_steps: list[PlanStep] = Field(default_factory=list)
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    content: str = ""
    validation: list[ValidationResult] = Field(default_factory=list)
    error: Optional[str] = None
