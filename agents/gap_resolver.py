# agents/gap_resolver.py: Meta-swarmlet for resolving persistent gaps
import re
import asyncio
import structlog
from typing import List, Dict
from collections import Counter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import MODELS, PipelineStep, INDEX_DIR
import os

parser = PydanticOutputParser(pydantic_object=PipelineStep)

# Specialized templates for common gap patterns
# Enhanced gap templates with comprehensive solutions
GAP_TEMPLATES = {
    "load": """
import pandas as pd
from google.cloud import bigquery
import boto3

def load_to_scalable_storage(df, format='parquet'):
    # S3 implementation
    if format == 'parquet':
        df.to_parquet('s3://data-bucket/sales_data.parquet', index=False)
    # BigQuery implementation  
    client = bigquery.Client()
    table_id = "project.dataset.sales_data"
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    return f"Loaded {{len(df)}} rows to scalable storage"
""",
    "monitoring": """
import logging
from prometheus_client import Counter, Histogram
import structlog

# Setup structured logging
logger = structlog.get_logger()
pipeline_counter = Counter('pipeline_steps_total', 'Total pipeline steps')
processing_time = Histogram('pipeline_step_duration_seconds', 'Step processing time')

def setup_monitoring():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Pipeline monitoring initialized")
    
def track_step(step_name, duration, status):
    pipeline_counter.inc()
    processing_time.observe(duration)
    logger.info("step_completed", step=step_name, duration=duration, status=status)
""",
    "testing": """
import pytest
import pandas as pd

def test_data_quality(df):
    assert not df.empty, "DataFrame should not be empty"
    assert df.isnull().sum().sum() == 0, "No null values allowed"
    assert not df.duplicated().any(), "No duplicates allowed"
    
def test_pipeline_step(input_data, expected_columns):
    result = process_step(input_data)
    assert all(col in result.columns for col in expected_columns)
    return result

# Pytest configuration
@pytest.fixture
def sample_data():
    return pd.DataFrame({{'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']}})
""",
    "collaboration": """
import git
from dataclasses import dataclass
from typing import Protocol

class PipelineModule(Protocol):
    def process(self, data: pd.DataFrame) -> pd.DataFrame: ...
    def get_api_info(self) -> Dict: ...

@dataclass
class ModuleAPI:
    name: str
    input_schema: Dict
    output_schema: Dict
    endpoint: str

def setup_git_integration():
    repo = git.Repo.init('.')
    repo.config_writer().set_value("user", "name", "Pipeline Bot").release()
    return repo

def create_module_interface(module_name: str) -> ModuleAPI:
    return ModuleAPI(
        name=module_name,
        input_schema={{"type": "DataFrame", "required_columns": []}},
        output_schema={{"type": "DataFrame", "new_columns": []}},
        endpoint=f"/api/v1/modules/{{module_name}}"
    )
""",
    "partitioning": """
import pandas as pd
from pyspark.sql import SparkSession

def setup_spark_partitioning():
    spark = SparkSession.builder.appName("DataPipeline").getOrCreate()
    return spark

def partition_by_date(df, date_column='date', partitions=10):
    df['partition_key'] = pd.to_datetime(df[date_column]).dt.strftime('%Y-%m')
    spark_df = spark.createDataFrame(df)
    return spark_df.repartition(partitions, 'partition_key')

def partition_by_region(df, region_column='region'):
    spark_df = spark.createDataFrame(df)
    return spark_df.repartition(spark_df[region_column])
""",
    "validation": """
import great_expectations as ge
from typing import Dict, List

def create_data_quality_suite(df: pd.DataFrame) -> Dict:
    ge_df = ge.from_pandas(df)
    suite = {{
        "null_check": ge_df.expect_column_values_to_not_be_null,
        "unique_check": ge_df.expect_column_values_to_be_unique,
        "range_check": ge_df.expect_column_values_to_be_between,
        "type_check": ge_df.expect_column_values_to_be_of_type
    }}
    return suite

def validate_pipeline_output(df: pd.DataFrame, rules: List[str]) -> Dict:
    results = {{"passed": [], "failed": []}}
    for rule in rules:
        try:
            # Apply validation rule
            assert eval(f"df.{{rule}}"), f"Validation failed: {{rule}}"
            results["passed"].append(rule)
        except AssertionError as e:
            results["failed"].append(f"{{rule}}: {{str(e)}}")
    return results
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
4. Output file path where the step saves its results
5. Output format (csv, parquet, etc.)

Focus on practical solutions like missing data loads, validation logic, or transformation steps.
Ensure your code saves output to a file for the next pipeline step.

{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(resolver_template)
chain = prompt | MODELS["gap_resolver"] | parser  # Use dedicated gap resolver model

# Setup RAG for gap similarity detection  
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
gap_vectorstore = Chroma(
    persist_directory=str(INDEX_DIR / "gap_history"), 
    embedding_function=embeddings
)

def extract_top_gaps(rationales: List[str], top_n: int = 5) -> List[str]:
    """Extract top-N gaps using TF-IDF-like keyword frequency analysis"""
    gap_keywords = ["load", "monitoring", "testing", "collaboration", "partitioning", 
                   "validation", "documentation", "error handling", "retry", "api", 
                   "interface", "logging", "lineage", "scalability", "spark", "bigquery",
                   "storage", "warehouse", "s3", "cloud", "pytest", "unit test"]
    
    gap_counts = Counter()
    
    # Also analyze the gaps string directly
    all_text = " ".join(rationales) + " " + " ".join([r for r in rationales if r])
    
    for rationale in [all_text]:  # Process combined text
        rationale_lower = rationale.lower()
        for keyword in gap_keywords:
            # Count both exact matches and partial matches
            count = rationale_lower.count(keyword)
            if count > 0:
                gap_counts[keyword] += count
    
    # If no specific gaps found, return common ETL gaps
    if not gap_counts:
        return ["load", "monitoring", "testing"]  # Default essential gaps
    
    return [gap for gap, _ in gap_counts.most_common(top_n)]

async def multi_gap_resolver_swarmlet(gaps: str, context: str, history: List[str]) -> List[PipelineStep]:
    """Parallel processing of multiple gaps using divide-and-conquer sub-swarm"""
    
    logger = structlog.get_logger('pipeline')
    
    # Extract top gaps from rationales
    rationales = [entry for entry in history if "rationale" in entry.lower()]
    top_gaps = extract_top_gaps(rationales, top_n=3)
    
    logger.info("multi_gap_resolver_started", 
               target_gaps=top_gaps, 
               rationale_count=len(rationales),
               history_length=len(history))
    print(f"🎯 Multi-Gap Resolver targeting: {top_gaps}")
    
    # Create parallel tasks for each gap
    async def resolve_single_gap(gap_type: str) -> PipelineStep:
        template = GAP_TEMPLATES.get(gap_type, GAP_TEMPLATES["validation"])
        
        single_gap_template = f"""
        You are resolving the specific gap: {gap_type}
        
        Context: {context}
        Template suggestion: {template}
        
        Generate a PipelineStep that specifically addresses {gap_type} issues.
        Use the template as a starting point but adapt for the current context.
        
        {{format_instructions}}
        """
        
        prompt = ChatPromptTemplate.from_template(single_gap_template)
        chain = prompt | MODELS["gap_resolver"] | parser
        
        try:
            return await chain.ainvoke({
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            print(f"⚠️ Single gap resolver failed for {gap_type}: {e}")
            return PipelineStep(
                step_name=f"{gap_type.title()} Implementation",
                code_snippet=template,
                rationale=f"Template-based {gap_type} solution. Error: {str(e)[:50]}",
                output_file_path=f"output/{gap_type}_output.csv",
                output_format="csv"
            )
    
    # Execute parallel gap resolution
    tasks = [resolve_single_gap(gap) for gap in top_gaps]
    resolved_steps = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return valid steps
    valid_steps = [step for step in resolved_steps if isinstance(step, PipelineStep)]
    exceptions = [step for step in resolved_steps if not isinstance(step, PipelineStep)]
    
    logger.info("multi_gap_resolver_completed",
               total_gaps=len(top_gaps),
               successful_solutions=len(valid_steps),
               exceptions=len(exceptions),
               solution_names=[step.step_name for step in valid_steps])
    print(f"✅ Multi-Gap Resolver generated {len(valid_steps)} solutions")
    
    return valid_steps

async def resolve_persistent_gaps(gaps: str, context: str, history: List[str]) -> PipelineStep:
    """Enhanced gap resolution with multi-gap swarmlet and embedding similarity"""
    
    # Store current gaps in RAG for future similarity detection
    gap_vectorstore.add_texts([gaps], metadatas=[{"timestamp": str(asyncio.get_event_loop().time())}])
    
    # Check similarity with past gaps using embeddings
    similar_gaps = gap_vectorstore.similarity_search(gaps, k=3)
    similarity_context = "\n".join([doc.page_content for doc in similar_gaps])
    
    # Use multi-gap resolver for comprehensive solution
    try:
        multi_solutions = await multi_gap_resolver_swarmlet(gaps, context, history)
        
        if multi_solutions:
            # Combine multiple solutions into one comprehensive step
            combined_code = "\n\n# === COMPREHENSIVE GAP RESOLUTION ===\n"
            combined_rationale = "Multi-gap resolver addressed: "
            step_names = []
            
            for solution in multi_solutions:
                combined_code += f"\n# {solution.step_name}\n{solution.code_snippet}\n"
                step_names.append(solution.step_name)
            
            combined_rationale += ", ".join(step_names)
            
            return PipelineStep(
                step_name="Comprehensive Multi-Gap Resolution",
                code_snippet=combined_code,
                rationale=combined_rationale,
                output_file_path="output/comprehensive_pipeline_solution.py",
                output_format="python"
            )
        else:
            # Fallback to single gap resolution
            return await single_gap_fallback(gaps, context, history)
            
    except Exception as e:
        print(f"⚠️ Multi-gap resolver failed: {e}")
        return await single_gap_fallback(gaps, context, history)

async def single_gap_fallback(gaps: str, context: str, history: List[str]) -> PipelineStep:
    """Fallback single gap resolution method"""
    
    # Template matching for common patterns
    code_suggestions = []
    gaps_lower = gaps.lower()
    
    if "load" in gaps_lower or "storage" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["load"])
    if "monitoring" in gaps_lower or "logging" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["monitoring"])
    if "testing" in gaps_lower or "pytest" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["testing"])
    if "collaboration" in gaps_lower or "api" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["collaboration"])
    if "partitioning" in gaps_lower or "spark" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["partitioning"])
    if "validation" in gaps_lower or "quality" in gaps_lower:
        code_suggestions.append(GAP_TEMPLATES["validation"])
    
    # Enhance context with templates
    enhanced_context = context
    if code_suggestions:
        enhanced_context += f"\n\nSuggested code patterns:\n" + "\n".join(code_suggestions)
    
    try:
        return await chain.ainvoke({
            "gaps": gaps,
            "context": enhanced_context,
            "history": "; ".join(history[-3:]),  # Last 3 attempts
            "format_instructions": parser.get_format_instructions()
        })
    except Exception as e:
        print(f"⚠️ Gap resolver parsing error: {e}")
        # Return fallback with most comprehensive template
        return PipelineStep(
            step_name="Comprehensive Pipeline Enhancement",
            code_snippet=GAP_TEMPLATES["load"] + "\n\n" + GAP_TEMPLATES["monitoring"],
            rationale=f"Gap resolver failed with parsing error. Applied comprehensive load and monitoring solutions. Original error: {str(e)[:100]}",
            output_file_path="output/enhanced_pipeline.py",
            output_format="python"
        )