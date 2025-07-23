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
from agents.gap_resolver import resolve_persistent_gaps
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
import functools
import structlog

def calculate_semantic_similarity(gaps1, gaps2):
    """Calculate semantic similarity between gap sets using keyword overlap"""
    keywords1, keywords2 = set(), set()
    key_terms = ["validation", "error", "handling", "transformation", "missing", "data", "pipeline", "quality", "incomplete"]
    
    for gap in gaps1:
        keywords1.update(term for term in key_terms if term in gap.lower())
    for gap in gaps2:
        keywords2.update(term for term in key_terms if term in gap.lower())
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)
    return intersection / union if union > 0 else 0.0

# Debate Configuration
MAX_DEBATE_ROUNDS = 3  # Maximum number of consensus rounds before force-exit (LangGraph has 25-step limit)
VOTING_MODELS = [
    "validator",
    "cleaner",
    "transformer",
]  # Models that participate in voting
CONSENSUS_THRESHOLD = 0.5  # Fraction of votes needed for consensus (majority)


class AgentState(TypedDict):
    task: str
    refined_prompt: str
    pipeline_steps: List[PipelineStep]
    debate_rounds: int = 0
    consensus_reached: bool = False
    discovered_tools: Dict[
        str, str
    ] = {}  # New: Dynamic tool map (e.g., {"ingest": "load_csv"})
    feedback_summary: str = ""  # Aggregated feedback from all agents
    feedback_history: List[str] = []  # Raw feedback for trend analysis
    gap_escalation_count: int = 0  # Track escalations to prevent infinite loops
    current_data_path: str = "data/sales_data.csv"  # Track current dataset file path
    data_format: str = "csv"  # Track current data format (csv, parquet, etc.)
    pipeline_metadata: Dict[str, str] = {}  # Track metadata between agents


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
    task_with_feedback = state["task"]
    if state["feedback_summary"]:
        task_with_feedback = f"{state['feedback_summary']}\n\nOriginal Task: {task_with_feedback}\n\nIMPORTANT: Address the gaps above in your refinements."
    refined = await refine_prompt(task_with_feedback)
    state["refined_prompt"] = refined.rationale
    state["pipeline_steps"].append(refined)
    return state


@hybrid_async_node
async def ingest_node(state: AgentState) -> AgentState:
    # Pass feedback context to help ingestor adapt to validation gaps
    step = await ingest_data(
        state["current_data_path"], 
        state.get("feedback_summary", ""),
        state["data_format"]
    )
    state["pipeline_steps"].append(step)
    
    # Update pipeline state with ingestor's output
    if step.output_file_path:
        state["current_data_path"] = step.output_file_path
        state["data_format"] = step.output_format
        state["pipeline_metadata"]["last_ingest_output"] = step.output_file_path
    
    return state


@hybrid_async_node
async def clean_node(state: AgentState) -> AgentState:
    last_step = state["pipeline_steps"][-1]  # This should be the ingest step
    # Pass feedback context and current data path to help cleaner adapt
    step = await clean_data(
        state["current_data_path"], 
        last_step, 
        state.get("feedback_summary", ""),
        state["data_format"]
    )
    state["pipeline_steps"].append(step)
    
    # Update pipeline state with cleaner's output
    if step.output_file_path:
        state["current_data_path"] = step.output_file_path
        state["data_format"] = step.output_format
        state["pipeline_metadata"]["last_clean_output"] = step.output_file_path
    
    return state


@hybrid_async_node
async def transform_node(state: AgentState) -> AgentState:
    last_step = state["pipeline_steps"][-1]  # This should be the clean step
    # Pass feedback context and current data path to help transformer adapt
    step = await transform_data(
        state["current_data_path"], 
        last_step, 
        state.get("feedback_summary", ""),
        state["data_format"]
    )
    state["pipeline_steps"].append(step)
    
    # Update pipeline state with transformer's output
    if step.output_file_path:
        state["current_data_path"] = step.output_file_path
        state["data_format"] = step.output_format
        state["pipeline_metadata"]["last_transform_output"] = step.output_file_path
    
    return state


