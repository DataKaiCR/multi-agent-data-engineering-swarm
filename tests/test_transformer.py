# tests/test_transformer.py
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.transformer import transform_data, build_transform_index
from config import PipelineStep


@pytest.mark.asyncio
async def test_transform_data():
    mock_step = PipelineStep(step_name="clean", code_snippet="", rationale="")
    with patch(
        "agents.transformer.retriever.invoke",
        return_value=[AsyncMock(page_content="Scale numerics")],
    ):
        with patch("agents.transformer.streamablehttp_client") as mock_client:
            mock_session = AsyncMock()
            mock_session.call_tool.return_value = AsyncMock(
                structuredContent={
                    "transformed_json": "[]",
                    "metadata": {"size_mb": 0.5},
                }
            )
            mock_client.__aenter__.return_value = (None, None, None)
            mock_client.ClientSession.return_value = mock_session
            with patch(
                "agents.transformer.chain.ainvoke",
                return_value=PipelineStep(
                    step_name="transform",
                    code_snippet="scaler.fit_transform()",
                    rationale="Mock",
                ),
            ):
                result = await transform_data("data/test.csv", mock_step)
                assert isinstance(result, PipelineStep)
                assert "single-pass" in result.rationale


def test_build_transform_index():
    with patch("agents.transformer.vectorstore.add_texts") as mock_add:
        with patch("agents.transformer.vectorstore.persist") as mock_persist:
            build_transform_index(["Test rule"])
            mock_add.assert_called_once_with(["Test rule"])
            mock_persist.assert_called_once()
