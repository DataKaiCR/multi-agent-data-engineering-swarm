# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a multi-agent data engineering swarm system that uses LangGraph to orchestrate AI agents for automated data pipeline creation. The system leverages multiple LLM providers (OpenAI, Anthropic, xAI/Grok, Ollama) in specialized roles to collaboratively ingest, clean, transform, and validate datasets.

## Development Commands

### Running the Application
```bash
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py
pytest tests/test_data_tools.py

# Run with verbose output
pytest -v
```

### Environment Setup
Create a `.env` file with required API keys:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
XAI_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
MODEL_TEMPERATURE=0.2
```

## Architecture

### Core Components

**LangGraph Workflow (`graph.py`)**
- Uses StateGraph for multi-agent orchestration with cyclic workflows
- Implements debate/consensus mechanism for iterative refinement
- State is shared via AgentState TypedDict containing task, pipeline_steps, debate_rounds

**Agent System (`agents/`)**
- `prompt_engineer.py`: Uses Deepseek (Ollama) for prompt refinement
- `data_ingestor.py`: Uses OpenAI GPT-4o with RAG (Chroma vectorstore) for data ingestion
- Each agent returns PipelineStep objects with code_snippet, rationale, step_name

**Configuration (`config.py`)**
- Multi-provider model initialization with fallback handling
- Uses `langchain.chat_models.init_chat_model` for unified model interfaces
- Environment-based configuration for API keys and model parameters

**Tools & MCP Integration (`tools/`)**
- `data_tools.py`: MCP-wrapped tools using Anthropic MCP client
- CSV loading with automatic sharding hints for large files
- Standardized tool interfaces for agent interoperability

**Data Management**
- `data/`: Sample datasets (sales_data.csv for testing)
- `indexes/`: Chroma vectorstore for RAG-based schema retrieval
- Dynamic file size checking for parallel processing decisions

### Key Patterns

**Multi-Model Strategy**: Different LLMs assigned to specialized roles based on their strengths:
- Deepseek: Prompt engineering (creative reasoning)
- OpenAI: Data ingestion (structured analysis)  
- Claude: Data cleaning (logical reasoning)
- Grok: Transformation (creative feature engineering)

**Scalability Design**: 
- Async-capable LangGraph nodes for concurrent execution
- Dynamic sub-agent spawning for large datasets (>1MB threshold)
- Chunked processing with pandas for memory efficiency

**RAG Integration**: 
- OpenAI embeddings + Chroma for schema/context retrieval
- Persistent vectorstore in `indexes/schemas/` directory

**Consensus Mechanism**: 
- Multi-model voting in debate_node for quality assurance
- Maximum 5 iteration rounds with automatic convergence

## File Structure Context

- **Root files**: `main.py` (entry point), `graph.py` (workflow), `config.py` (models)
- **Agents**: Specialized LLM agents for different pipeline stages  
- **Tools**: MCP-standardized utilities for data operations
- **Tests**: Pytest-based testing with model invocation validation
- **Utils**: Helper scripts like `generate_sales_data.py`

## Development Notes

- Models may fail to initialize (handled gracefully with None fallbacks)
- Test suite includes actual LLM invocations to verify connectivity
- Project uses uv for dependency management (uv.lock present)
- RAG index must be built before first run (automated in main.py)
- Large file processing automatically triggers parallel agent spawning