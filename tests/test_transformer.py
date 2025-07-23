# tests/test_transformer.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.transformer import transform_data, build_transform_index
from config import PipelineStep


@pytest.mark.asyncio
async def test_transform_data():
    """Test transform_data function with proper mocking"""
    mock_step = PipelineStep(step_name="clean", code_snippet="", rationale="")
    
    # Mock the retriever invoke method
    mock_doc = MagicMock()
    mock_doc.page_content = "Scale numerics"
    
    with patch("agents.transformer.retriever") as mock_retriever:
        mock_retriever.invoke.return_value = [mock_doc]
        
        # Mock MCP client
        with patch("agents.transformer.streamablehttp_client") as mock_client_ctx:
            with patch("agents.transformer.ClientSession") as mock_session_cls:
                mock_session = AsyncMock()
                mock_session.initialize = AsyncMock()
                mock_session.call_tool.return_value = AsyncMock(
                    structuredContent={
                        "transformed_json": "[]",
                        "metadata": {"size_mb": 0.5},
                    }
                )
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                mock_client_ctx.return_value.__aenter__.return_value = (None, None, None)
                
                # Mock the chain - make ainvoke an async function
                with patch("agents.transformer.chain") as mock_chain:
                    mock_chain.ainvoke = AsyncMock(return_value=PipelineStep(
                        step_name="transform",
                        code_snippet="scaler.fit_transform()",
                        rationale="Applied transformations with single-pass processing",
                    ))
                    
                    result = await transform_data("data/test.csv", mock_step)
                    assert isinstance(result, PipelineStep)
                    assert result.step_name == "transform"
                    assert "scaler.fit_transform()" in result.code_snippet


def test_build_transform_index():
    """Test build_transform_index function - no persist() method in new Chroma"""
    with patch("agents.transformer.vectorstore") as mock_vectorstore:
        mock_vectorstore.add_texts = MagicMock()
        
        build_transform_index(["Test rule"])
        
        # Only test add_texts since persist() doesn't exist in new Chroma version
        mock_vectorstore.add_texts.assert_called_once_with(["Test rule"])
