# tools/data_tools.py
import os
from typing import Any, List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
import pandas as pd


mcp = FastMCP("DataEngTools", stateless_http=True)  # Stateless for scalability


class CsvLoadResult(BaseModel):
    """Structured output for CSV loading."""

    data_json: str = Field(description="JSON-serialized DataFrame")
    metadata: dict[str, Any] = Field(
        description="Data stats: rows, cols, size_mb, sharding_hint"
    )


@mcp.tool()
def load_csv(file_path: str, ctx: Context) -> CsvLoadResult:
    """MCP tool: Load and serialize CSV with sharding hints."""
    df = pd.read_csv(file_path)
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    metadata = {"rows": len(df), "columns": len(df.columns), "size_mb": file_size}
    if file_size > 10:
        metadata["sharding_hint"] = "Chunk into 10k rows for parallel ETL."
        # Remove async call for now - will work in sync context
    return CsvLoadResult(data_json=df.to_json(orient="records"), metadata=metadata)


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


def main():
    """Start the MCP server."""
    print("🚀 Starting MCP server on http://127.0.0.1:8000")
    print("Available tools: load_csv, validate_data")
    print("Press Ctrl+C to stop")
    mcp.run(transport="streamable-http")


# Run as standalone for testing
if __name__ == "__main__":
    main()
