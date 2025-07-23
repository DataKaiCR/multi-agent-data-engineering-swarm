# agents/transformer.py
import asyncio
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import MODELS, PipelineStep, DATA_DIR, INDEX_DIR
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Chroma for RAG: Retrieve transform rules (e.g., "encode categoricals with one-hot")
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = Chroma(
    persist_directory=str(INDEX_DIR / "transform_rules"), embedding_function=embeddings
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)  # Top 3 for focused reasoning

parser = PydanticOutputParser(pydantic_object=PipelineStep)

transform_template = """
Transform cleaned dataset from {dataset_path}. Clean metadata: {clean_metadata}.
Retrieved transform rules: {transform_rules}.

Generate transform step: Feature engineering (e.g., scaling, encoding, derivations). Suggest parallel if large.
Output code_snippet as executable Python (Pandas/Sklearn for small, Spark hints for large).
Rationale: Include feature insights and scalability notes.
"""

prompt = ChatPromptTemplate.from_template(transform_template)

chain = prompt | MODELS["transformer"] | parser


async def transform_data(dataset_path: str, clean_step: PipelineStep) -> PipelineStep:
    # RAG: Fetch transform rules (e.g., "derive profit = revenue - cost")
    query = f"Transform rules for {os.path.basename(dataset_path)}"
    retrieved_docs = retriever.invoke(query)
    transform_rules = "\n".join([doc.page_content for doc in retrieved_docs])

    # MCP tool call: Use transform_data for standardized features (scalable to ML frameworks)
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_result = await session.call_tool(
                "transform_data",
                {"file_path": dataset_path, "clean_metadata": clean_step.model_dump()},
            )
            structured_transform = mcp_result.structuredContent  # Pydantic-validated

    # Adaptive transform: Check size, hint parallelism (swarmlet prep for distributed features)
    file_size = structured_transform["metadata"]["size_mb"]
    rationale_add = structured_transform["metadata"].get(
        "sharding_hint", "Small dataset; single-pass transform."
    )

    # Async invoke for scalability (e.g., concurrent feature gen in high-volume ETL)
    result = await chain.ainvoke(
        {
            "dataset_path": dataset_path,
            "clean_metadata": str(structured_transform["metadata"]),
            "transform_rules": transform_rules + "\n" + rationale_add,
        }
    )
    return result


# Pre-build index (call in main.py; scalable: Batch embed rules)
def build_transform_index(docs: list[str]):
    vectorstore.add_texts(docs)  # Embed; extensible to Neo4j for relational features
