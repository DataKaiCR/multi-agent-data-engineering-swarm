# tools/data_tools.py
import os
import asyncio
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


class CleanDataResult(BaseModel):
    """Structured output for data cleaning."""

    cleaned_json: str = Field(description="JSON-serialized cleaned DataFrame")
    metadata: dict = Field(
        description="Cleaning stats: nulls_fixed, outliers_removed, size_mb"
    )


@mcp.tool()
def clean_data(file_path: str, ingest_metadata: dict, ctx: Context) -> CleanDataResult:
    """MCP tool: Clean CSV (nulls, outliers)."""
    df = pd.read_csv(file_path)
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    metadata = {"size_mb": file_size, "nulls_fixed": 0, "outliers_removed": 0}

    # Basic cleaning (extend with Great Expectations for prod)
    metadata["nulls_fixed"] = int(df.isna().sum().sum())  # Convert numpy int to Python int
    df = df.fillna(df.median(numeric_only=True))  # Simple imputation
    # Outlier detection (example): Remove >3 std dev
    numeric_cols = df.select_dtypes(include="number").columns
    outliers = (
        (
            (df[numeric_cols] - df[numeric_cols].mean()).abs()
            > 3 * df[numeric_cols].std()
        )
        .sum()
        .sum()
    )
    metadata["outliers_removed"] = int(outliers)  # Convert numpy int to Python int
    df = df[
        ~(
            (df[numeric_cols] - df[numeric_cols].mean()).abs()
            > 3 * df[numeric_cols].std()
        ).any(axis=1)
    ]

    if file_size > 10:
        metadata["sharding_hint"] = "Chunk into 10k rows for parallel cleaning."
        # Remove async call for now - will work in sync context

    return CleanDataResult(cleaned_json=df.to_json(orient="records"), metadata=metadata)


from sklearn.preprocessing import StandardScaler, OneHotEncoder  # For transforms


class TransformDataResult(BaseModel):
    """Structured output for data transformation."""

    transformed_json: str = Field(description="JSON-serialized transformed DataFrame")
    metadata: dict = Field(
        description="Transform stats: new_features, scaled_cols, size_mb"
    )


@mcp.tool()
def transform_data(
    file_path: str, clean_metadata: dict, ctx: Context
) -> TransformDataResult:
    """MCP tool: Transform data (scaling, encoding, derivations)."""
    df = pd.read_json(
        clean_metadata.get("cleaned_json", "[]"), orient="records"
    )  # From clean step
    file_size = clean_metadata.get("size_mb", 0)
    metadata = {"size_mb": file_size, "new_features": 0, "scaled_cols": 0}

    # Basic transforms (extend with Featuretools for auto-eng in prod)
    # Scaling numerics
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        metadata["scaled_cols"] = len(numeric_cols)

    # Encoding categoricals
    cat_cols = df.select_dtypes(include="object").columns
    if len(cat_cols) > 0:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        encoded = pd.DataFrame(
            encoder.fit_transform(df[cat_cols]), columns=encoder.get_feature_names_out()
        )
        df = pd.concat([df.drop(cat_cols, axis=1), encoded], axis=1)
        metadata["new_features"] += encoded.shape[1] - len(cat_cols)

    # Derivations (example: Add a simple ratio if applicable)
    if "revenue" in df.columns and "cost" in df.columns:
        df["profit"] = df["revenue"] - df["cost"]
        metadata["new_features"] += 1

    if file_size > 10:
        metadata["sharding_hint"] = "Parallel transform per feature group."
        # Remove async call for now - will work in sync context

    return TransformDataResult(
        transformed_json=df.to_json(orient="records"), metadata=metadata
    )


def main():
    """Start the MCP server."""
    print("🚀 Starting MCP server on http://127.0.0.1:8000")
    print("Available tools: load_csv, validate_data, clean_data, transform_data")
    print("Press Ctrl+C to stop")
    mcp.run(transport="streamable-http")


# Run as standalone for testing
if __name__ == "__main__":
    main()
