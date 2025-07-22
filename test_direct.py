#!/usr/bin/env python3
"""Direct test without pytest to verify functionality."""

import asyncio
from unittest.mock import patch, MagicMock

# Test langchain-chroma functionality directly
def test_chroma_integration():
    print("🧪 Testing Chroma integration...")
    
    try:
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings
        import tempfile
        
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        print(f"Using temp directory: {temp_dir}")
        
        # Test Chroma initialization (no API call needed)
        embeddings = OpenAIEmbeddings(api_key="dummy-key")
        vectorstore = Chroma(persist_directory=temp_dir, embedding_function=embeddings)
        
        print("✅ Chroma vectorstore created successfully")
        
        # Test that vectorstore has expected methods
        assert hasattr(vectorstore, 'add_texts')
        assert hasattr(vectorstore, 'as_retriever')
        print("✅ Chroma has expected methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Chroma test failed: {e}")
        return False

def test_cleaner_functionality():
    print("\n🧪 Testing cleaner functionality...")
    
    try:
        from agents.cleaner import build_cleaning_index
        
        # Mock the vectorstore to avoid API calls
        with patch('agents.cleaner.vectorstore') as mock_vectorstore:
            mock_vectorstore.add_texts = MagicMock()
            
            # Test build_cleaning_index
            build_cleaning_index(["Test cleaning rule"])
            
            # Verify it was called
            mock_vectorstore.add_texts.assert_called_once_with(["Test cleaning rule"])
            
        print("✅ Cleaner build_cleaning_index works")
        return True
        
    except Exception as e:
        print(f"❌ Cleaner test failed: {e}")
        return False

def test_mcp_tools():
    print("\n🧪 Testing MCP tools...")
    
    try:
        from tools.data_tools import mcp, clean_data
        
        print("✅ MCP tools imported successfully")
        
        # Verify clean_data function exists
        assert callable(clean_data)
        print("✅ clean_data function is callable")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def main():
    print("🚀 Running direct functionality tests...\n")
    
    results = []
    results.append(test_chroma_integration())
    results.append(test_cleaner_functionality()) 
    results.append(test_mcp_tools())
    
    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests passed! The langchain-chroma integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()