@hybrid_async_node
async def debate_node(state: AgentState) -> AgentState:
    logger = structlog.get_logger('pipeline')
    logger.info("debate_node_started", round=state["debate_rounds"] + 1)
    
    step, votes = await validate_steps(state["pipeline_steps"], state["refined_prompt"])
    state["pipeline_steps"].append(step)
    state["debate_rounds"] += 1

    # Proper consensus detection based on validator's actual majority vote
    state["consensus_reached"] = sum(1 for v in votes if "Yes" in v) > len(votes) / 2

    # Enhanced gap extraction from structured votes
    gaps = set()
    for vote in votes:
        if vote["vote"] == "No":
            # Extract gaps from rationale using improved keyword matching
            rationale = vote["rationale"].lower()
            gap_keywords = ["missing", "lacks", "incomplete", "should include", "needs", "requires", "absent"]
            for line in rationale.split("."):
                if any(keyword in line for keyword in gap_keywords):
                    gaps.add(line.strip())
    
    # Create compact feedback summary
    unique_gaps = list(gaps)[:5]  # Limit to top 5 for token efficiency
    state["feedback_summary"] = "MUST address these gaps: " + "; ".join(unique_gaps) if unique_gaps else ""
    
    # Store raw feedback for escalation detection
    current_feedback = "; ".join(unique_gaps)
    state["feedback_history"].append(current_feedback)
    
    # Check for persistent gaps (escalation trigger)
    if len(state["feedback_history"]) > 2 and state["gap_escalation_count"] < 2:
        recent_feedback = state["feedback_history"][-3:]
        # Semantic similarity check for persistent gap patterns
        recent_gaps = [set(feedback.split(";")) for feedback in recent_feedback if feedback]
        if len(recent_gaps) >= 2:
            similarity = calculate_semantic_similarity(recent_gaps[0], recent_gaps[-1])
            if similarity > 0.3 and len(unique_gaps) > 0:
                logger.info("persistent_gaps_detected", 
                           similarity=similarity, 
                           gap_count=len(unique_gaps),
                           escalation_count=state["gap_escalation_count"])
                print(f"🔄 Persistent gaps detected (similarity: {similarity:.2f}). Triggering meta-swarmlet resolver...")
                state["gap_escalation_count"] += 1
                
                # Escalate to gap resolver (async for scalability)
                resolver_step = await resolve_persistent_gaps(
                    gaps=current_feedback,
                    context=state["refined_prompt"],
                    history=state["feedback_history"]
                )
                state["pipeline_steps"].append(resolver_step)
                logger.info("gap_resolver_generated", 
                           step_name=resolver_step.step_name,
                           output_format=resolver_step.output_format)
                print(f"🛠️ Gap resolver generated: {resolver_step.step_name}")
                
                # INTRA-ROUND VALIDATION: Immediately validate the resolver solution
                logger.info("intra_round_validation_started")
                print("🔍 Intra-round validation: Testing resolver solution...")
                from agents.validator import validate_pipeline
                validation_result = await validate_pipeline(
                    pipeline_steps=state["pipeline_steps"],
                    task=state["task"]
                )
                
                logger.info("intra_round_validation_completed",
                           consensus_reached=validation_result.consensus_reached,
                           vote_count=validation_result.vote_count)
                
                if validation_result.consensus_reached:
                    print("✅ Resolver solution passed immediate validation!")
                    state["consensus_reached"] = True
                    state["feedback_summary"] = f"Resolver solution validated: {resolver_step.step_name}"
                else:
                    print(f"⚠️ Resolver solution needs refinement: {validation_result.rationale[:100]}...")
                    state["feedback_summary"] = f"Resolver applied but needs refinement: {validation_result.rationale[:200]}"
    return state


# Conditional routing: Loop if no consensus (scalable: Max rounds prevent infinite loops)
def route(state: AgentState) -> str:
    if state["consensus_reached"]:
        return END
    elif state["debate_rounds"] >= MAX_DEBATE_ROUNDS:
        print(
            f"\n⚠️  Maximum debate rounds ({MAX_DEBATE_ROUNDS}) reached. Forcing consensus..."
        )
        return END
    return "prompt"  # Re-refine; dynamic: Route to weak agent based on discovered tools


# Build graph (async nodes for parallel scalability in large swarms)
graph = StateGraph(state_schema=AgentState, initial_state={
    'feedback_history': [], 
    'gap_escalation_count': 0,
    'current_data_path': 'data/sales_data.csv',
    'data_format': 'csv',
    'pipeline_metadata': {}
})
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
