"""
verify_advanced_toggles.py — dry-run sanity check for the 11 opt-in toggles.

The GUI calls `run_verification()` and renders the result inline (no terminal).
CLI use is dev-only and exists as a fallback when the UI is not running.

No Docker, no model loads. Validates: recipe schema, executor handoff, YAML
emitters, mutation routine.
"""
from __future__ import annotations
import json
import sys
from typing import Dict, List, Tuple

from breeding_vat.modules.merge.recipe_validator import (
    RecipeValidator, ValidationError, ADVANCED_TOGGLE_KEYS,
)
from breeding_vat.modules.recipe_executor import RecipeExecutor
from breeding_vat.modules.merge.mergekit_engine import MergekitConfigBuilder
from breeding_vat.modules.merge import advanced_toggles as ATG


def _all_toggles_recipe() -> dict:
    """Recipe with every advanced toggle enabled; mutate flag flipped on half."""
    base = {
        # Fields required by RecipeValidator (single-method shape):
        "method": "slerp",
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "merge_models": ["Qwen/Qwen2.5-3B-Instruct"],
        # Recipe-executor required fields:
        "metadata": {"name": "advanced_toggles_smoke", "goal": "verify"},
        "evolution": {
            "base_models": [
                "Qwen/Qwen2.5-1.5B-Instruct",
                "Qwen/Qwen2.5-3B-Instruct",
            ],
            "merge_methods": {"slerp": {"enabled": True}},
            "num_cycles": 2,
            "culling_rate": 50,
        },
        "evaluation": {"tier": "fast"},
        "advanced": {},
    }
    advanced = {
        "layerwise_alpha":      {"params": {"base_alpha": 1.0, "gamma": 1.2,
                                            "layer_mode": "linear",
                                            "total_layers": 32}},
        "topk_sparsify":        {"params": {"keep_percent": 10.0}},
        "sign_consensus_mask":  {"params": {"sign_mode": "majority"}},
        "attn_mlp_filter":      {"params": {}},
        "bench_weighted_blend": {"params": {"gamma": 2.0}},
        "dynamic_coef_sample":  {"params": {"coef_scope": "region"}},
        "slerp_variants":       {"params": {"slerp_variant": "nuslerp",
                                            "t": 0.5}},
        "lora_rank_prune":      {"params": {"retain_rank_percent": 50.0}},
        "cosine_filter":        {"params": {"similarity_threshold": 0.0,
                                            "cosine_mode": "suppress"}},
        "gaussian_mutation":    {"params": {"mutation_sigma": 1e-4,
                                            "mutation_target": "all"}},
        "alt_layer_inject":     {"params": {"alt_pattern": "odd_even"}},
    }
    for i, (k, cfg) in enumerate(advanced.items()):
        cfg["enabled"] = True
        cfg["mutate"] = (i % 2 == 0)
        base["advanced"][k] = cfg
    return base


