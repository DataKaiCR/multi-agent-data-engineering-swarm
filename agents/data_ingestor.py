# agents/data_ingestor.py
import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import Chroma
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
Ingest dataset at {dataset_path}.
Retrieved schemas/context: {retrieved_context}.

Generate ingestion step: Load, profile (shape, types, nulls), suggest sharding if large.
Output code_snippet as executable Python (Pandas for small, Spark for large).
Rationale: Include quality insights and scalability notes (e.g., parallel hints).
"""

prompt = ChatPromptTemplate.from_template(ingest_template)

chain = prompt | MODELS["ingestor"] | parser


async def ingest_data(dataset_path: str) -> PipelineStep:
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
    file_size = structured_load["metadata"]["size_mb"]
    rationale_add = structured_load["metadata"].get(
        "sharding_hint", "Small dataset; single-pass."
    )

    # Invoke chain with enriched context (async for scalability in high-throughput pipelines)
    result = await chain.ainvoke(
        {
            "dataset_path": dataset_path,
            "retrieved_context": retrieved_context
            + "\n"
            + rationale_add
            + "\nLoaded metadata: "
            + str(structured_load["metadata"]),
        }
    )
    return result


# Pre-build index (call in main.py; scalable: Batch embed at startup)
def build_rag_index(docs: list[str]):
    vectorstore.add_texts(
        docs
    )  # Embed; future: Hybrid with Neo4j for relational queries
    vectorstore.persist()
