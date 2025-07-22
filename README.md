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

### Run
```bash
# Basic usage - generate a data pipeline
uv run python main.py

# Start MCP server for tool testing
uv run python tools/data_tools.py

# With custom task
uv run python -c "
from graph import app
result = app.invoke({
    'task': 'clean and analyze my sales data',
    'refined_prompt': '',
    'pipeline_steps': [],
    'debate_rounds': 0,
    'consensus_reached': False
})
print('Generated steps:')
for step in result['pipeline_steps']:
    print(f'- {step.step_name}: {step.code_snippet}')
"
```

## ✨ Features

- **Multi-Agent Collaboration**: Specialized AI agents work together using swarm intelligence
- **Multi-LLM Support**: OpenAI GPT-4, Anthropic Claude, xAI Grok, and local Ollama models
- **Smart Pipeline Generation**: Automatically creates cleaning, transformation, and validation steps
- **Consensus Mechanism**: Agents debate and vote on pipeline quality through iterative refinement
- **RAG Integration**: Uses Chroma vectorstore for schema and context retrieval
- **MCP Integration**: Standardized tool interfaces for agent interoperability
- **Dynamic Scaling**: Automatically spawns sub-agents for large datasets

## 🏗️ How It Works

1. **Task Input**: Provide a data engineering task (e.g., "clean sales data")
2. **Agent Collaboration**: 
   - Prompt Engineer (Deepseek) refines the task
   - Data Ingestor (OpenAI) loads data with RAG context
   - Cleaner (Claude) handles data quality issues  
   - Transformer (Grok) performs feature engineering
   - Validator ensures consensus through multi-model voting
3. **Pipeline Output**: Structured pipeline with executable Python code

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Test model connectivity (requires API keys)
uv run pytest tests/test_config.py::test_model_invocation -s

# Run with coverage
uv run pytest --cov=.
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