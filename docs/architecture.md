# Architecture Overview

## High-Level Design
- **Core Framework:** LangGraph for graph-based workflows (nodes: agents, edges: conditional routes for iteration).
- **Agents:** Semi-autonomous units with roles:
  - Prompt Engineer: Refines user inputs (Deepseek-powered).
  - Data Ingestor: Retrieves/loads data with RAG (OpenAI embeddings + Chroma)
  - Cleaner: Handles missing values, outliers (Claude for reasoning).
  - Transformer: Feature engineering, transformations (Grok for creative approaches).
  - Validator/Debater: Consensus via multi-model voting (Claude + CodeLlama + locals).
- **Shared State:** TypedDict in LangGraph for passing pipeline steps, debate history.
- **Tools & Protocols:** MCP (via FastMCP) for standardized tool calls (e.g., data validators); Custom tools for data ops with Pydantic structures.
- **Iteration Loop:** Debate node triggers re-routes until consensus or max rounds.
- **Novel Element:** Dynamic sub-swarm spawning: If a task exceeds complexity threshold, spawn parallel agents (e.g., for sharded data processing). Extended with MCP for tool discovery.

## Data Flow Example
1. User inputs task: "Build pipeline for sales_data.csv".
2. Prompt Engineer refines it.
3. Ingestor loads data + RAG for schemas (using MCP tools).
4. Sequential agents build steps.
5. Validator evalutes/debates; loops if needed.
6. Output: Structured pipeline (Pydantic-enforced JSON/code snippets).

## Scalability Features
- **Parallelism:** LangGraph async nodes for concurrent agent execution.
- **Fault Tolerance:** Model fallbacks (e.g., API down → local).
- **Monitoring:** LangSmith traces all interactions.
- **Extension Points:** Hooks for cloud integration (e.g., S3 for large data);
MCP servers for dynamic tools.

## Project Structure
```
multi-agent-data-engineering-swarm/
├── agents/                # Agent logic
│   ├── prompt_engineer.py
│   ├── data_ingestor.py
│   ├── cleaner.py
│   ├── transformer.py
│   └── validator.py
├── tools/                 # MCP-wrapped tools
│   └── data_tools.py      # E.g., validators, loaders
├── graph.py               # LangGraph workflow
├── config.py              # Models, Pydantic schemas, keys
├── main.py                # Entry point
├── pyproject.toml         # Dependencies
├── data/                  # Datasets & indexes
│   └── sales_data.csv     # Sample
└── indexes/               # Chroma for RAG
```

## Key Components

### Config & Pydantic Contracts (`config.py`)
The configuration system uses Pydantic for type safety and supports multiple LLM providers with fallback handling.

### Agent Examples
- **Prompt Engineer (`agents/prompt_engineer.py`):** Uses chain to refine prompts.
- **Data Ingestor (`agents/data_ingestor.py`):** Integrates MCP tools.
- **Validator (`agents/validator.py`):** Handles consensus/debate. Uses
multi-model voting on pipeline steps, integrating MCP tools for validation (e.g. schema checks). For creativity it implements a "Debate Swarmlet" paradigm--spawns sub-debates for contentious steps, scaling to ensemble validation in large pipelines.

### Workflow Graph (`graph.py`)
StateGraph with cycles for iterative refinement and consensus building.

### Tools with MCP
Wrap tools for interoperability:
```python
# tools/data_tools.py (excerpt addition)
class DataValidationResult(BaseModel):
    valid: bool = Field(description="Is data valid?")
    issues: List[str] = Field(description="List of validation issues")

@mcp.tool()
def validate_data(steps: List[dict], ctx: Context) -> DataValidationResult:
    """MCP tool: Validate pipeline steps (e.g., schema checks)."""
    # Simulated validation; in prod, use libraries like Great Expectations
    issues = []  # E.g., check for nulls, types
    if not steps:
        issues.append("No steps provided")
    return DataValidationResult(valid=len(issues) == 0, issues=issues)
```