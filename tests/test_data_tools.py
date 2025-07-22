# tests/test_data_tools.py
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.data_tools import load_csv, mcp


@pytest.fixture
def mock_pd():
    with patch("tools.data_tools.pd.read_csv") as mock_read:
        mock_df = MagicMock()
        mock_df.to_json.return_value = '[{"col": "val"}]'
        mock_df.__len__.return_value = 10
        mock_df.columns = ["col"]
        mock_read.return_value = mock_df
        yield


def test_load_csv_small_file(mock_pd):
    # Mock the context object
    from unittest.mock import MagicMock
    mock_ctx = MagicMock()
    
    # Mock file size to be small
    with patch("tools.data_tools.os.path.getsize", return_value=1024):  # 1KB
        result = load_csv("data/small.csv", mock_ctx)
    
    assert result.data_json is not None
    assert result.metadata["size_mb"] > 0
    assert "sharding_hint" not in result.metadata  # No hint for small files


def test_mcp_tool_registration():
    # Test that MCP server has tools registered
    assert mcp is not None
    # Note: Full MCP testing would require starting server, which we do separately
