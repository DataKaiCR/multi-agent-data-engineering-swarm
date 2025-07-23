# main.py
import asyncio
import argparse
import json
import logging
import structlog
from datetime import datetime
from pathlib import Path
from graph import app
from agents.data_ingestor import build_rag_index
from agents.cleaner import build_cleaning_index
from agents.transformer import build_transform_index


# Setup structured logging for observability
def setup_structured_logging():
    """Configure structured JSON logging for pipeline observability"""
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    log_file = logs_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Clear any existing handlers to prevent conflicts
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Setup dedicated file handler for our structured logs
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Create a specific logger for our pipeline events
    pipeline_logger = logging.getLogger('pipeline')
    pipeline_logger.setLevel(logging.INFO)
    pipeline_logger.addHandler(file_handler)
    pipeline_logger.propagate = False  # Don't propagate to root logger
    
    # Configure structlog to use our pipeline logger
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=lambda name=None: pipeline_logger,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
    
    # Get structlog logger instance
    logger = structlog.get_logger('pipeline')
    logger.info("structured_logging_initialized", log_file=str(log_file))
    print(f"📋 Structured logs: {log_file}")
    
    return logger

# Pre-build all RAG indexes (scalable: Run in parallel via asyncio.gather)
def setup_indexes():
    logger = structlog.get_logger()
    logger.info("building_rag_indexes", status="started")
    
    build_rag_index(["Sales schema: id:int, date:datetime, amount:float"])
    build_cleaning_index(["Impute nulls with median", "Remove outliers >3SD"])
    build_transform_index(
        ["Scale numerics", "Encode categoricals", "Derive profit ratio"]
    )
    
    logger.info("building_rag_indexes", status="completed")


def setup_initial_state():
    return {
        "task": "Build ETL pipeline for sales_data.csv",
        "refined_prompt": "",
        "pipeline_steps": [],
        "debate_rounds": 0,
        "consensus_reached": False,
        "discovered_tools": {},
        "feedback_summary": "",
        "feedback_history": [],
        "gap_escalation_count": 0,
        "current_data_path": "data/sales_data.csv",
        "data_format": "csv",
        "pipeline_metadata": {},
    }


