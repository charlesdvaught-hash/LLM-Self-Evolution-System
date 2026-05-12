"""
InfiFusion Integration Test

Tests that InfiFusion engine is properly integrated into the breeding vat system.
"""

import os
import json
import logging

logger = logging.getLogger("InfiFusionTest")


def test_infifusion_engine_initialization():
    """Test InfiFusionEngine initializes correctly."""
    from breeding_vat.modules.merge.infifusion_engine import InfiFusionEngine
    
    engine = InfiFusionEngine()
    assert engine is not None
    assert engine.output_dir == "breeding_vat/data/merged_models"
    
    # Test config template
    template = engine.get_config_template()
    assert template["method"] == "infifusion"
    assert template["target_context"] == 32000
    assert template["num_bands"] == 3
    
    print("✅ InfiFusionEngine initialization test passed")


def test_infifusion_in_merger():
    """Test InfiFusion method is registered in AdvancedMerger."""
    from breeding_vat.modules.merge.merger import AdvancedMerger
    
    merger = AdvancedMerger()
    methods = merger.get_available_methods()
    
    assert "infifusion" in methods
    assert "Infinite Context Fusion" in methods["infifusion"]
    
    print("✅ InfiFusion in AdvancedMerger test passed")


def test_infifusion_in_advisor():
    """Test InfiFusion recommendations in SpecializationAdvisor."""
    from breeding_vat.modules.specialize.advisor import SpecializationAdvisor
    
    # Check that infifusion is in recommendations
    assert "infifusion" in SpecializationAdvisor.RECOMMENDATIONS
    
    rec = SpecializationAdvisor.RECOMMENDATIONS["infifusion"]
    assert rec["recommendation"] in ["MANDATORY", "RECOMMENDED", "OPTIONAL"]
    
    # Test getting recommendation for infifusion
    recommendation = SpecializationAdvisor.get_recommendation(
        merge_methods=["infifusion"],
        goal="Extend context to 32K",
        num_models=2
    )
    
    assert recommendation["overall_recommendation"] == "RECOMMENDED"
    assert "sae_guided" in recommendation["methods_analysis"]["infifusion"]["strategies"]
    
    print("✅ InfiFusion in SpecializationAdvisor test passed")


def test_infifusion_config_validation():
    """Test InfiFusion config validation."""
    from breeding_vat.modules.merge.infifusion_engine import InfiFusionEngine
    
    engine = InfiFusionEngine()
    
    # Valid config
    valid_config = {
        "base_model": "Qwen-3B",
        "merge_models": ["Llama-3B-long"],
        "target_context": 32000,
        "num_bands": 3
    }
    
    is_valid, msg = engine.validate_config(valid_config)
    assert is_valid, msg
    
    # Invalid config: missing base_model
    invalid_config_1 = {
        "merge_models": ["Llama-3B-long"],
        "target_context": 32000
    }
    
    is_valid, msg = engine.validate_config(invalid_config_1)
    assert not is_valid
    
    # Invalid config: target context too small
    invalid_config_2 = {
        "base_model": "Qwen-3B",
        "merge_models": ["Llama-3B-long"],
        "target_context": 1024
    }
    
    is_valid, msg = engine.validate_config(invalid_config_2)
    assert not is_valid
    
    print("✅ InfiFusion config validation test passed")


def test_infifusion_docker_image_exists():
    """Test that Dockerfile.infifusion exists."""
    dockerfile_path = "docker/Dockerfile.infifusion"
    
    assert os.path.exists(dockerfile_path), f"{dockerfile_path} not found"
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
        assert "pytorch/pytorch" in content
        assert "transformers" in content
    
    print("✅ InfiFusion Docker image test passed")


def test_infifusion_merge_method_call():
    """Test that infifusion_merge method exists and is callable."""
    from breeding_vat.modules.merge.merger import AdvancedMerger
    
    merger = AdvancedMerger()
    
    # Check method exists
    assert hasattr(merger, 'infifusion_merge')
    assert callable(merger.infifusion_merge)
    
    print("✅ InfiFusion merge method test passed")


def run_all_tests():
    """Run all InfiFusion integration tests."""
    print("\n" + "="*60)
    print("Running InfiFusion Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        test_infifusion_engine_initialization,
        test_infifusion_in_merger,
        test_infifusion_in_advisor,
        test_infifusion_config_validation,
        test_infifusion_docker_image_exists,
        test_infifusion_merge_method_call,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
