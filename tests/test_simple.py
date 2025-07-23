# Test basic functionality without MCP dependencies
import pytest
from config import PipelineStep


def test_pipeline_step_creation():
    """Test basic PipelineStep functionality."""
    step = PipelineStep(
        step_name="test_step",
        code_snippet="df = pd.read_csv('test.csv')",
        rationale="Load test data",
    )
    assert step.step_name == "test_step"
    assert "pd.read_csv" in step.code_snippet
    assert "test data" in step.rationale


@pytest.mark.asyncio
async def test_graph_basic_functionality():
    """Test that graph can be imported and used."""
    import pytest
    from graph import app, AgentState

    # Test basic state structure
    state = {
        "task": "test task",
        "refined_prompt": "",
        "pipeline_steps": [],
        "debate_rounds": 0,
        "consensus_reached": False,
        "discovered_tools": {},
    }

    result = await app.ainvoke(state)
    assert "pipeline_steps" in result
    assert len(result["pipeline_steps"]) > 0
    assert result["debate_rounds"] > 0


@pytest.mark.asyncio
async def test_main_app_runs():
    """Test that the main app can execute successfully."""
    import pytest
    from main import setup_initial_state
    from graph import app

    initial_state = setup_initial_state()
    result = await app.ainvoke(initial_state)
    assert (
        len(result["pipeline_steps"]) >= 3
    )  # Our implementation creates multiple steps

    step_names = [step.step_name for step in result["pipeline_steps"]]
    assert "data_ingestion" in step_names
    assert "data_cleaning" in step_names
    assert "data_transformation" in step_names

