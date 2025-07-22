from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import MODELS, PipelineStep

parser = PydanticOutputParser(pydantic_object=PipelineStep)

refine_template = """
Refine this user prompt for a data engineering task: {user_prompt}.
Make it more structured, incorporate ETL best practices (e.g., data lineage, scalability hints), and optimize for multi-agent collaboration.
Add few-shot examples if helpful. Critique and iterate if needed for precision.

Output as a PipelineStep with step_name='refined_prompt', code_snippet=empty, rationale=refined prompt text.
"""

prompt = ChatPromptTemplate.from_template(refine_template)

chain = prompt | MODELS["prompt_engineer"] | parser


def refine_prompt(user_prompt: str) -> PipelineStep:
    # Internal iteration for meta-refinement (scalable creativity)
    initial = chain.invoke({"user_prompt": user_prompt})
    critique_prompt = f"Critique and improve: {initial.rationale}"
    refined = chain.invoke({"user_prompt": critique_prompt})
    return refined
