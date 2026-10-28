"""Query API router — agentic RAG with SSE streaming."""

from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import AgentState, get_agent_graph
from app.schemas import (
    ChatMessage,
    PlanStep,
    QueryEvent,
    QueryEventType,
    QueryRequest,
    RetrievedChunk,
    ValidationResult,
)

router = APIRouter()


@router.post("/query")
async def query_documents(request: QueryRequest):
    """
    Process a user query through the agentic RAG pipeline.

    Streams SSE events interleaving:
    - plan: Agent's reasoning plan and tool calls
    - retrieval: Retrieved chunks with hybrid search scores
    - token: Streaming response tokens
    - validation: Gatekeeper/Auditor/Strategist results
    - complete: Final signal

    Args:
        request: QueryRequest with query string and optional history/filters.
    """

    async def event_stream() -> AsyncGenerator[dict, None]:
        """Run the agentic RAG graph and stream events."""
        graph = get_agent_graph()

        # Build initial messages from history + new query
        messages = []
        for msg in request.history:
            if msg.role.value == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role.value == "assistant":
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=request.query))

        # Initial state
        initial_state: AgentState = {
            "messages": messages,
            "plan_steps": [],
            "retrieved_context": "",
            "validation_results": [],
            "retry_count": 0,
            "final_answer": "",
        }

        try:
            # Stream through graph nodes
            async for event in graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name == "plan":
                        # Emit plan steps
                        plan_steps = node_output.get("plan_steps", [])
                        yield _sse_event(QueryEvent(
                            type=QueryEventType.PLAN,
                            plan_steps=plan_steps,
                        ))

                    elif node_name == "tools":
                        # Emit retrieval results (parse from tool messages)
                        msgs = node_output.get("messages", [])
                        for msg in msgs:
                            if isinstance(msg, ToolMessage):
                                yield _sse_event(QueryEvent(
                                    type=QueryEventType.RETRIEVAL,
                                    content=msg.content[:2000],  # Truncate for SSE
                                ))

                    elif node_name == "generate":
                        # Emit the generated answer as a token stream
                        answer = node_output.get("final_answer", "")
                        if answer:
                            # Simulate token streaming for SSE
                            # (In production, use actual streaming from LLM)
                            words = answer.split(" ")
                            chunk_size = 5
                            for i in range(0, len(words), chunk_size):
                                token_chunk = " ".join(words[i : i + chunk_size])
                                if i > 0:
                                    token_chunk = " " + token_chunk
                                yield _sse_event(QueryEvent(
                                    type=QueryEventType.TOKEN,
                                    content=token_chunk,
                                ))

                    elif node_name == "validate":
                        # Emit validation results
                        results = node_output.get("validation_results", [])
                        yield _sse_event(QueryEvent(
                            type=QueryEventType.VALIDATION,
                            validation=results,
                        ))

            # Complete
            yield _sse_event(QueryEvent(
                type=QueryEventType.COMPLETE,
                content="",
            ))

        except Exception as e:
            yield _sse_event(QueryEvent(
                type=QueryEventType.ERROR,
                error=str(e),
            ))

    return EventSourceResponse(event_stream())


def _sse_event(event: QueryEvent) -> dict:
    """Format a QueryEvent as an SSE-compatible dict."""
    return {
        "event": event.type.value,
        "data": event.model_dump_json(),
    }
