import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def test_mcp():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # List tools (progress check: Should show load_csv, validate_data)
            tools = await session.list_tools()
            print("Available Tools:", [t.name for t in tools.tools])

            # Test load_csv (simulate ingestion)
            load_result = await session.call_tool(
                "load_csv", {"file_path": "data/sales_data.csv"}
            )
            print("Load Result (Structured):", load_result.structuredContent)

            # Test validate_data (simulate validation)
            mock_steps = [{"step_name": "test", "code_snippet": "", "rationale": ""}]
            valid_result = await session.call_tool(
                "validate_data", {"steps": mock_steps}
            )
            print("Validation Result:", valid_result.structuredContent)


asyncio.run(test_mcp())
