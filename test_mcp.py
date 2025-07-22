#!/usr/bin/env python3
"""Test script for MCP server functionality."""

import asyncio
import subprocess
import time
import requests
import json


async def test_mcp_server():
    """Test MCP server startup and basic functionality."""
    print("🧪 Testing MCP Server...")
    
    # Start MCP server in background
    print("Starting MCP server...")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "tools/data_tools.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test server is running
        print("Testing server connectivity...")
        
        # Create test data file if it doesn't exist
        import pandas as pd
        import os
        
        if not os.path.exists("data/test_data.csv"):
            test_df = pd.DataFrame({
                'id': [1, 2, 3],
                'value': [10, 20, 30],
                'category': ['A', 'B', 'C']
            })
            test_df.to_csv("data/test_data.csv", index=False)
            print("Created test data file")
        
        print("✅ MCP server started successfully!")
        print("Server is running on http://127.0.0.1:8000")
        print("You can now test the tools manually or use them in agents.")
        
        # Keep server running for a bit to allow manual testing
        print("\n📝 To test manually:")
        print("1. Keep this server running")
        print("2. In another terminal, try connecting to the MCP server")
        print("3. Press Ctrl+C here to stop the server")
        
        # Wait for user to stop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped.")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())