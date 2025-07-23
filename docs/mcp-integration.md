# MCP (Model Context Protocol) Integration

## Overview
This project leverages MCP for **production-ready standardized tool interfaces** between AI agents in our self-learning multi-agent system. MCP enables seamless interoperability with Pydantic validation and supports the **meta-swarmlet escalation** and **consensus achievement** mechanisms.

## Current Production Usage
- **Data Loading & Validation**: CSV processing with automatic sharding hints
- **Schema Discovery**: RAG-enhanced context for agent decision making
- **Gap Resolution**: Production templates for BigQuery, Spark, monitoring solutions
- **Pipeline State Management**: File path propagation between agents for cohesion

## Production MCP Server Deployment

### Quick Start for Self-Learning System
```bash
# Start MCP server for multi-agent collaboration
make mcp-start          # Background server with logging

# Test all MCP tools used by agents
make mcp-probe          # Validates load_csv, validate_data integration

# Run main pipeline with MCP integration
make run                # Full self-learning pipeline execution

# Monitor MCP server logs
make dev-logs           # Real-time server monitoring
```

### Manual Development Testing
```bash
# Launch standalone MCP server (included in dependencies)
uv run python -m tools.data_tools

# Test MCP tools via HTTP endpoints
curl -X POST http://localhost:8000/mcp/tools/load_csv \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sales_data.csv"}'

# Validate multi-agent pipeline data
curl -X POST http://localhost:8000/mcp/tools/validate_data \
  -H "Content-Type: application/json" \
  -d '{"steps": []}'
```

### Production Integration Status ✅
- **Agent Communication**: All agents use MCP for standardized data operations
- **Pipeline Continuity**: File paths propagated through MCP metadata
- **Schema Discovery**: RAG context enhanced via MCP tool calls
- **Gap Resolution**: Production templates accessible via MCP interface

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

### Enhanced Data Validation for Self-Learning System
```python
@mcp.tool()
def validate_data(steps: List[dict], ctx: Context) -> DataValidationResult:
    """Production MCP tool: Advanced pipeline validation for consensus system"""
    issues = []
    
    if not steps:
        issues.append("No pipeline steps provided for validation")
        return DataValidationResult(valid=False, issues=issues)
    
    # Advanced validation for self-learning system
    for i, step in enumerate(steps):
        # Check pipeline continuity
        if not step.get("output_file_path") and i < len(steps) - 1:
            issues.append(f"Step {i+1} missing output_file_path for pipeline continuity")
        
        # Validate code quality for gap resolution
        if "code_snippet" in step and step["code_snippet"]:
            code = step["code_snippet"]
            if "import pandas" not in code and "df" in code:
                issues.append(f"Step {i+1} uses DataFrame without pandas import")
            
            # Check for production-ready patterns
            if "to_parquet" in code or "to_csv" in code:
                if "index=False" not in code:
                    issues.append(f"Step {i+1} missing index=False in file output")
    
    # Gap detection for meta-swarmlet escalation
    gap_keywords = ["load", "monitoring", "testing", "validation", "lineage"]
    covered_gaps = []
    for step in steps:
        rationale = step.get("rationale", "").lower()
        for gap in gap_keywords:
            if gap in rationale:
                covered_gaps.append(gap)
    
    missing_gaps = set(gap_keywords) - set(covered_gaps)
    if missing_gaps:
        issues.append(f"Pipeline missing coverage for: {', '.join(missing_gaps)}")
    
    return DataValidationResult(
        valid=len(issues) == 0, 
        issues=issues,
        gap_coverage=list(set(covered_gaps)),
        missing_gaps=list(missing_gaps)
    )

# Enhanced validation result for self-learning system
class DataValidationResult(BaseModel):
    valid: bool = Field(description="Is pipeline valid for production?")
    issues: List[str] = Field(description="List of validation issues")
    gap_coverage: List[str] = Field(description="Gaps covered by pipeline", default=[])
    missing_gaps: List[str] = Field(description="Gaps requiring meta-swarmlet resolution", default=[])
```

## Advanced Agent MCP Integration

### Self-Learning Data Ingestor with MCP
```python
async def ingest_data(dataset_path: str) -> PipelineStep:
    """Enhanced MCP integration for self-learning pipeline"""
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # MCP tool call with pipeline continuity
            mcp_result = await session.call_tool(
                "load_csv", {"file_path": dataset_path}
            )
            structured_load = mcp_result.structuredContent
            
            # Extract file path and format for agent cohesion
            if structured_load and "metadata" in structured_load:
                file_size = structured_load["metadata"].get("size_mb", 0)
                # Automatic sharding recommendation for large datasets
                if file_size > 1:  # MB threshold for parallel processing
                    sharding_hint = structured_load["metadata"].get("sharding_hint", "")
    
    # Generate pipeline step with MCP-enhanced context
    return PipelineStep(
        step_name="Enhanced Data Ingestion",
        code_snippet=generate_ingestion_code(structured_load),
        rationale=f"MCP-enhanced loading with metadata: {structured_load['metadata']}",
        output_file_path=f"processed_{Path(dataset_path).name}",
        output_format="parquet"  # Pipeline continuity format
    )
```

### Multi-Model Validator MCP Integration
```python
async def validate_steps_with_mcp(pipeline_steps: List[PipelineStep]) -> ValidationResult:
    """Multi-model validation enhanced with MCP structured checks"""
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # MCP validation for structured pipeline analysis
            mcp_result = await session.call_tool(
                "validate_data",
                {"steps": [step.model_dump() for step in pipeline_steps]}
            )
            structured_validation = mcp_result.structuredContent
            
            # Enhanced context for multi-model consensus
            enriched_context = f"MCP Validation: {structured_validation}"
            
            # Continue with 3-LLM voting using enriched context
            # ... multi-model consensus logic
```