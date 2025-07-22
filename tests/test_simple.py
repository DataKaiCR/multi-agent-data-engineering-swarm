# Test basic functionality without MCP dependencies
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PipelineStep


def test_pipeline_step_creation():
    """Test basic PipelineStep functionality."""
    step = PipelineStep(
        step_name="test_step",
        code_snippet="df = pd.read_csv('test.csv')",
        rationale="Load test data"
    )
    assert step.step_name == "test_step"
    assert "pd.read_csv" in step.code_snippet
    assert "test data" in step.rationale


def test_graph_basic_functionality():
    """Test that graph can be imported and used."""
    from graph import app, AgentState
    
    # Test basic state structure
    state = {
        "task": "test task",
        "refined_prompt": "",
        "pipeline_steps": [],
        "debate_rounds": 0,
        "consensus_reached": False,
    }
    
    result = app.invoke(state)
    assert "pipeline_steps" in result
    assert len(result["pipeline_steps"]) > 0
    assert result["debate_rounds"] > 0


def test_main_app_runs():
    """Test that the main app can execute successfully."""
    from main import initial_state
    from graph import app
    
    result = app.invoke(initial_state)
    assert len(result["pipeline_steps"]) == 3  # Our simple implementation creates 3 steps
    
    step_names = [step.step_name for step in result["pipeline_steps"]]
    assert "data_ingestion" in step_names
    assert "data_cleaning" in step_names  
    assert "data_transformation" in step_names