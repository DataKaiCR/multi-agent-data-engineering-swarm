# tests/test_graph.py
import pytest
from unittest.mock import patch, AsyncMock
from graph import app
from config import PipelineStep


@pytest.mark.asyncio
async def test_graph_workflow():
    with patch(
        "graph.discovery_node",
        return_value={"discovered_tools": {"ingest": "load_csv"}},
    ):
        with patch(
            "graph.prompt_node",
            return_value={
                "refined_prompt": "Mock refine",
                "pipeline_steps": [PipelineStep(step_name="test", code_snippet="", rationale="test")],
            },
        ):
            with patch(
                "graph.ingest_node",
                return_value={"pipeline_steps": [PipelineStep(...)]},
            ):
                with patch(
                    "graph.clean_node",
                    return_value={"pipeline_steps": [PipelineStep(...)]},
                ):
                    with patch(
                        "graph.transform_node",
                        return_value={"pipeline_steps": [PipelineStep(...)]},
                    ):
                        with patch(
                            "graph.debate_node",
                            return_value={
                                "consensus_reached": True,
                                "pipeline_steps": [PipelineStep(step_name="test", code_snippet="", rationale="test")],
                            },
                        ):
                            initial = {"task": "test", "pipeline_steps": []}
                            result = await app.ainvoke(initial)
                            assert len(result["pipeline_steps"]) > 0
                            assert result["consensus_reached"]
