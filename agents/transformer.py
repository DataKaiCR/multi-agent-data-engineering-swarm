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
Transform cleaned dataset from {dataset_path} (current format: {current_format}).
Previous step output: {previous_output_info}
Clean metadata: {clean_metadata}.
Retrieved transform rules: {transform_rules}.
{feedback_context}

Generate transform step: Feature engineering (e.g., scaling, encoding, derivations). Suggest parallel if large.
Output code_snippet as executable Python (Pandas/Sklearn for small, Spark hints for large).
Rationale: Include feature insights and scalability notes.

IMPORTANT: Read from the PREVIOUS step's output file (cleaned data), not the original dataset.
Your code must save the transformed data to an output file.
Include the output file path in output_file_path field and format in output_format field.
Maintain format consistency with previous steps where possible.

If feedback context is provided, adapt your transformation approach to address the identified gaps.

CRITICAL: Return ONLY valid JSON without any additional text, explanations, markdown formatting, or code blocks. Do not wrap in ```json or any other formatting. Your response must be parseable JSON starting with {{ and ending with }}.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(transform_template)

chain = prompt | MODELS["transformer"] | parser


async def transform_data(dataset_path: str, clean_step: PipelineStep, feedback_context: str = "", current_format: str = "csv") -> PipelineStep:
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
    if structured_transform and isinstance(structured_transform, dict) and "metadata" in structured_transform and structured_transform["metadata"]:
        file_size = structured_transform["metadata"].get("size_mb", 0)
        rationale_add = structured_transform["metadata"].get(
            "sharding_hint", "Small dataset; single-pass transform."
        )
    else:
        file_size = 0
        rationale_add = "Small dataset; single-pass transform."

    # Get previous step output info for continuity
    previous_output_info = f"Previous output: {clean_step.output_file_path} (format: {clean_step.output_format})" if clean_step.output_file_path else "No previous output file specified"
    
    # Async invoke for scalability (e.g., concurrent feature gen in high-volume ETL)
    feedback_prompt = f"\nFeedback Context: {feedback_context}" if feedback_context else ""
    try:
        result = await chain.ainvoke(
            {
                "dataset_path": dataset_path,
                "current_format": current_format,
                "previous_output_info": previous_output_info,
                "clean_metadata": str(structured_transform.get("metadata", {})) if structured_transform else "No metadata available",
                "transform_rules": transform_rules + "\n" + rationale_add,
                "feedback_context": feedback_prompt,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result
    except Exception as e:
        print(f"⚠️ Transformer parsing error: {e}")
        # Return fallback transformation step to keep system running
        input_path = clean_step.output_file_path if clean_step.output_file_path else dataset_path
        return PipelineStep(
            step_name="feature_engineering_fallback",
            code_snippet=f"df = pd.read_csv('{input_path}'); df['profit_ratio'] = df['profit'] / df['revenue']; df.to_csv('data/transformed_sales_data.csv', index=False)",
            rationale=f"Transformer failed with parsing error. Applied basic profit ratio derivation. Original error: {str(e)[:100]}",
            output_file_path="data/transformed_sales_data.csv",
            output_format="csv"
        )


# Pre-build index (call in main.py; scalable: Batch embed rules)
def build_transform_index(docs: list[str]):
    vectorstore.add_texts(docs)  # Embed; extensible to Neo4j for relational features
