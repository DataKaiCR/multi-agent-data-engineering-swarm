#!/usr/bin/env python3
"""Debug clean_data function."""

import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def test_clean_only():
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🧪 Testing clean_data function specifically...")
            
            try:
                # Test clean_data
                clean_result = await session.call_tool(
                    "clean_data",
                    {
                        "file_path": "data/sales_data.csv",
                        "ingest_metadata": {"test": "data"},
                    },
                )
                print(f"Clean result type: {type(clean_result)}")
                print(f"Clean result: {clean_result}")
                print(f"Clean result structured content: {clean_result.structuredContent}")
                
            except Exception as e:
                print(f"❌ Error calling clean_data: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_clean_only())