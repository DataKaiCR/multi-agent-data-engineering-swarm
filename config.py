from pathlib import Path
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from typing import Dict, Any
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Project root (dynamic, avoids hardcoding)
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "indexes"


class PipelineStep(BaseModel):
    step_name: str = Field(description="Name of the pipeline step")
    code_snippet: str = Field(description="Python code for this step")
    rationale: str = Field(description="Why this step?")


# Model configurations
MODEL_CONFIGS = [
    {
        "agent_role": "prompt_engineer",
        "model_provider": "openai",
        "model": "gpt-4o-mini",
        "config": {"api_key": os.getenv("OPENAI_API_KEY"), "temperature": 0.2},
    },
    {
        "agent_role": "ingestor",
        "model_provider": "openai",
        "model": "gpt-4o",
        "config": {"api_key": os.getenv("OPENAI_API_KEY"), "temperature": 0.5},
    },
    {
        "agent_role": "cleaner",
        "model_provider": "anthropic",
        "model": "claude-3-5-sonnet-20240620",
        "config": {"api_key": os.getenv("ANTHROPIC_API_KEY"), "temperature": 0.5},
    },
    {
        "agent_role": "transformer",
        "model_provider": "xai",  # Placeholder
        "model": "grok-3",
        "config": {"api_key": os.getenv("XAI_API_KEY"), "temperature": 0.8},
    },
    {
        "agent_role": "validator",
        "model_provider": "xai",  # Placeholder
        "model": "grok-3",
        "config": {"api_key": os.getenv("XAI_API_KEY"), "temperature": 0.2},
    },
    ##{
    ##    "agent_role": "validator",
    ##    "model_provider": "ollama",
    ##    "model": "llama3.2:3b",
    ##    "config": {"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")},
    ##},
]

# Initialize models with error handling
MODELS: Dict[str, Any] = {}
for config in MODEL_CONFIGS:
    try:
        MODELS[config["agent_role"]] = init_chat_model(
            model=config["model"],
            model_provider=config["model_provider"],
            **config["config"],
        )
    except Exception as e:
        print(f"Error initializing {config['agent_role']}: {e}")
        # Fallback: Use a local model or skip
        MODELS[config["agent_role"]] = None  # Placeholder for fallback logic
