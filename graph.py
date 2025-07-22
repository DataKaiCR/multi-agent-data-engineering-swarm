from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from config import PipelineStep, MODELS


class AgentState(TypedDict):  # Shared state for scalability
    task: str
    refined_prompt: str
    pipeline_steps: List[PipelineStep]
    debate_rounds: int
    consensus_reached: bool


# Placeholder nodes - simplified for working implementation
def prompt_node(state: AgentState) -> AgentState:
    # Simple prompt refinement for now
    state["refined_prompt"] = f"Refined: {state['task']}"
    return state


def ingest_node(state: AgentState) -> AgentState:
    # Only add if we don't already have this step
    existing_steps = [s.step_name for s in state["pipeline_steps"]]
    if "data_ingestion" not in existing_steps:
        step = PipelineStep(
            step_name="data_ingestion",
            code_snippet="df = pd.read_csv('data/sales_data.csv')",
            rationale="Load the dataset for processing"
        )
        state["pipeline_steps"].append(step)
    return state


def clean_node(state: AgentState) -> AgentState:
    # Only add if we don't already have this step  
    existing_steps = [s.step_name for s in state["pipeline_steps"]]
    if "data_cleaning" not in existing_steps:
        step = PipelineStep(
            step_name="data_cleaning",
            code_snippet="df = df.dropna()",
            rationale="Remove missing values from dataset"
        )
        state["pipeline_steps"].append(step)
    return state


def transform_node(state: AgentState) -> AgentState:
    # Only add if we don't already have this step
    existing_steps = [s.step_name for s in state["pipeline_steps"]]
    if "data_transformation" not in existing_steps:
        step = PipelineStep(
            step_name="data_transformation",
            code_snippet="df['processed'] = df['amount'] * 1.1",
            rationale="Apply business logic transformation"
        )
        state["pipeline_steps"].append(step)
    return state


def debate_node(state: AgentState) -> AgentState:
    # Simplified consensus mechanism
    state["consensus_reached"] = len(state["pipeline_steps"]) >= 3  # Simple rule
    state["debate_rounds"] = state.get("debate_rounds", 0) + 1
    return state


# Conditional edge: If not consensus and <5 rounds, loop to refine/ingest  
def route(state: AgentState):
    if state["consensus_reached"] or state.get("debate_rounds", 0) > 2:  # Lower threshold to prevent too many loops
        return END
    return "prompt"  # Loop back to prompt for refinement


graph = StateGraph(state_schema=AgentState)
graph.add_node("prompt", prompt_node)
graph.add_node("ingest", ingest_node)
graph.add_node("clean", clean_node)
graph.add_node("transform", transform_node)
graph.add_node("debate", debate_node)

# Set entry point
graph.set_entry_point("prompt")

# Edges: Sequential then cycle
graph.add_edge("prompt", "ingest")
graph.add_edge("ingest", "clean")
graph.add_edge("clean", "transform")
graph.add_edge("transform", "debate")
graph.add_conditional_edges("debate", route, {"prompt": "prompt", END: END})

app = graph.compile()
