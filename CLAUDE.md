# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **self-learning multi-agent data engineering swarm** that uses LangGraph to orchestrate AI agents for automated data pipeline creation. The system features **emergent self-optimization** through feedback loops, **multi-gap parallel resolution**, and **intra-round validation** for achieving consensus. It leverages multiple LLM providers (OpenAI, Anthropic, xAI/Grok) in specialized roles with **embedding-based similarity detection** for persistent gap resolution.

## Development Commands

### Running the Application
```bash
# Basic run
uv run python main.py

# Verbose run (recommended - shows detailed progress)
uv run python main.py -v
```

**Output Files:**
- `output.json`: Complete pipeline results with metadata
- `logs/pipeline_YYYYMMDD_HHMMSS.json`: Structured JSON logs for observability

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
- Uses StateGraph for multi-agent orchestration with self-learning feedback loops
- Implements **semantic similarity detection** for persistent gap identification (>0.3 threshold)
- **Intra-round validation** immediately tests resolver solutions within the same debate round
- State includes `feedback_history`, `gap_escalation_count`, and pipeline continuity tracking

**Enhanced Agent System (`agents/`)**
- `prompt_engineer.py`: OpenAI GPT-4o-mini for fast prompt refinement
- `data_ingestor.py`: OpenAI GPT-4o with RAG (Chroma vectorstore) for structured data analysis
- `cleaner.py`: Anthropic Claude-3.5-Sonnet for logical data cleaning reasoning
- `transformer.py`: xAI Grok-3 for creative feature engineering
- `validator.py`: **Multi-model consensus** using validator + cleaner + transformer models
- `gap_resolver.py`: **Meta-swarmlet resolver** with Anthropic Claude for persistent gap resolution

**Self-Learning Features:**
- **Multi-Gap Resolver Swarmlet**: Parallel processing of multiple gaps using `asyncio.gather()`
- **TF-IDF Gap Extraction**: Keyword frequency analysis to identify top-N gaps from rationales
- **Embedding-based Similarity**: RAG storage of past gaps using OpenAI embeddings + Chroma
- **Comprehensive Templates**: Production-ready solutions (BigQuery, Spark, pytest, monitoring)

**Configuration (`config.py`)**
- Multi-provider model initialization with fallback handling
- Uses `langchain.chat_models.init_chat_model` for unified model interfaces
- Environment-based configuration for API keys and model parameters

**Tools & MCP Integration (`tools/`)**
- `data_tools.py`: MCP-wrapped tools using Anthropic MCP client
- CSV loading with automatic sharding hints for large files
- Standardized tool interfaces for agent interoperability

**Data Management & Observability**
- `data/`: Sample datasets (sales_data.csv for testing)
- `indexes/`: Multi-domain Chroma vectorstores:
  - `schemas/`: Schema and context retrieval for agents
  - `gap_history/`: Persistent gap storage for similarity detection
  - `cleaning_rules/`, `transform_rules/`: Domain-specific knowledge bases
- `logs/`: **Structured JSON logging** for production observability
- `output.json`: Complete pipeline results with consensus status and metadata

### Key Patterns

**Multi-Model Strategy**: Different LLMs assigned to specialized roles based on their strengths:
- **OpenAI GPT-4o**: Data ingestion (structured analysis, fast processing)
- **Anthropic Claude**: Data cleaning + gap resolution (logical reasoning, creative problem-solving)  
- **xAI Grok**: Transformation + validation (creative feature engineering, analytical thinking)
- **Multi-model Consensus**: Validator uses 3 different models for robust decision-making

**Self-Learning Architecture**: 
- **Feedback Loop System**: Treats validation failures as "feedback dataset" for learning
- **Semantic Gap Detection**: Embedding-based similarity analysis (>0.3 threshold triggers escalation)
- **Meta-Swarmlet Escalation**: Parallel gap resolution when patterns persist across rounds
- **Intra-Round Validation**: Immediate testing prevents unnecessary additional debate rounds

**Scalability & Performance**: 
- **Async Parallel Processing**: `asyncio.gather()` for concurrent gap resolution
- **Token-Efficient Summaries**: Compact gap aggregation prevents prompt bloat
- **Pipeline State Management**: File path propagation ensures agent cohesion
- **Dynamic Scaling**: Automatic parallel agent spawning for large datasets

**Production Observability**: 
- **Structured JSON Logging**: ELK-compatible logs for monitoring dashboards
- **Performance Metrics**: Gap resolution rates, consensus tracking, escalation patterns
- **RAG-Enhanced Memory**: Persistent storage prevents token bloat in long-running swarms

## File Structure Context

- **Root files**: `main.py` (entry point), `graph.py` (workflow), `config.py` (models)
- **Agents**: Specialized LLM agents for different pipeline stages  
- **Tools**: MCP-standardized utilities for data operations
- **Tests**: Pytest-based testing with model invocation validation
- **Utils**: Helper scripts like `generate_sales_data.py`

## Advanced Features

### Self-Learning Feedback Loop
The system demonstrates **emergent self-optimization** where validation failures become learning opportunities:

1. **Gap Extraction**: TF-IDF analysis identifies persistent issues from validator rationales
2. **Similarity Detection**: Embeddings detect recurring patterns (>0.3 threshold)
3. **Meta-Swarmlet Escalation**: Parallel gap resolvers target multiple issues simultaneously
4. **Intra-Round Validation**: Immediate consensus testing within the same debate round

### Multi-Gap Resolver Templates
Production-ready code templates for common ETL gaps:
- **Load**: BigQuery, S3, Parquet storage solutions
- **Monitoring**: Prometheus metrics, structured logging, alerting
- **Testing**: Pytest configurations, data quality assertions
- **Collaboration**: Git integration, modular APIs, version control
- **Partitioning**: Spark-based distributed processing strategies

### Consensus Achievement
The system successfully achieves consensus through:
- **Multi-model validation**: 3 different LLMs vote on pipeline quality
- **Gap-aware resolution**: Targeted fixes for specific validation failures  
- **Pipeline continuity**: Agents build on each other's work rather than starting independently

## Development Notes

- **Model Initialization**: Graceful fallback handling for failed model connections
- **Dependency Management**: Uses `uv` for fast, reliable package management
- **Auto-indexing**: RAG vectorstores built automatically on first run
- **MCP Integration**: Tools server must be running (`./scripts/mcp-server.sh`)
- **Structured Logging**: JSON logs automatically timestamped in `logs/` directory
- **Output Generation**: Complete results saved to `output.json` with metadata