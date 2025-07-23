# main.py
import asyncio
import argparse
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


def setup_initial_state():
    return {
        "task": "Build ETL pipeline for sales_data.csv",
        "refined_prompt": "",
        "pipeline_steps": [],
        "debate_rounds": 0,
        "consensus_reached": False,
        "discovered_tools": {},
    }


async def main(verbose=False):
    print("🚀 Starting Multi-Agent Data Engineering Swarm...")
    print("📚 Setting up RAG indexes...")
    setup_indexes()
    
    print("🎯 Initializing pipeline state...")
    initial_state = setup_initial_state()
    
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
                print(f"✏️  Prompt Engineer: Task refined and structured")
                if verbose:
                    refined_prompt = node_output.get('refined_prompt', '')
                    print(f"   Refined Task: {refined_prompt[:200]}{'...' if len(refined_prompt) > 200 else ''}")
                
            elif node_name == "ingest":
                print(f"📥 Data Ingestor: Data loaded and profiled")
                if verbose:
                    steps = node_output.get('pipeline_steps', [])
                    if steps:
                        latest_step = steps[-1]
                        print(f"   Step: {latest_step.step_name}")
                        print(f"   Details: {latest_step.rationale[:150]}{'...' if len(latest_step.rationale) > 150 else ''}")
                
            elif node_name == "clean":
                print(f"🧹 Data Cleaner: Applied cleaning transformations")
                if verbose:
                    steps = node_output.get('pipeline_steps', [])
                    if steps:
                        latest_step = steps[-1]
                        print(f"   Step: {latest_step.step_name}")
                        print(f"   Details: {latest_step.rationale[:150]}{'...' if len(latest_step.rationale) > 150 else ''}")
                
            elif node_name == "transform":
                print(f"⚡ Data Transformer: Feature engineering completed")
                if verbose:
                    steps = node_output.get('pipeline_steps', [])
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
        
        print(f"\n📊 Generated {len(final_state['pipeline_steps'])} pipeline steps:")
        print(f"🔄 Debate rounds: {final_state['debate_rounds']}")
        print(f"✅ Consensus: {'Yes' if final_state['consensus_reached'] else 'No'}")
        
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
            }
        
        # Replace the function globally for this run
        globals()['setup_initial_state'] = setup_initial_state_custom
    
    asyncio.run(main(verbose=args.verbose))
