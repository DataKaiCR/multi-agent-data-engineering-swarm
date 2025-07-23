# agents/gap_resolver.py: Meta-swarmlet for resolving persistent gaps
import re
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from config import MODELS, PipelineStep

parser = PydanticOutputParser(pydantic_object=PipelineStep)

# Specialized templates for common gap patterns
GAP_TEMPLATES = {
    "bigquery": """
def load_to_bigquery(df, table_id, project_id):
    from google.cloud import bigquery
    client = bigquery.Client(project=project_id)
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    return f"Loaded {{len(df)}} rows to {{table_id}}"
""",
    "validation": """
def validate_data_quality(df):
    issues = []
    if df.isnull().sum().sum() > 0:
        issues.append("Contains null values")
    if df.duplicated().sum() > 0:
        issues.append("Contains duplicates")
    return {"valid": len(issues) == 0, "issues": issues}
""",
    "transformation": """
def apply_business_rules(df):
    # Apply domain-specific transformations
    df['processed_date'] = pd.Timestamp.now()
    df = df.dropna()  # Remove invalid records
    return df
"""
}

resolver_template = """
You are a specialized gap resolver agent. Analyze these persistent gaps and generate concrete code solutions:

Persistent Gaps: {gaps}
Context: {context}
Previous Attempts: {history}

Generate a specific PipelineStep that addresses these gaps with:
1. Concrete code snippet (not pseudocode)
2. Clear rationale explaining how it fixes the gaps
3. Step name that reflects the solution

Focus on practical solutions like missing data loads, validation logic, or transformation steps.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(resolver_template)
chain = prompt | MODELS["validator"] | parser  # Use validator model for analytical thinking

async def resolve_persistent_gaps(gaps: str, context: str, history: List[str]) -> PipelineStep:
    """Generate code solutions for persistent gaps using template matching and LLM reasoning"""
    
    # Template matching for common patterns
    code_suggestions = []
    gaps_lower = gaps.lower()
    
    if "bigquery" in gaps_lower or "load" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["bigquery"])
    if "validation" in gaps_lower or "quality" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["validation"])
    if "transform" in gaps_lower and "missing" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["transformation"])
    
    # Enhance context with templates
    enhanced_context = context
    if code_suggestions:
        enhanced_context += f"\n\nSuggested code patterns:\n" + "\n".join(code_suggestions)
    
    return await chain.ainvoke({
        "gaps": gaps,
        "context": enhanced_context,
        "history": "; ".join(history[-3:]),  # Last 3 attempts
        "format_instructions": parser.get_format_instructions()
    })