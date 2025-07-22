#!/usr/bin/env python3
"""Test script to debug Chroma import issues."""

import sys
import os

print("Python executable:", sys.executable)
print("Python path:", sys.path[:3], "...")

print("\n=== Testing imports ===")

try:
    import chromadb
    print("✅ chromadb imported successfully")
except ImportError as e:
    print("❌ chromadb failed:", e)

try:
    from langchain_chroma import Chroma
    print("✅ langchain_chroma imported successfully")
except ImportError as e:
    print("❌ langchain_chroma failed:", e)

try:
    from langchain_openai import OpenAIEmbeddings
    print("✅ langchain_openai imported successfully")  
except ImportError as e:
    print("❌ langchain_openai failed:", e)

try:
    import mcp
    print("✅ mcp imported successfully")
except ImportError as e:
    print("❌ mcp failed:", e)

print("\n=== Testing agents import ===")

try:
    from agents.cleaner import clean_data
    print("✅ agents.cleaner imported successfully")
except ImportError as e:
    print("❌ agents.cleaner failed:", e)

print("\nDebugging complete!")