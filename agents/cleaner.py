import asyncio
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import MODELS, PipelineStep, DATA_DIR, INDEX_DIR
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Chroma for RAG: Retrieve cleaning rules (e.g., domain-specific policies)
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = Chroma(
    persist_directory=str(INDEX_DIR / "cleaning_rules"), embedding_function=embeddings
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)  # Top 3 rules for efficiency

parser = PydanticOutputParser(pydantic_object=PipelineStep)

clean_template = """
Clean dataset from {dataset_path}. Ingested metadata: {ingest_metadata}.
Retrieved cleaning rules: {cleaning_rules}.

Generate cleaning step: Handle nulls, outliers, type errors. Suggest parallel cleaning if large.
Output code_snippet as executable Python (Pandas for small, Spark hints for large).
Rationale: Include quality fixes and scalability notes.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(clean_template)

chain = prompt | MODELS["cleaner"] | parser


async def clean_data(dataset_path: str, ingest_step: PipelineStep) -> PipelineStep:
    # RAG: Fetch cleaning rules (e.g., "impute nulls with median for numeric columns")
    query = f"Cleaning rules for {os.path.basename(dataset_path)}"
    retrieved_docs = retriever.invoke(query)
    cleaning_rules = "\n".join([doc.page_content for doc in retrieved_docs])

    # MCP tool call: Use clean_data tool for standardized cleaning (scalable to cloud)
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_result = await session.call_tool(
                "clean_data",
                {
                    "file_path": dataset_path,
                    "ingest_metadata": ingest_step.model_dump(),
                },
            )
            structured_clean = mcp_result.structuredContent  # Pydantic-validated

    # Adaptive cleaning: Check size, hint parallelism (swarmlet for large data)
    file_size = structured_clean["metadata"]["size_mb"]
    rationale_add = structured_clean["metadata"].get(
        "sharding_hint", "Small dataset; single-pass cleaning."
    )

    # Async invoke for scalability (e.g., parallel cleaning in distributed ETL)
    result = await chain.ainvoke(
        {
            "dataset_path": dataset_path,
            "ingest_metadata": str(structured_clean["metadata"]),
            "cleaning_rules": cleaning_rules + "\n" + rationale_add,
            "format_instructions": parser.get_format_instructions(),
        }
    )
    return result


# Pre-build index (call in main.py; scalable: Batch embed rules)
def build_cleaning_index(docs: list[str]):
    vectorstore.add_texts(docs)  # Embed rules; auto-persisted with persist_directory
