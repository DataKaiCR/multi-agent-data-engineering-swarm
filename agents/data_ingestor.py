# agents/data_ingestor.py
import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import MODELS, PipelineStep, DATA_DIR, INDEX_DIR
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # For MCP tool integration

# Setup Chroma RAG (persistent, scalable; hook for Neo4j graph extension)
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = Chroma(
    persist_directory=str(INDEX_DIR / "schemas"), embedding_function=embeddings
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}
)  # Top 5 relevant for efficiency

parser = PydanticOutputParser(pydantic_object=PipelineStep)

ingest_template = """
Ingest dataset at {dataset_path} (current format: {current_format}).
Retrieved schemas/context: {retrieved_context}.
{feedback_context}

Generate ingestion step: Load, profile (shape, types, nulls), suggest sharding if large.
Output code_snippet as executable Python (Pandas for small, Spark for large).
Rationale: Include quality insights and scalability notes (e.g., parallel hints).

IMPORTANT: Your code must save the loaded/profiled data to an output file. 
Include the output file path in output_file_path field and format in output_format field.
For small datasets, save as CSV. For large datasets, consider Parquet.

If feedback context is provided, adapt your ingestion approach to address the identified gaps.

CRITICAL: Return ONLY valid JSON without any additional text, explanations, markdown formatting, or code blocks. Do not wrap in ```json or any other formatting. Your response must be parseable JSON starting with {{ and ending with }}.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(ingest_template)

chain = prompt | MODELS["ingestor"] | parser


async def ingest_data(dataset_path: str, feedback_context: str = "", current_format: str = "csv") -> PipelineStep:
    # RAG retrieval: Embed query dynamically for schema-aware ingestion
    query = f"Schemas and ETL patterns for {os.path.basename(dataset_path)}"
    retrieved_docs = retriever.invoke(query)
    retrieved_context = "\n".join([doc.page_content for doc in retrieved_docs])

    # MCP tool call: Use standardized load_csv for interoperable data fetch
    async with streamablehttp_client("http://localhost:8000/mcp") as (
        read,
        write,
        _,
    ):  # Scale to cloud endpoint
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_result = await session.call_tool(
                "load_csv", {"file_path": dataset_path}
            )
            structured_load = mcp_result.structuredContent  # Pydantic: Ensures contract

    # Adaptive sharding: Creative swarmlet—check size, hint parallelism (extend to spawn sub-agents)
    if structured_load and isinstance(structured_load, dict) and "metadata" in structured_load and structured_load["metadata"]:
        file_size = structured_load["metadata"].get("size_mb", 0)
        rationale_add = structured_load["metadata"].get(
            "sharding_hint", "Small dataset; single-pass."
        )
        metadata_str = str(structured_load["metadata"])
    else:
        file_size = 0
        rationale_add = "Small dataset; single-pass."
        metadata_str = "No metadata available"

    # Invoke chain with enriched context (async for scalability in high-throughput pipelines)
    feedback_prompt = f"\nFeedback Context: {feedback_context}" if feedback_context else ""
    try:
        result = await chain.ainvoke(
            {
                "dataset_path": dataset_path,
                "current_format": current_format,
                "retrieved_context": retrieved_context
                + "\n"
                + rationale_add
                + "\nLoaded metadata: "
                + metadata_str,
                "feedback_context": feedback_prompt,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result
    except Exception as e:
        print(f"⚠️ Ingestor parsing error: {e}")
        # Return fallback ingestion step to keep system running
        return PipelineStep(
            step_name="data_ingestion_fallback",
            code_snippet="df = pd.read_csv('data/sales_data.csv'); df.to_csv('data/ingested_sales_data.csv', index=False); print(f'Shape: {df.shape}'); print(f'Nulls: {df.isnull().sum().sum()}')",
            rationale=f"Ingestor failed with parsing error. Applied basic CSV loading and profiling. Original error: {str(e)[:100]}",
            output_file_path="data/ingested_sales_data.csv",
            output_format="csv"
        )


# Pre-build index (call in main.py; scalable: Batch embed at startup)
def build_rag_index(docs: list[str]):
    vectorstore.add_texts(
        docs
    )  # Embed; auto-persisted with persist_directory
