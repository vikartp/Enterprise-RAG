"""Planner agent — decomposes complex queries into sub-tasks."""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.schemas import PlanStep

PLANNER_SYSTEM_PROMPT = """You are an expert query planner for a RAG (Retrieval-Augmented Generation) system.

Your job is to analyze the user's question and determine the best retrieval strategy.

## Capabilities
You have access to these tools:
1. **hybrid_search_tool**: Search the knowledge base using semantic + keyword hybrid search. Use for general information retrieval.
2. **metadata_filter_tool**: Search with filters (by source file or keywords). Use when the user references specific documents or topics.

## Planning Rules
1. For simple, single-topic questions: Use ONE hybrid_search_tool call.
2. For complex, multi-part questions: Decompose into 2-4 sub-queries, each with its own search.
3. For questions about specific files: Use metadata_filter_tool with the filename.
4. Always plan to SYNTHESIZE results from all sub-queries into a coherent answer.

## Output
Respond with your reasoning about how to approach the query, then execute the appropriate tools."""


def get_planner_llm() -> ChatOpenAI:
    """Create the planner LLM instance."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.0,
        streaming=True,
    )


def get_planner_system_message() -> SystemMessage:
    """Get the planner system message."""
    return SystemMessage(content=PLANNER_SYSTEM_PROMPT)
