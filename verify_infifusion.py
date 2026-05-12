import sys
sys.path.insert(0, '.')

print("\n" + "="*70)
print("InfiFusion Integration Verification")
print("="*70 + "\n")

# Test 1: InfiFusionEngine initialization
print("[1] Testing InfiFusionEngine initialization...")
try:
    from breeding_vat.modules.merge.infifusion_engine import InfiFusionEngine
    engine = InfiFusionEngine()
    print("    [PASS] InfiFusionEngine imported and initialized")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 2: InfiFusion registered in AdvancedMerger
print("\n[2] Testing InfiFusion in AdvancedMerger...")
try:
    from breeding_vat.modules.merge.merger import AdvancedMerger
    merger = AdvancedMerger()
    methods = merger.get_available_methods()
    assert 'infifusion' in methods, "infifusion not in methods"
    print("    [PASS] InfiFusion registered in AdvancedMerger")
    print(f"    Total methods available: {len(methods)}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 3: InfiFusion recommendations in SpecializationAdvisor
print("\n[3] Testing InfiFusion in SpecializationAdvisor...")
try:
    from breeding_vat.modules.specialize.advisor import SpecializationAdvisor
    rec = SpecializationAdvisor.get_recommendation(
        merge_methods=['infifusion'],
        goal='Extend context to 32K tokens',
        num_models=2
    )
    print("    [PASS] InfiFusion recommendation retrieved")
    print(f"    Recommendation: {rec['overall_recommendation']}")
    print(f"    Strategy: {rec['suggested_strategy']}")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 4: Docker image file exists
print("\n[4] Testing Docker image file...")
try:
    import os
    dockerfile_path = "docker/Dockerfile.infifusion"
    assert os.path.exists(dockerfile_path), f"{dockerfile_path} not found"
    print("    [PASS] Dockerfile.infifusion exists")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 5: InfiFusion method callable
print("\n[5] Testing infifusion_merge method...")
try:
    assert hasattr(merger, 'infifusion_merge'), "infifusion_merge method not found"
    assert callable(merger.infifusion_merge), "infifusion_merge not callable"
    print("    [PASS] infifusion_merge method exists and is callable")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

# Test 6: Config validation
print("\n[6] Testing InfiFusion config validation...")
try:
    valid_config = {
        "base_model": "Qwen-3B",
        "merge_models": ["Llama-3B-long"],
        "target_context": 32000,
        "num_bands": 3
    }
    is_valid, msg = engine.validate_config(valid_config)
    assert is_valid, f"Config validation failed: {msg}"
    print("    [PASS] Config validation working")
except Exception as e:
    print(f"    [FAIL] {e}")
    sys.exit(1)

print("\n" + "="*70)
print("All tests passed!")
print("="*70 + "\n")
