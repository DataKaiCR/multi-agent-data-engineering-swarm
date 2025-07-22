# agents/data_ingestor.py
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings  # For embedding; swap as needed
from config import MODELS, PipelineStep, DATA_DIR, INDEX_DIR
from tools.data_tools import load_csv  # Assume defined; extend with MCP

# Setup Chroma RAG (persistent for scalability)
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = Chroma(
    persist_directory=str(INDEX_DIR / "schemas"), embedding_function=embeddings
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})  # Top 5 relevant schemas

parser = PydanticOutputParser(pydantic_object=PipelineStep)

ingest_template = """
Ingest this dataset: {dataset_path}.
Retrieved schemas/context: {retrieved_context}.

Generate an ingestion step: Load data, profile basics (shape, types, nulls), suggest sharding if large.
Output code_snippet as executable Python (e.g., Pandas for small, Spark hints for large).
Rationale: Include data quality insights and scalability notes.

For large data (>1MB), chunk and parallelize ingestion.
"""

prompt = ChatPromptTemplate.from_template(ingest_template)

chain = prompt | MODELS["ingestor"] | parser


def ingest_data(dataset_path: str) -> PipelineStep:
    # RAG retrieval: Embed query from path or metadata
    query = f"Schemas for {os.path.basename(dataset_path)} ingestion"
    retrieved_docs = retriever.invoke(query)
    retrieved_context = "\n".join([doc.page_content for doc in retrieved_docs])

    # Dynamic complexity check for self-adaptive swarm
    file_size = os.path.getsize(dataset_path) / (1024 * 1024)  # MB
    if file_size > 1:  # Threshold for POC; scale to GB in prod
        # Simulate sub-swarm: Chunk file (creative: parallel via multiprocessing)
        import pandas as pd

        chunks = pd.read_csv(dataset_path, chunksize=10000)  # Example chunking
        # In full swarm: Spawn sub-agents per chunk
        rationale_add = "Data sharded for scalability; process in parallel."
    else:
        rationale_add = "Small dataset; single-pass ingestion."

    # Invoke chain
    result = chain.invoke(
        {
            "dataset_path": dataset_path,
            "retrieved_context": retrieved_context + "\n" + rationale_add,
        }
    )
    return result


# Pre-build index if needed (call once in main.py)
def build_rag_index(docs: list[str]):
    vectorstore.add_texts(docs)  # Embed sample schemas/docs
    vectorstore.persist()
