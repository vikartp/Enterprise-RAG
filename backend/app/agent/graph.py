"""LangGraph state graph — agentic RAG orchestration with validation loop."""

from __future__ import annotations

import json
from typing import Annotated, Any, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agent.planner import get_planner_llm, get_planner_system_message
from app.agent.tools import AGENT_TOOLS
from app.schemas import PlanStep, ValidationResult
from app.validation.gatekeeper import validate_gatekeeper
from app.validation.auditor import validate_auditor
from app.validation.strategist import validate_strategist


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """State carried through the LangGraph agent execution."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    plan_steps: list[PlanStep]
    retrieved_context: str
    validation_results: list[ValidationResult]
    retry_count: int
    final_answer: str


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

async def plan_node(state: AgentState) -> dict:
    """
    Planning node — the LLM analyzes the query and decides what tools to call.
    This is the 'brain' of the agentic RAG system.
    """
    llm = get_planner_llm()
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    # Ensure system message is first
    messages = list(state["messages"])
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, get_planner_system_message())

    response = await llm_with_tools.ainvoke(messages)

    # Track plan steps
    plan_steps = list(state.get("plan_steps", []))
    if response.tool_calls:
        for i, tc in enumerate(response.tool_calls):
            plan_steps.append(PlanStep(
                step_index=len(plan_steps),
                description=f"Call {tc['name']} with query",
                tool=tc["name"],
                tool_input=tc.get("args", {}),
                status="executing",
            ))
    else:
        plan_steps.append(PlanStep(
            step_index=len(plan_steps),
            description="Generate final answer from context",
            status="executing",
        ))

    return {"messages": [response], "plan_steps": plan_steps}


async def generate_node(state: AgentState) -> dict:
    """
    Generation node — synthesize retrieved context into a final answer.
    Called after all tools have returned their results.
    """
    llm = get_planner_llm()

    # Collect all tool results as context
    context_parts = []
    for msg in state["messages"]:
        if isinstance(msg, ToolMessage):
            context_parts.append(msg.content)

    retrieved_context = "\n\n---\n\n".join(context_parts) if context_parts else ""

    # Generate final answer
    gen_messages = [
        SystemMessage(content=(
            "You are a helpful assistant answering questions based on retrieved documents. "
            "Base your answer STRICTLY on the provided context. "
            "If the context doesn't contain enough information, say so clearly. "
            "Cite source files when possible."
        )),
        HumanMessage(content=(
            f"## Retrieved Context\n{retrieved_context}\n\n"
            f"## User Question\n{state['messages'][1].content if len(state['messages']) > 1 else ''}\n\n"
            "Please provide a comprehensive answer based on the context above."
        )),
    ]

    response = await llm.ainvoke(gen_messages)

    return {
        "messages": [response],
        "retrieved_context": retrieved_context,
        "final_answer": response.content,
    }


async def validate_node(state: AgentState) -> dict:
    """
    Validation node — run the three validation checks on the generated answer.
    """
    query = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    answer = state.get("final_answer", "")
    context = state.get("retrieved_context", "")

    # Run all three validators
    gatekeeper_result = await validate_gatekeeper(query, answer)
    auditor_result = await validate_auditor(query, answer, context)
    strategist_result = await validate_strategist(query, answer)

    validation_results = [gatekeeper_result, auditor_result, strategist_result]

    return {"validation_results": validation_results}


# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------

def should_continue(state: AgentState) -> str:
    """Decide whether to continue tool calling or move to generation."""
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "generate"


def should_retry_or_finish(state: AgentState) -> str:
    """Check validation results — retry if any critical check fails."""
    validation_results = state.get("validation_results", [])
    retry_count = state.get("retry_count", 0)

    # Don't retry more than twice
    if retry_count >= 2:
        return "end"

    # Check if all validators passed
    all_passed = all(v.passed for v in validation_results)

    if all_passed:
        return "end"

    # If gatekeeper or auditor failed, retry retrieval
    for v in validation_results:
        if not v.passed and v.validator in ("gatekeeper", "auditor"):
            return "retry"

    return "end"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph state graph for agentic RAG.

    Flow:
    plan → [tools → plan]* → generate → validate → [retry → plan]* → end
    """
    tool_node = ToolNode(AGENT_TOOLS)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("plan", plan_node)
    graph.add_node("tools", tool_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)

    # Set entry point
    graph.set_entry_point("plan")

    # Conditional edge: plan → tools or generate
    graph.add_conditional_edges(
        "plan",
        should_continue,
        {"tools": "tools", "generate": "generate"},
    )

    # tools → plan (for iterative tool calling)
    graph.add_edge("tools", "plan")

    # generate → validate
    graph.add_edge("generate", "validate")

    # validate → end or retry
    graph.add_conditional_edges(
        "validate",
        should_retry_or_finish,
        {"end": END, "retry": "plan"},
    )

    return graph


# Compiled graph (singleton)
_compiled_graph = None


def get_agent_graph():
    """Get or compile the agent graph."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_agent_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph
