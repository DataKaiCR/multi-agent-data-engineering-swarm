# tests/test_cleaner.py
import sys
import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.cleaner import clean_data, build_cleaning_index
from config import PipelineStep


@pytest.mark.asyncio
async def test_clean_data():
    mock_step = PipelineStep(step_name="ingest", code_snippet="", rationale="")
    with patch(
        "agents.cleaner.retriever.invoke",
        return_value=[AsyncMock(page_content="Impute nulls")],
    ):
        with patch("agents.cleaner.streamablehttp_client") as mock_client:
            mock_session = AsyncMock()
            mock_session.call_tool.return_value = AsyncMock(
                structuredContent={"cleaned_json": "[]", "metadata": {"size_mb": 0.5}}
            )
            mock_client.__aenter__.return_value = (None, None, None)
            mock_client.ClientSession.return_value = mock_session
            with patch(
                "agents.cleaner.chain.ainvoke",
                return_value=PipelineStep(
                    step_name="clean", code_snippet="df.fillna()", rationale="Mock"
                ),
            ):
                result = await clean_data("data/test.csv", mock_step)
                assert isinstance(result, PipelineStep)
                assert "single-pass" in result.rationale


def test_build_cleaning_index():
    with patch("agents.cleaner.vectorstore.add_texts") as mock_add:
        build_cleaning_index(["Test rule"])
        mock_add.assert_called_once_with(["Test rule"])
