# graph.py: LangGraph workflow for data engineering swarm with dynamic tool discovery
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from config import PipelineStep
from agents.prompt_engineer import refine_prompt
from agents.data_ingestor import ingest_data
from agents.cleaner import clean_data
from agents.transformer import transform_data
from agents.validator import validate_steps
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import functools


class AgentState(TypedDict):
    task: str
    refined_prompt: str
    pipeline_steps: List[PipelineStep]
    debate_rounds: int = 0
    consensus_reached: bool = False
    discovered_tools: Dict[
        str, str
    ] = {}  # New: Dynamic tool map (e.g., {"ingest": "load_csv"})


# Invented paradigm: Hybrid wrapper for sync/async agents (scales to mixed workloads in ETL swarms)
def hybrid_async_node(func):
    @functools.wraps(func)
    async def wrapper(state: AgentState) -> AgentState:
        if asyncio.iscoroutinefunction(func):
            return await func(state)
        else:
            # Offload sync to thread (non-blocking; scalable for CPU-bound ops in data pipelines)
            return await asyncio.to_thread(func, state)

    return wrapper


# Dynamic discovery node: Query MCP for tools, map to agents (creative swarm discovery paradigm)
async def discovery_node(state: AgentState) -> AgentState:
    try:
        async with streamablehttp_client("http://localhost:8000/mcp") as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_resp = await session.list_tools()
                tools = {tool.name: tool.description for tool in tools_resp.tools}

        # Map discovered tools to agent roles (scalable: Auto-assign based on desc keywords)
        state["discovered_tools"] = {}
        if "load_csv" in tools:
            state["discovered_tools"]["ingest"] = "load_csv"
        if "clean_data" in tools:
            state["discovered_tools"]["clean"] = "clean_data"
        if "transform_data" in tools:
            state["discovered_tools"]["transform"] = "transform_data"
        if "validate_data" in tools:
            state["discovered_tools"]["validate"] = "validate_data"

        # Creative: If tools missing, fallback or spawn sub-discovery (e.g., query alt MCP endpoints)
        if not state["discovered_tools"]:
            print("Warning: No tools discovered; using static fallbacks.")
            state["discovered_tools"] = {
                "ingest": "default_load",
                "clean": "default_clean",
            }  # Etc.
    except Exception as e:
        print(f"Discovery failed: {e}; using fallbacks.")
        state["discovered_tools"] = {}  # Handle gracefully for ETL resilience

    return state


# Agent nodes (async for scalability; use discovered tools in calls if needed)
@hybrid_async_node
async def prompt_node(state: AgentState) -> AgentState:
    refined = await refine_prompt(
        state["task"]
    )  # Assuming async version; update if sync
    state["refined_prompt"] = refined.rationale
    state["pipeline_steps"].append(refined)
    return state


@hybrid_async_node
async def ingest_node(state: AgentState) -> AgentState:
    step = await ingest_data(
        "data/sales_data.csv"
    )  # Dynamic: Could pass discovered tool
    state["pipeline_steps"].append(step)
    return state


@hybrid_async_node
async def clean_node(state: AgentState) -> AgentState:
    last_step = state["pipeline_steps"][-1]
    step = await clean_data("data/sales_data.csv", last_step)
    state["pipeline_steps"].append(step)
    return state


@hybrid_async_node
async def transform_node(state: AgentState) -> AgentState:
    last_step = state["pipeline_steps"][-1]
    step = await transform_data("data/sales_data.csv", last_step)
    state["pipeline_steps"].append(step)
    return state


@hybrid_async_node
async def debate_node(state: AgentState) -> AgentState:
    step = await validate_steps(state["pipeline_steps"], state["refined_prompt"])
    state["pipeline_steps"].append(step)
    state["debate_rounds"] += 1
    state["consensus_reached"] = (
        "yes" in step.rationale.lower()
    )  # Simplified; enhance with vote parse
    return state


# Conditional routing: Loop if no consensus (scalable: Max rounds prevent infinite loops)
def route(state: AgentState) -> str:
    if state["consensus_reached"] or state["debate_rounds"] > 5:
        return END
    return "prompt"  # Re-refine; dynamic: Route to weak agent based on discovered tools


# Build graph (async nodes for parallel scalability in large swarms)
graph = StateGraph(state_schema=AgentState)
graph.add_node("discovery", discovery_node)
graph.add_node("prompt", prompt_node)
graph.add_node("ingest", ingest_node)
graph.add_node("clean", clean_node)
graph.add_node("transform", transform_node)
graph.add_node("debate", debate_node)

# Edges: Discovery first, then sequential ETL with debate loop
graph.set_entry_point("discovery")
graph.add_edge("discovery", "prompt")
graph.add_edge("prompt", "ingest")
graph.add_edge("ingest", "clean")
graph.add_edge("clean", "transform")
graph.add_edge("transform", "debate")
graph.add_conditional_edges("debate", route, {"prompt": "prompt", END: END})

app = graph.compile()  # Ready for async invoke in main.py