async def main(verbose=False):
    # Initialize structured logging
    logger = setup_structured_logging()
    logger.info("pipeline_started", verbose=verbose)
    
    print("🚀 Starting Multi-Agent Data Engineering Swarm...")
    print("📚 Setting up RAG indexes...")
    setup_indexes()
    
    print("🎯 Initializing pipeline state...")
    initial_state = setup_initial_state()
    logger.info("pipeline_state_initialized", 
               task=initial_state["task"][:100],
               gap_escalation_count=initial_state["gap_escalation_count"])
    
    print("🤖 Agents starting collaboration...\n")
    
    final_result = None
    
    # Stream the workflow to see progress in real-time  
    # Set recursion limit in config to handle debate loops
    config = {"recursion_limit": 35}
    async for chunk in app.astream(initial_state, config=config):
        # Each chunk represents completion of a node
        for node_name, node_output in chunk.items():
            if node_name == "discovery":
                tools = node_output.get('discovered_tools', {})
                print(f"🔍 Discovery Agent: Found {len(tools)} MCP tools")
                if verbose and tools:
                    print(f"   Tools: {list(tools.keys())}")
                
            elif node_name == "prompt":
                logger.info("prompt_engineer_completed", 
                           task_length=len(node_output.get('refined_prompt', '')))
                print(f"✏️  Prompt Engineer: Task refined and structured")
                if verbose:
                    refined_prompt = node_output.get('refined_prompt', '')
                    print(f"   Refined Task: {refined_prompt[:200]}{'...' if len(refined_prompt) > 200 else ''}")
                
            elif node_name == "ingest":
                steps = node_output.get('pipeline_steps', [])
                if steps:
                    latest_step = steps[-1]
                    logger.info("data_ingestor_completed", 
                               step_name=latest_step.step_name,
                               output_file=latest_step.output_file_path or "none",
                               output_format=latest_step.output_format)
                print(f"📥 Data Ingestor: Data loaded and profiled")
                if verbose:
                    if steps:
                        latest_step = steps[-1]
                        print(f"   Step: {latest_step.step_name}")
                        print(f"   Details: {latest_step.rationale[:150]}{'...' if len(latest_step.rationale) > 150 else ''}")
                
            elif node_name == "clean":
                steps = node_output.get('pipeline_steps', [])
                if steps:
                    latest_step = steps[-1]
                    logger.info("data_cleaner_completed", 
                               step_name=latest_step.step_name,
                               output_file=latest_step.output_file_path or "none",
                               output_format=latest_step.output_format)
                print(f"🧹 Data Cleaner: Applied cleaning transformations")
                if verbose:
                    if steps:
                        latest_step = steps[-1]
                        print(f"   Step: {latest_step.step_name}")
                        print(f"   Details: {latest_step.rationale[:150]}{'...' if len(latest_step.rationale) > 150 else ''}")
                
            elif node_name == "transform":
                steps = node_output.get('pipeline_steps', [])
                if steps:
                    latest_step = steps[-1]
                    logger.info("data_transformer_completed", 
                               step_name=latest_step.step_name,
                               output_file=latest_step.output_file_path or "none",
                               output_format=latest_step.output_format)
                print(f"⚡ Data Transformer: Feature engineering completed")
                if verbose:
                    if steps:
                        latest_step = steps[-1]
                        print(f"   Step: {latest_step.step_name}")
                        print(f"   Details: {latest_step.rationale[:150]}{'...' if len(latest_step.rationale) > 150 else ''}")
                
            elif node_name == "debate":
                rounds = node_output.get('debate_rounds', 0)
                consensus = node_output.get('consensus_reached', False)
                print(f"🗳️  Validator: Round {rounds} - {'✅ Consensus reached!' if consensus else '🔄 Continuing debate...'}")
                
                # Show vote details for debugging
                steps = node_output.get('pipeline_steps', [])
                if steps:
                    latest_step = steps[-1]
                    if latest_step.step_name == "validation":
                        # Extract vote count from rationale
                        rationale = latest_step.rationale
                        if "yes votes" in rationale:
                            vote_part = rationale.split("Details:")[0]
                            print(f"   {vote_part}")
                        
                        if verbose:
                            print(f"   Full Details: {rationale[:300]}{'...' if len(rationale) > 300 else ''}")
        
        # Store the final result
        final_result = chunk
    
    print("\n" + "="*80)
    print("🎉 Pipeline Generation Complete!")
    print("="*80)
    
    if final_result:
        # Get the final state from the last chunk
        final_state = list(final_result.values())[0]
        
        # Save pipeline results to output.json
        pipeline_output = {
            "pipeline_steps": [step.model_dump() for step in final_state["pipeline_steps"]],
            "debate_rounds": final_state["debate_rounds"],
            "consensus_reached": final_state["consensus_reached"],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "gap_escalation_count": final_state.get("gap_escalation_count", 0),
                "feedback_rounds": len(final_state.get("feedback_history", [])),
                "total_steps": len(final_state["pipeline_steps"])
            }
        }
        
        with open("output.json", "w") as f:
            json.dump(pipeline_output, f, indent=2, default=str)
        
        logger.info("pipeline_output_saved", 
                   file="output.json", 
                   total_steps=len(final_state["pipeline_steps"]),
                   consensus_reached=final_state["consensus_reached"])
        
        print(f"\n📊 Generated {len(final_state['pipeline_steps'])} pipeline steps:")
        print(f"🔄 Debate rounds: {final_state['debate_rounds']}")
        print(f"✅ Consensus: {'Yes' if final_state['consensus_reached'] else 'No'}")
        print(f"💾 Results saved to: output.json")
        
        print("\n" + "="*80)
        print("📋 FINAL PIPELINE STEPS:")
        print("="*80)
        
        for i, step in enumerate(final_state["pipeline_steps"], 1):
            print(f"\n{i}. **{step.step_name}**")
            
            if verbose:
                # Show full rationale and code in verbose mode
                print(f"\n   📝 RATIONALE:")
                print(f"   {step.rationale}")
                
                if step.code_snippet.strip():
                    print(f"\n   💻 CODE:")
                    # Indent code for better readability
                    code_lines = step.code_snippet.split('\n')
                    for line in code_lines:
                        print(f"   {line}")
                
                print("\n" + "-"*80)
            else:
                # Show summary in normal mode
                print(f"   Rationale: {step.rationale[:100]}{'...' if len(step.rationale) > 100 else ''}")
                if step.code_snippet.strip():
                    print(f"   Code Preview: {step.code_snippet[:80]}{'...' if len(step.code_snippet) > 80 else ''}")
                print()
    else:
        print("❌ No results generated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Data Engineering Swarm")
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Show detailed output including full rationales and code"
    )
    parser.add_argument(
        "--task",
        default="Build ETL pipeline for sales_data.csv",
        help="Custom task description for the pipeline"
    )
    
    args = parser.parse_args()
    
    # Update initial state with custom task if provided
    if args.task != "Build ETL pipeline for sales_data.csv":
        def setup_initial_state_custom():
            return {
                "task": args.task,
                "refined_prompt": "",
                "pipeline_steps": [],
                "debate_rounds": 0,
                "consensus_reached": False,
                "discovered_tools": {},
                "feedback_summary": "",
                "feedback_history": [],
                "gap_escalation_count": 0,
                "current_data_path": "data/sales_data.csv",
                "data_format": "csv",
                "pipeline_metadata": {},
            }
        
        # Replace the function globally for this run
        globals()['setup_initial_state'] = setup_initial_state_custom
    
    asyncio.run(main(verbose=args.verbose))
