# Multi-Agent Data Engineering Swarm

> AI agents that collaborate to automatically build data engineering pipelines

A proof-of-concept system where specialized LLM agents work together using swarm intelligence to ingest, clean, transform, and validate datasets. Each agent has a specific role (prompt engineering, data ingestion, cleaning, transformation, validation) and they debate through consensus mechanisms to create high-quality ETL pipelines.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys for OpenAI, Anthropic, and/or xAI

### Installation
```bash
# Clone repository
git clone <repository-url>
cd multi-agent-data-engineering-swarm

# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv if needed
uv sync

# Setup environment
cp .env.example .env  # Create from template
# Edit .env with your API keys
```

### Environment Setup
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  
XAI_API_KEY=your_xai_key
OLLAMA_BASE_URL=http://localhost:11434  # Optional for local models
MODEL_TEMPERATURE=0.2
```

### Quick Commands

**Using Make (Recommended):**
```bash
# Start MCP server in background
make mcp-start

# Run main pipeline
make run

# Test MCP tools
make mcp-probe

# Run tests
make test

# Check server status
make mcp-status

# Stop server
make mcp-stop

# See all available commands
make help
```

**Using Shell Script:**
```bash
# Start MCP server
./scripts/mcp-server.sh start

# Test with probe
./scripts/mcp-server.sh probe

# Check logs
./scripts/mcp-server.sh logs
```

**Manual Commands:**
```bash
# Basic usage - generate a data pipeline
uv run python main.py

# Start MCP server manually (foreground)
uv run python tools/data_tools.py
```

### Development Workflow

**Quick Start Development:**
```bash
make setup           # First time setup
make mcp-start       # Start MCP server in background  
make run             # Test main pipeline
make mcp-probe       # Test all MCP tools
make test-simple     # Run basic tests
```

**Daily Development:**
```bash
make dev             # Start development mode (MCP + tips)
make test-unit       # Run fast unit tests
make mcp-probe       # Test functionality
make dev-logs        # Watch server logs
make clean           # Cleanup when done
```

**Testing Workflow:**
```bash
make test-unit       # Fast unit tests during development
make test-integration # Full integration tests
make test            # All tests before committing
```

## ✨ Features

- **Multi-Agent Collaboration**: Specialized AI agents work together using swarm intelligence
- **Adaptive Multi-LLM Architecture**: Dynamically selects optimal models (OpenAI, Anthropic, xAI, Ollama) based on task-specific performance
- **Smart Pipeline Generation**: Automatically creates cleaning, transformation, and validation steps
- **Consensus Mechanism**: Agents debate and vote on pipeline quality through iterative refinement
- **RAG Integration**: Uses Chroma vectorstore for schema and context retrieval
- **MCP Integration**: Standardized tool interfaces for agent interoperability
- **Dynamic Scaling**: Automatically spawns sub-agents for large datasets

## 🏗️ How It Works

1. **Task Input**: Provide a data engineering task (e.g., "clean sales data")
2. **Agent Collaboration**: 
   - **Prompt Engineer**: Optimized for task refinement and structured thinking
   - **Data Ingestor**: Excels at data profiling and schema understanding with RAG context
   - **Cleaner**: Strong at data quality assessment and cleaning logic
   - **Transformer**: Specialized in feature engineering and mathematical transformations
   - **Validator**: Multi-model consensus mechanism for quality assurance
3. **Pipeline Output**: Structured pipeline with executable Python code

> **Model Selection**: Each agent role uses the most suitable LLM based on performance benchmarks for that specific task type. Models are regularly evaluated and upgraded as new capabilities become available.

## 🧪 Testing

**Using Make (Recommended):**
```bash
# Run all tests
make test

# Run unit tests only (fast)
make test-unit

# Run basic functionality tests
make test-simple

# Run integration tests (starts MCP server automatically)
make test-integration
```

**Manual Commands:**
```bash
# Run all tests
uv run python -m pytest

# Test model connectivity (requires API keys)
uv run python -m pytest tests/test_config.py::test_model_invocation -s

# Run specific test files
uv run python -m pytest tests/test_transformer.py -v

# Run with coverage
uv run python -m pytest --cov=.
```

## 🛠️ Project Structure

```
├── agents/           # Specialized AI agents
├── tools/           # MCP-wrapped data tools
├── docs/           # Detailed documentation
├── tests/          # Test suite  
├── data/           # Sample datasets
├── graph.py        # LangGraph workflow orchestration
├── config.py       # Model configuration
└── main.py         # Entry point
```

## 📚 Documentation

- **[Architecture Overview](docs/architecture.md)** - Detailed system design and components
- **[MCP Integration](docs/mcp-integration.md)** - Model Context Protocol usage and tools
- **[Experimentation Guide](docs/experimentation.md)** - Research goals and novel concepts

## 🔧 Optional: Local Models

For local model support with Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull required models  
ollama pull deepseek-r1:1.5b
ollama pull llama3.2:3b
```

## 🤝 Contributing

This is an experimental proof-of-concept exploring:
- Multi-agent consensus mechanisms in data pipelines
- Dynamic tool discovery via MCP
- Novel swarm intelligence paradigms for data engineering

Feel free to experiment with new agent types, LLM providers, or consensus mechanisms!

---

*Built with LangChain, LangGraph, MCP, and modern AI orchestration tools*