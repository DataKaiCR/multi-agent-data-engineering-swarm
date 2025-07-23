# main.py
import asyncio
from graph import app
from agents.data_ingestor import build_rag_index
from agents.cleaner import build_cleaning_index
from agents.transformer import build_transform_index


# Pre-build all RAG indexes (scalable: Run in parallel via asyncio.gather)
def setup_indexes():
    build_rag_index(["Sales schema: id:int, date:datetime, amount:float"])
    build_cleaning_index(["Impute nulls with median", "Remove outliers >3SD"])
    build_transform_index(
        ["Scale numerics", "Encode categoricals", "Derive profit ratio"]
    )


async def main():
    setup_indexes()
    initial_state = {
        "task": "Build ETL pipeline for sales_data.csv",
        "refined_prompt": "",
        "pipeline_steps": [],
        "debate_rounds": 0,
        "consensus_reached": False,
        "discovered_tools": {},
    }
    result = await app.ainvoke(initial_state)
    print("Final Pipeline Steps:")
    for step in result["pipeline_steps"]:
        print(f"- {step.step_name}: {step.rationale}\nCode: {step.code_snippet}\n")


if __name__ == "__main__":
    asyncio.run(main())
