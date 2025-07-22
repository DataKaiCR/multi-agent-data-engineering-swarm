from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from config import PipelineStep


class AgentState(TypedDict):  # Shared state for scalability
    task: str
    refined_prompt: str
    pipeline_steps: List[PipelineStep]
    debate_rounds: int = 0
    consensus_reached: bool = False


# Nodes: Functions calling agents
def prompt_node(state: AgentState) -> AgentState:
    state["refined_prompt"] = refine_prompt(state["task"]).rationale
    return state


def ingest_node(state: AgentState) -> AgentState:
    # RAG retrieve + ingest logic
    step = ingest_data(state["refined_prompt"])  # Your impl
    state["pipeline_steps"].append(step)
    return state


# Add cleaner, transformer nodes similarly


def debate_node(state: AgentState) -> AgentState:
    # Multi-model debate: Call different models to vote
    votes = []
    for model in ["creative_insights", "orchestrator"]:
        vote = MODELS[model].invoke(
            f"Evaluate steps: {state['pipeline_steps']}. Vote yes/no."
        )
        votes.append(vote)
    state["consensus_reached"] = len([v for v in votes if "yes" in v]) > len(votes) / 2
    state["debate_rounds"] += 1
    return state


# Conditional edge: If not consensus and <5 rounds, loop to refine/ingest
def route(state: AgentState):
    if state["consensus_reached"] or state["debate_rounds"] > 5:
        return END
    return "refine"  # Or dynamic: to specific nodes


graph = StateGraph(state_schema=AgentState)
graph.add_node("prompt", prompt_node)
graph.add_node("ingest", ingest_node)
graph.add_node("clean", clean_node)  # Define similarly
graph.add_node("transform", transform_node)
graph.add_node("debate", debate_node)

# Edges: Sequential then cycle
graph.add_edge("prompt", "ingest")
graph.add_edge("ingest", "clean")
graph.add_edge("clean", "transform")
graph.add_edge("transform", "debate")
graph.add_conditional_edges("debate", route, {"refine": "prompt", END: END})

app = graph.compile()
