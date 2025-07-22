# MCP (Model Context Protocol) Integration

## Overview
This project uses MCP for standardized tool interfaces between AI agents, enabling interoperable data operations with Pydantic validation.

## Testing MCP Server

To launch a test MCP server for development:

1. Ensure MCP SDK installed (included in dependencies).
2. Run standalone MCP server:
   ```bash
   uv run python -m tools.data_tools
   ```
3. Access via client (in separate terminal):
   ```bash
   # Use MCP Inspector
   uv run mcp dev
   
   # Or test with curl for HTTP endpoints
   curl -X POST http://localhost:8000/mcp/tools/load_csv \
     -H "Content-Type: application/json" \
     -d '{"file_path": "data/sales_data.csv"}'
   ```
4. Test tools: Call `load_csv` or `validate_data` via client session
5. Debug: Check logs for progress reports; scale by mounting in Starlette for multi-tool testing.

## MCP Tool Examples

### Data Loading Tool
```python
@mcp_client.tool(
    name="load_csv",
    description="Load and serialize a CSV file for data ingestion",
    input_schema={
        "type": "object", 
        "properties": {"file_path": {"type": "string"}},
        "required": ["file_path"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "data_json": {"type": "string"}, 
            "metadata": {"type": "object"}
        },
    },
)
def load_csv(file_path: str) -> dict:
    df = pd.read_csv(file_path)
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    metadata = {"rows": len(df), "columns": len(df.columns), "size_mb": file_size}
    if file_size > 10:  # Scalability threshold
        metadata["sharding_hint"] = (
            "Recommended: Chunk into 10k row segments for parallel processing."
        )
    return {"data_json": df.to_json(orient="records"), "metadata": metadata}
```

### Data Validation Tool
```python
@mcp.tool()
def validate_data(steps: List[dict], ctx: Context) -> DataValidationResult:
    """MCP tool: Validate pipeline steps (e.g., schema checks)."""
    issues = []
    if not steps:
        issues.append("No steps provided")
    # Add more validation logic here
    return DataValidationResult(valid=len(issues) == 0, issues=issues)
```

## Agent Integration

Agents use MCP tools through async client sessions:

```python
async def ingest_data(dataset_path: str) -> PipelineStep:
    # MCP tool call for standardized data loading
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_result = await session.call_tool(
                "load_csv", {"file_path": dataset_path}
            )
            structured_load = mcp_result.structuredContent
    
    # Use loaded data in pipeline generation
    # ... rest of agent logic
```