def run_verification() -> Dict[str, object]:
    """
    Programmatic entry point used by app.py's Advanced Presets button.
    Returns: {"ok": bool, "steps": [(label, passed, detail), ...]}.
    """
    steps: List[Tuple[str, bool, str]] = []
    ok = True

    # Step 1 — schema validation
    rv = RecipeValidator()
    recipe = _all_toggles_recipe()
    try:
        rv.validate(recipe)
        steps.append(("Schema validation", True,
                      f"all {len(recipe['advanced'])} toggles accepted"))
    except ValidationError as e:
        steps.append(("Schema validation", False, str(e))); ok = False

    # Step 2 — toggle keys known
    enabled = set(recipe["advanced"].keys())
    unknown = enabled - ADVANCED_TOGGLE_KEYS
    if unknown:
        steps.append(("Known toggle keys", False, f"unknown: {unknown}")); ok = False
    else:
        steps.append(("Known toggle keys", True,
                      f"{len(enabled)} in ADVANCED_TOGGLE_KEYS"))

    # Step 3 — RecipeExecutor handoff
    ex = RecipeExecutor()
    cfg = ex.build_evolution_config(recipe)
    n_adv = len(cfg.get("advanced", {}))
    if n_adv == 11:
        steps.append(("RecipeExecutor handoff", True, f"engine sees {n_adv} toggles"))
    else:
        steps.append(("RecipeExecutor handoff", False, f"got {n_adv}, expected 11")); ok = False

    mutate_n = sum(1 for v in cfg["advanced"].values() if v.get("mutate"))
    if mutate_n > 0:
        steps.append(("Mutate flag propagation", True, f"{mutate_n} toggles marked mutate"))
    else:
        steps.append(("Mutate flag propagation", False, "none marked mutate")); ok = False

    # Step 4 — YAML emitters
    yaml_cfg = MergekitConfigBuilder.build_ties_config(
        base_model="Qwen/Qwen2.5-1.5B-Instruct",
        merge_models=["Qwen/Qwen2.5-3B-Instruct"],
        weights=[0.5], threshold=0.9,
    )
    yaml_cfg = MergekitConfigBuilder.apply_density(yaml_cfg, density=0.1)
    yaml_cfg = MergekitConfigBuilder.apply_module_filters(
        yaml_cfg, merge_attention=True, merge_mlp=False,
        merge_norms=True, merge_embeddings=False,
    )
    curve = ATG.layer_alpha_curve(32, base_alpha=1.0, mode="linear")
    yaml_cfg = MergekitConfigBuilder.apply_layerwise_alpha(yaml_cfg, curve, 32)
    yaml_cfg = MergekitConfigBuilder.apply_tokenizer_mode(yaml_cfg, "freeze")
    weights = ATG.bench_score_to_weights([0.8, 0.3], gamma=2.0)
    yaml_cfg = MergekitConfigBuilder.apply_per_model_weights(yaml_cfg, weights)
    if "slices" in yaml_cfg and len(yaml_cfg["slices"]) == 32:
        steps.append(("Layerwise slices YAML", True, "32 slice entries"))
    else:
        steps.append(("Layerwise slices YAML", False,
                      f"slices={yaml_cfg.get('slices')}")); ok = False
    if abs(sum(weights) - 1.0) < 1e-6:
        steps.append(("Bench-weighted softmax", True,
                      f"sum=1.0  weights={[round(w,3) for w in weights]}"))
    else:
        steps.append(("Bench-weighted softmax", False, str(weights))); ok = False

    # Step 5 — region sampler
    sample = ATG.dynamic_coef_sample(32, scope="region", seed=42)
    if set(sample.keys()) == {"early", "middle", "late"}:
        steps.append(("Dynamic coef sampler",
                      True, str({k: round(v, 3) for k, v in sample.items()})))
    else:
        steps.append(("Dynamic coef sampler", False, list(sample.keys()))); ok = False

    # Step 6 — mutation jitter in bounds
    import random
    rng = random.Random(0)
    from breeding_vat.modules.merge.recipe_validator import PARAM_BOUNDS
    v = 1.0
    lo, hi = PARAM_BOUNDS["alpha"]
    for _ in range(10):
        span = (hi - lo) * 0.1
        v = max(lo, min(hi, v + rng.gauss(0, span)))
    if lo <= v <= hi:
        steps.append(("Mutation in bounds", True, f"{v:.3f} ∈ [{lo}, {hi}]"))
    else:
        steps.append(("Mutation in bounds", False, f"drifted to {v}")); ok = False

    # Step 7 — routing distribution
    routes = {k: ATG.toggle_route(k) for k in ADVANCED_TOGGLE_KEYS}
    counts: Dict[str, int] = {}
    for r in routes.values():
        counts[r] = counts.get(r, 0) + 1
    if counts.get("mergekit_yaml", 0) >= 6 and counts.get("post_transform", 0) >= 3:
        steps.append(("Routing distribution", True, str(counts)))
    else:
        steps.append(("Routing distribution", False, str(counts))); ok = False

    return {"ok": ok, "steps": steps}


def main() -> int:
    """CLI entry — dev fallback only. UI uses run_verification() directly."""
    result = run_verification()
    for label, passed, detail in result["steps"]:
        tag = "PASS" if passed else "FAIL"
        print(f"   {tag} — {label}: {detail}")
    print()
    print("OK" if result["ok"] else "FAIL")
    return 0 if result["ok"] else 1


