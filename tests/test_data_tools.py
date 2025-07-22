# tests/test_data_tools.py
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.data_tools import load_csv, mcp_client


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
    result = load_csv("data/small.csv")
    assert "data_json" in result
    assert result["metadata"]["size_mb"] > 0
    assert "sharding_hint" not in result["metadata"]  # No hint for small


def test_mcp_tool_registration():
    tools = mcp_client.list_tools()  # Assume SDK method
    assert "load_csv" in [t["name"] for t in tools]  # Verify wrapping
