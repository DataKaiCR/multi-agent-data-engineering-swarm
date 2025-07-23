# agents/validator.py
import asyncio
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import MODELS, PipelineStep
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

parser = PydanticOutputParser(pydantic_object=PipelineStep)

validate_template = """
Evaluate pipeline steps: {pipeline_steps}.
Vote yes/no on validity, with rationale. Use validation rules: {validation_context}.
If debate needed, suggest refinements for scalability/quality.

IMPORTANT: Return ONLY valid JSON without any additional text or explanations.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(validate_template)

chain = prompt | MODELS["validator"] | parser


async def validate_steps(
    pipeline_steps: List[PipelineStep], validation_context: str
) -> PipelineStep:
    # MCP integration: Call validate_data tool for structured checks (scalable: Externalize validation logic)
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_result = await session.call_tool(
                "validate_data",
                {"steps": [step.model_dump() for step in pipeline_steps]},
            )
            structured_valid = (
                mcp_result.structuredContent
            )  # Pydantic: valid bool + issues list

    enriched_context = validation_context + "\nMCP Validation: " + str(structured_valid)

    # Multi-model debate: Async parallel invokes for scalability in large ensembles
    model_keys = ["validator", "cleaner", "transformer"]
    
    # Create separate chains for each model to ensure proper model switching
    async def get_vote_for_model(model_key: str):
        model_chain = prompt | MODELS[model_key] | parser
        try:
            return await model_chain.ainvoke(
                {
                    "pipeline_steps": [step.model_dump() for step in pipeline_steps],
                    "validation_context": enriched_context,
                    "format_instructions": parser.get_format_instructions(),
                }
            )
        except Exception as e:
            print(f"⚠️ Validation parsing error for {model_key}: {e}")
            # Return fallback vote to keep system running
            return PipelineStep(
                step_name=f"validation_error_{model_key}",
                code_snippet="",
                rationale=f"Validation failed for {model_key} - parsing error. Pipeline needs refinement."
            )
    
    votes = await asyncio.gather(
        *[get_vote_for_model(model_key) for model_key in model_keys]
    )

    structured_votes = [
        {
            "vote": "Yes" if "yes" in v.rationale.lower() else "No",
            "rationale": v.rationale,
        }
        for v in votes
    ]

    consensus = (
        len([v for v in structured_votes if v["vote"] == "Yes"])
        > len(structured_votes) / 2
    )
    rationale = (
        f"Consensus: {sum(1 for v in structured_votes if v['vote'] == 'Yes')}/{len(structured_votes)} yes votes. Details: "
        + " | ".join([v["rationale"] for v in structured_votes])
    )

    return PipelineStep(
        step_name="validation",
        code_snippet="" if consensus else "Refine pipeline",
        rationale=rationale,
    ), structured_votes