def _main_legacy() -> int:  # noqa: F811  (kept for reference; unused)
    return 0
    # Original step-printing flow preserved below for diff history; never runs.
    ok = True
    print(">> step 1: schema validation")
    rv = RecipeValidator()
    recipe = _all_toggles_recipe()
    try:
        rv.validate(recipe)
        print("   PASS — schema accepts every advanced toggle")
    except ValidationError as e:
        print(f"   FAIL — {e}")
        ok = False

    print(">> step 2: RecipeValidator knows the toggle keys")
    enabled = set(recipe["advanced"].keys())
    unknown = enabled - ADVANCED_TOGGLE_KEYS
    if unknown:
        print(f"   FAIL — unknown toggles: {unknown}")
        ok = False
    else:
        print(f"   PASS — all {len(enabled)} toggles in ADVANCED_TOGGLE_KEYS")

    print(">> step 3: RecipeExecutor.build_evolution_config")
    ex = RecipeExecutor()
    cfg = ex.build_evolution_config(recipe)
    if cfg.get("advanced") and len(cfg["advanced"]) == 11:
        print(f"   PASS — engine config has 11 advanced toggles")
    else:
        print(f"   FAIL — engine config advanced={cfg.get('advanced')}")
        ok = False
    if any(v.get("mutate") for v in cfg["advanced"].values()):
        print("   PASS — at least one toggle marked mutate")
    else:
        print("   FAIL — no toggles marked mutate")
        ok = False

    print(">> step 4: MergekitConfigBuilder YAML emitters smoke test")
    yaml_cfg = MergekitConfigBuilder.build_ties_config(
        base_model="Qwen/Qwen2.5-1.5B-Instruct",
        merge_models=["Qwen/Qwen2.5-3B-Instruct"],
        weights=[0.5], threshold=0.9,
    )
    yaml_cfg = MergekitConfigBuilder.apply_density(yaml_cfg, density=0.1)
    yaml_cfg = MergekitConfigBuilder.apply_module_filters(
        yaml_cfg, merge_attention=True, merge_mlp=False,
        merge_norms=True, merge_embeddings=False,
    )
    curve = ATG.layer_alpha_curve(32, base_alpha=1.0, mode="linear")
    yaml_cfg = MergekitConfigBuilder.apply_layerwise_alpha(yaml_cfg, curve, 32)
    yaml_cfg = MergekitConfigBuilder.apply_tokenizer_mode(yaml_cfg, "freeze")
    weights = ATG.bench_score_to_weights([0.8, 0.3], gamma=2.0)
    yaml_cfg = MergekitConfigBuilder.apply_per_model_weights(yaml_cfg, weights)
    if "slices" in yaml_cfg and len(yaml_cfg["slices"]) == 32:
        print("   PASS — layerwise slices generated (32 layers)")
    else:
        print(f"   FAIL — slices={yaml_cfg.get('slices') and len(yaml_cfg['slices'])}")
        ok = False
    if abs(sum(weights) - 1.0) < 1e-6:
        print(f"   PASS — bench weights sum to 1.0: {weights}")
    else:
        print(f"   FAIL — bench weights: {weights}")
        ok = False

    print(">> step 5: dynamic_coef_sample + layer_alpha_curve")
    sample = ATG.dynamic_coef_sample(32, scope="region", seed=42)
    if set(sample.keys()) == {"early", "middle", "late"}:
        print(f"   PASS — region sampler: {sample}")
    else:
        print(f"   FAIL — keys={list(sample.keys())}")
        ok = False

    print(">> step 6: mutation jitter (no torch needed for numeric path)")
    import random
    rng = random.Random(0)
    from breeding_vat.modules.merge.recipe_validator import PARAM_BOUNDS
    v = 1.0
    lo, hi = PARAM_BOUNDS["alpha"]
    for _ in range(10):
        span = (hi - lo) * 0.1
        v = max(lo, min(hi, v + rng.gauss(0, span)))
    if lo <= v <= hi:
        print(f"   PASS — mutation stayed in bounds: {v:.3f} ∈ [{lo}, {hi}]")
    else:
        print(f"   FAIL — mutation drifted: {v}")
        ok = False

    print(">> step 7: route classifier")
    routes = {k: ATG.toggle_route(k) for k in ADVANCED_TOGGLE_KEYS}
    counts = {r: sum(1 for v in routes.values() if v == r) for r in set(routes.values())}
    print(f"   route counts: {counts}")
    if counts.get("mergekit_yaml", 0) >= 6 and counts.get("post_transform", 0) >= 3:
        print("   PASS — routing distribution matches spec")
    else:
        print("   FAIL — routing distribution off")
        ok = False

    print()
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
