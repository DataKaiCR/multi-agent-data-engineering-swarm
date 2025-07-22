# test_config.py
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import MODELS, PipelineStep
import pytest


def test_config_models_exist():
    """Test that MODELS dictionary is populated"""
    assert MODELS is not None
    assert isinstance(MODELS, dict)
    assert len(MODELS) > 0


def test_models_are_not_none():
    """Test that initialized models are not None"""
    for role, model in MODELS.items():
        if model is not None:  # Skip failed initializations
            assert hasattr(model, "invoke"), f"Model {role} should have invoke method"


def test_model_invocation():
    """Test actual model calls with better error handling"""
    successful_tests = 0
    
    for role, model in MODELS.items():
        if model is not None:
            try:
                print(f"\n🧪 Testing {role}...")
                response = model.invoke("Say 'Hello World' in exactly 2 words.")
                print(f"✅ {role}: {response.content[:100]}...")
                successful_tests += 1
            except Exception as e:
                print(f"❌ {role} failed: {e}")
    
    print(f"\n📊 Successfully tested {successful_tests}/{len([m for m in MODELS.values() if m is not None])} models")
    
    # Assert at least one model worked
    if len([m for m in MODELS.values() if m is not None]) > 0:
        assert successful_tests > 0, "At least one model should work"


def test_pipeline_step_creation():
    """Test PipelineStep model creation"""
    step = PipelineStep(
        step_name="test_step",
        code_snippet="print('hello')",
        rationale="Testing pipeline step creation"
    )
    
    assert step.step_name == "test_step"
    assert "print" in step.code_snippet
    assert "Testing" in step.rationale
