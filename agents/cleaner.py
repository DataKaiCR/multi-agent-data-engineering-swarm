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
Clean dataset from {dataset_path} (current format: {current_format}). 
Previous step output: {previous_output_info}
Ingested metadata: {ingest_metadata}.
Retrieved cleaning rules: {cleaning_rules}.
{feedback_context}

Generate cleaning step: Handle nulls, outliers, type errors. Suggest parallel cleaning if large.
Output code_snippet as executable Python (Pandas for small, Spark hints for large).
Rationale: Include quality fixes and scalability notes.

IMPORTANT: Read from the PREVIOUS step's output file, not the original dataset.
Your code must save the cleaned data to an output file.
Include the output file path in output_file_path field and format in output_format field.
If previous step used Spark/Parquet, continue with that format for consistency.

If feedback context is provided, adapt your cleaning approach to address the identified gaps.

CRITICAL: Return ONLY valid JSON without any additional text, explanations, markdown formatting, or code blocks. Do not wrap in ```json or any other formatting. Your response must be parseable JSON starting with {{ and ending with }}.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(clean_template)

chain = prompt | MODELS["cleaner"] | parser


async def clean_data(dataset_path: str, ingest_step: PipelineStep, feedback_context: str = "", current_format: str = "csv") -> PipelineStep:
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
    if structured_clean and isinstance(structured_clean, dict) and "metadata" in structured_clean and structured_clean["metadata"]:
        file_size = structured_clean["metadata"].get("size_mb", 0)
        rationale_add = structured_clean["metadata"].get(
            "sharding_hint", "Small dataset; single-pass cleaning."
        )
    else:
        file_size = 0
        rationale_add = "Small dataset; single-pass cleaning."

    # Get previous step output info for continuity
    previous_output_info = f"Previous output: {ingest_step.output_file_path} (format: {ingest_step.output_format})" if ingest_step.output_file_path else "No previous output file specified"
    
    # Async invoke for scalability (e.g., parallel cleaning in distributed ETL)
    feedback_prompt = f"\nFeedback Context: {feedback_context}" if feedback_context else ""
    try:
        result = await chain.ainvoke(
            {
                "dataset_path": dataset_path,
                "current_format": current_format,
                "previous_output_info": previous_output_info,
                "ingest_metadata": str(structured_clean.get("metadata", {})) if structured_clean else "No metadata available",
                "cleaning_rules": cleaning_rules + "\n" + rationale_add,
                "feedback_context": feedback_prompt,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result
    except Exception as e:
        print(f"⚠️ Cleaner parsing error: {e}")
        # Return fallback cleaning step to keep system running
        input_path = ingest_step.output_file_path if ingest_step.output_file_path else dataset_path
        return PipelineStep(
            step_name="data_cleaning_fallback",
            code_snippet=f"df = pd.read_csv('{input_path}'); df_cleaned = df.dropna(); df_cleaned.to_csv('data/cleaned_sales_data.csv', index=False)",
            rationale=f"Cleaner failed with parsing error. Applied basic cleaning - dropna(). Original error: {str(e)[:100]}",
            output_file_path="data/cleaned_sales_data.csv",
            output_format="csv"
        )


# Pre-build index (call in main.py; scalable: Batch embed rules)
def build_cleaning_index(docs: list[str]):
    vectorstore.add_texts(docs)  # Embed rules; auto-persisted with persist_directory
