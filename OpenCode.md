# OpenCode.md

## Development Commands

### Build and Run
- Start MCP server: `make mcp-start`
- Run the pipeline: `make run`
- Check server status: `make mcp-status`
- Stop server: `make mcp-stop`

### Testing
- Run all tests: `pytest`
- Run specific test file: `pytest tests/test_config.py`
- Run specific test with verbose: `pytest tests/test_transformer.py -v`
- Run tests with coverage: `pytest --cov=.`

### Environment Setup
- Create `.env` file with required API keys:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
XAI_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
MODEL_TEMPERATURE=0.2
```

## Code Style Guidelines

### Formatting
- Strict adherence to Python 3.12+ syntax.
- Use PEP8 for formatting; ensure line length ≤ 120 characters.

### Imports
- Group locally defined modules, third-party libraries, and Python standard libraries in separate blocks.
- Local imports should use relative paths when within the same module.

### Naming Conventions
- Functions and variables: `snake_case`
- Class names: `CamelCase`
- Constants: `UPPER_SNAKE_CASE`

### Types
- Use type hints for all function signatures (e.g., `def func(x: int) -> str:`).
- Prefer `TypedDict` for structured types.

### Error Handling
- Handle exceptions gracefully with specific error classes (avoid broad `Exception`).
- Log errors using MCP tools instead of printing.

### Best Practices
- Follow existing patterns for multi-agent workflows.
- Use async for concurrent tasks in LangGraph and pandas for chunked processing.
- Ensure debate/consensus mechanism consistency with max iteration thresholds.