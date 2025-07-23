# tests/test_cleaner.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.cleaner import clean_data, build_cleaning_index
from config import PipelineStep


@pytest.mark.asyncio
async def test_clean_data():
    """Test clean_data function with proper mocking"""
    mock_step = PipelineStep(step_name="ingest", code_snippet="", rationale="")
    
    # Mock the retriever invoke method
    mock_doc = MagicMock()
    mock_doc.page_content = "Impute nulls"
    
    with patch("agents.cleaner.retriever") as mock_retriever:
        mock_retriever.invoke.return_value = [mock_doc]
        
        # Mock MCP client
        with patch("agents.cleaner.streamablehttp_client") as mock_client_ctx:
            with patch("agents.cleaner.ClientSession") as mock_session_cls:
                mock_session = AsyncMock()
                mock_session.initialize = AsyncMock()
                mock_session.call_tool.return_value = AsyncMock(
                    structuredContent={
                        "cleaned_json": "[]", 
                        "metadata": {"size_mb": 0.5}
                    }
                )
                mock_session_cls.return_value.__aenter__.return_value = mock_session
                mock_client_ctx.return_value.__aenter__.return_value = (None, None, None)
                
                # Mock the chain - make ainvoke an async function
                with patch("agents.cleaner.chain") as mock_chain:
                    mock_chain.ainvoke = AsyncMock(return_value=PipelineStep(
                        step_name="clean", 
                        code_snippet="df.fillna()", 
                        rationale="Applied cleaning with single-pass processing"
                    ))
                    
                    result = await clean_data("data/test.csv", mock_step)
                    assert isinstance(result, PipelineStep)
                    assert result.step_name == "clean"
                    assert "df.fillna()" in result.code_snippet


def test_build_cleaning_index():
    """Test build_cleaning_index function"""
    with patch("agents.cleaner.vectorstore") as mock_vectorstore:
        mock_vectorstore.add_texts = MagicMock()
        
        build_cleaning_index(["Test rule"])
        
        mock_vectorstore.add_texts.assert_called_once_with(["Test rule"])
