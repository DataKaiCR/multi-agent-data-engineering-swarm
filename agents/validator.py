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
    votes = await asyncio.gather(
        *[
            chain.ainvoke(
                {
                    "pipeline_steps": [step.model_dump() for step in pipeline_steps],
                    "validation_context": enriched_context,
                }
            )
            for model_key in [
                "validator",
                "cleaner",
                "transformer",
            ]  # Expand models at scale
        ]
    )

    # Consensus: Majority vote; creative: Weight by rationale length/confidence (future RL optimization)
    yes_votes = len([v for v in votes if "yes" in v.rationale.lower()])
    consensus = yes_votes > len(votes) / 2
    rationale = (
        f"Consensus: {yes_votes}/{len(votes)} yes votes. Details: "
        + " | ".join([v.rationale for v in votes])
    )

    if not consensus:
        rationale += "\nDebate Swarmlet: Escalate to sub-debate for refinements."  # Hook for dynamic spawning

    return PipelineStep(
        step_name="validation",
        code_snippet="" if consensus else "Refine pipeline",
        rationale=rationale,
    )
