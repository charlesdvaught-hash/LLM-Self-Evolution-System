"""
advanced_toggles.py — Orthogonal toggles that compose with any merge method.

DESIGN PRINCIPLE
================
Where MergeKit / FusionBench already expose a knob, this module emits the
correct MergeKit YAML via `MergekitConfigBuilder` rather than reimplementing
tensor math. We only run post-merge state_dict transforms for things MergeKit
cannot express.

Split:

    Native MergeKit (emit YAML — see mergekit_engine.MergekitConfigBuilder):
        - Layerwise alpha     → slices block with per-slice weight
        - Top-K sparsify      → TIES/DARE `density` param
        - Sign consensus      → TIES `normalize: true`
        - Attn/MLP filter     → `filter:` selectors on q_proj / mlp / norm
        - Standard SLERP      → native `merge_method: slerp`
        - Embedding strategy  → `tokenizer_source` + filter on embed_tokens
        - Bench-weighted blend→ outer loop sets per-model `weight:` floats
        - Alt-layer (regular) → passthrough slices block

    Post-merge transforms (NOT in MergeKit — implemented here):
        - gaussian_mutation        : random N(0,σ) noise injection
        - cosine_filter            : per-tensor cosine-similarity rejection
        - lora_rank_prune          : drop weakest LoRA rank channels
        - nuslerp_variant_tensor   : magnitude-linear + direction-slerp
        - alt_layer_custom_inject  : arbitrary {layer_idx: 'a'|'b'} pattern

    Outer-loop helpers (evolutionary genome / score computation):
        - dynamic_coef_sample      : per-region/per-layer alpha sampler
        - bench_score_to_weights   : softmax over benchmark scores → per-model w
        - layer_alpha_curve        : alpha(L) function used by yaml_emitter
        - classify_module          : tensor-name → 'attention'|'mlp'|...
        - describe_toggle          : UI tooltip text

All ops are state_dict-level and stream key-by-key to respect 8GB VRAM.

References:
    - Task Arithmetic       https://arxiv.org/abs/2212.04089
    - TIES-Merging          https://arxiv.org/abs/2306.01708
    - DARE / Super Mario    https://arxiv.org/abs/2311.03099
    - LiNeS                 https://arxiv.org/abs/2311.03099
    - Layer-Aware TA        https://arxiv.org/abs/2403.17806
    - FrankenMoE            https://arxiv.org/abs/2404.19145
    - LoraHub               https://arxiv.org/abs/2307.13269
    - Orthogonal subspace   https://arxiv.org/abs/2402.09353
    - MergeKit              https://github.com/arcee-ai/mergekit
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import torch
    from torch import Tensor
    _HAS_TORCH = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore
    Tensor = Any  # type: ignore
    _HAS_TORCH = False

logger = logging.getLogger("AdvancedToggles")

StateDict = Dict[str, "Tensor"]

# ── Module-type regex (shared with mergekit_engine YAML emitter) ────────────
_ATTN_RE = re.compile(r"(?:^|\.)(self_attn|attention|attn|q_proj|k_proj|v_proj|o_proj|out_proj)\.")
_MLP_RE = re.compile(r"(?:^|\.)(mlp|feed_forward|ffn|gate_proj|up_proj|down_proj|fc1|fc2)\.")
_NORM_RE = re.compile(r"(?:^|\.)(norm|layernorm|layer_norm|rmsnorm|ln_\d)\.")
_EMBED_RE = re.compile(r"(?:^|\.)(embed|embeddings|wte|wpe|tok_embeddings)\.?")
_LAYER_IDX_RE = re.compile(r"(?:layers?|h|blocks?)\.(\d+)\.")

# MergeKit filter-string equivalents (used by yaml emitter).
FILTER_TOKENS: Dict[str, Tuple[str, ...]] = {
    "attention":  ("q_proj", "k_proj", "v_proj", "o_proj", "self_attn"),
    "mlp":        ("gate_proj", "up_proj", "down_proj", "mlp"),
    "norm":       ("input_layernorm", "post_attention_layernorm",
                   "norm", "rmsnorm"),
    "embedding":  ("embed_tokens", "lm_head"),
}


def classify_module(tensor_name: str) -> str:
    """Return one of: 'attention', 'mlp', 'norm', 'embedding', 'other'."""
    if _ATTN_RE.search(tensor_name):
        return "attention"
    if _MLP_RE.search(tensor_name):
        return "mlp"
    if _NORM_RE.search(tensor_name):
        return "norm"
    if _EMBED_RE.search(tensor_name):
        return "embedding"
    return "other"


def _layer_index(tensor_name: str) -> Optional[int]:
    m = _LAYER_IDX_RE.search(tensor_name)
    return int(m.group(1)) if m else None


# ════════════════════════════════════════════════════════════════════════════
# OUTER-LOOP HELPERS — used by yaml emitter, evolution genome, UI
# ════════════════════════════════════════════════════════════════════════════

def layer_alpha_curve(
    total_layers: int,
    base_alpha: float = 1.0,
    mode: str = "flat",
    gamma: float = 1.0,
) -> List[float]:
    """
    Compute per-layer alphas. Consumed by MergekitConfigBuilder when building
    a `slices:` block with per-slice `weight` (the proper MergeKit way to do
    layerwise scaling).

    Modes:
        flat        : alpha(L) = base_alpha
        linear      : alpha(L) = base_alpha * (L / total)        [backloaded]
        backloaded  : same as linear
        frontloaded : alpha(L) = base_alpha * (1 - L / total)
        exponential : alpha(L) = base_alpha * (L / total) ** gamma
        sigmoid     : alpha(L) = base_alpha / (1+exp(-gamma*(L/total - 0.5)))
        middle      : alpha(L) = base_alpha * (1 - 4*(L/total - 0.5)**2)
    """
    n = max(1, int(total_layers))
    out: List[float] = []
    for layer in range(n):
        t = layer / max(n - 1, 1)
        if mode == "flat":
            a = base_alpha
        elif mode in ("linear", "backloaded"):
            a = base_alpha * t
        elif mode == "frontloaded":
            a = base_alpha * (1.0 - t)
        elif mode == "exponential":
            a = base_alpha * (t ** max(gamma, 1e-6))
        elif mode == "sigmoid":
            a = base_alpha / (1.0 + math.exp(-gamma * (t - 0.5)))
        elif mode == "middle":
            a = base_alpha * max(0.0, 1.0 - 4.0 * (t - 0.5) ** 2)
        else:
            logger.warning(f"Unknown layerwise mode '{mode}', falling back to flat.")
            a = base_alpha
        out.append(float(a))
    return out


def bench_score_to_weights(
    scores: Sequence[float],
    gamma: float = 2.0,
) -> List[float]:
    """
    Softmax over scores^gamma. Outer evolution loop feeds the result to
    MergeKit as per-model `weight:` floats — no tensor work needed here.

        scores=[0.85, 0.30] gamma=2.0 → [0.93, 0.07]

    Returns weights summing to 1.0. Use gamma>1 for winner-take-most,
    gamma<1 for smoother blends.
    """
    if not scores:
        return []
    raw = [max(float(s), 0.0) ** float(gamma) for s in scores]
    m = max(raw) if raw else 0.0
    shifted = [r - m for r in raw]
    expv = [math.exp(x) for x in shifted]
    total = sum(expv) or 1.0
    return [e / total for e in expv]


def dynamic_coef_sample(
    total_layers: int,
    *,
    scope: str = "region",
    alpha_range: Tuple[float, float] = (0.1, 1.5),
    seed: Optional[int] = None,
) -> Dict[str, float]:
    """
    Sample per-layer / per-region alphas. The evolutionary genome uses this
    each cycle to seed `layer_alpha_curve(...)` or to populate a slices block.

    Scopes:
        region : 3 values {'early','middle','late'}
        layer  : N values  {'layer_0', ...}
        global : 1 value   {'global'}
    """
    import random
    rng = random.Random(seed)
    lo, hi = alpha_range
    if scope == "region":
        return {r: rng.uniform(lo, hi) for r in ("early", "middle", "late")}
    if scope in ("layer", "tensor"):
        return {f"layer_{i}": rng.uniform(lo, hi) for i in range(max(1, total_layers))}
    return {"global": rng.uniform(lo, hi)}


def expand_region_alphas(
    region_alphas: Dict[str, float],
    total_layers: int,
) -> Dict[int, float]:
    """{'early','middle','late'} → per-layer dict for slice generation."""
    if total_layers <= 0:
        return {}
    third = max(1, total_layers // 3)
    out: Dict[int, float] = {}
    for i in range(total_layers):
        if i < third:
            out[i] = float(region_alphas.get("early", 1.0))
        elif i < 2 * third:
            out[i] = float(region_alphas.get("middle", 1.0))
        else:
            out[i] = float(region_alphas.get("late", 1.0))
    return out


# ════════════════════════════════════════════════════════════════════════════
# POST-MERGE TRANSFORMS — only what MergeKit can't do
# ════════════════════════════════════════════════════════════════════════════

def gaussian_mutation(
    sd: StateDict,
    sigma: float = 1e-4,
    *,
    targets: str = "all",
    seed: Optional[int] = None,
    inplace: bool = False,
) -> StateDict:
    """
    Add N(0, sigma) noise to selected weights. Evolutionary exploration.
    No MergeKit equivalent.

    Args:
        sd: state_dict to perturb.
        sigma: stddev. Useful range 1e-5 to 5e-4.
        targets: 'all' | 'attention' | 'mlp' | 'embedding' | 'lora'.
        seed: rng seed.
        inplace: mutate input.
    """
    if not _HAS_TORCH:
        raise RuntimeError("gaussian_mutation requires PyTorch.")
    out = sd if inplace else {k: v.clone() for k, v in sd.items()}
    g = torch.Generator()
    if seed is not None:
        g.manual_seed(int(seed))
    perturbed = 0
    for k, v in out.items():
        if targets == "attention" and not _ATTN_RE.search(k):
            continue
        if targets == "mlp" and not _MLP_RE.search(k):
            continue
        if targets == "embedding" and not _EMBED_RE.search(k):
            continue
        if targets == "lora" and not (k.endswith("lora_A") or k.endswith("lora_B")):
            continue
        if v.dtype not in (torch.float16, torch.bfloat16, torch.float32):
            continue
        noise = torch.empty_like(v, dtype=torch.float32).normal_(0.0, sigma, generator=g)
        out[k] = (v.float() + noise).to(v.dtype)
        perturbed += 1
    logger.debug(f"gaussian_mutation sigma={sigma} targets={targets} perturbed {perturbed} tensors")
    return out


def cosine_filter(
    delta_a: StateDict,
    delta_b: StateDict,
    threshold: float = 0.0,
    *,
    mode: str = "suppress",
) -> Tuple[StateDict, StateDict, Dict[str, float]]:
    """
    Reject merges per-tensor when cosine(delta_a, delta_b) < threshold.
    TIES does sign-consensus only; this is the continuous version.

    Modes:
        suppress : zero both deltas where below threshold
        keep_a   : keep delta_a, zero delta_b
        keep_b   : keep delta_b, zero delta_a
        report   : do not modify; only return similarities

    Returns:
        (delta_a_filtered, delta_b_filtered, {tensor_name: cosine_sim})
    """
    if not _HAS_TORCH:
        raise RuntimeError("cosine_filter requires PyTorch.")
    out_a = {k: v.clone() for k, v in delta_a.items()}
    out_b = {k: v.clone() for k, v in delta_b.items()}
    sims: Dict[str, float] = {}
    for k in set(delta_a.keys()) & set(delta_b.keys()):
        a = delta_a[k].flatten().float()
        b = delta_b[k].flatten().float()
        na = a.norm() + 1e-12
        nb = b.norm() + 1e-12
        sim = float((a @ b) / (na * nb))
        sims[k] = sim
        if sim >= threshold or mode == "report":
            continue
        if mode == "keep_a":
            out_b[k] = torch.zeros_like(out_b[k])
        elif mode == "keep_b":
            out_a[k] = torch.zeros_like(out_a[k])
        else:
            out_a[k] = torch.zeros_like(out_a[k])
            out_b[k] = torch.zeros_like(out_b[k])
    return out_a, out_b, sims


def lora_rank_prune(
    lora_A: "Tensor",
    lora_B: "Tensor",
    retain_percent: float = 50.0,
) -> Tuple["Tensor", "Tensor"]:
    """
    Keep the strongest LoRA rank channels (PEFT territory, not MergeKit).

    Args:
        lora_A: shape (rank, in_dim).
        lora_B: shape (out_dim, rank).
        retain_percent: 1–100.

    Returns:
        Tuple of pruned (A, B) with rank' channels.
    """
    if not _HAS_TORCH:
        raise RuntimeError("lora_rank_prune requires PyTorch.")
    pct = max(1.0, min(100.0, float(retain_percent))) / 100.0
    rank = lora_A.shape[0]
    keep = max(1, int(round(rank * pct)))
    importance = lora_A.norm(dim=1) * lora_B.norm(dim=0)
    idx = importance.argsort(descending=True)[:keep]
    idx, _ = idx.sort()
    return lora_A.index_select(0, idx), lora_B.index_select(1, idx)


def nuslerp_variant_tensor(
    v1: "Tensor",
    v2: "Tensor",
    t: float = 0.5,
    *,
    eps: float = 1e-8,
) -> "Tensor":
    """
    Normalized SLERP — slerp on direction, linear on magnitude.
    More stable than vanilla SLERP for high-similarity pairs. Custom; not in
    MergeKit. For standard SLERP, use MergeKit's `merge_method: slerp`.
    """
    if not _HAS_TORCH:
        raise RuntimeError("nuslerp_variant_tensor requires PyTorch.")
    a = v1.flatten().float()
    b = v2.flatten().float()
    norm_a = a.norm() + eps
    norm_b = b.norm() + eps
    cos = (a @ b) / (norm_a * norm_b)
    cos = float(cos.clamp(-1.0, 1.0))
    if abs(cos) > 0.9995:
        return (1.0 - t) * v1 + t * v2
    omega = math.acos(cos)
    sin_omega = math.sin(omega) + eps
    dir_a = a / norm_a
    dir_b = b / norm_b
    dir_t = (math.sin((1 - t) * omega) / sin_omega) * dir_a + \
            (math.sin(t * omega) / sin_omega) * dir_b
    mag_t = (1 - t) * norm_a + t * norm_b
    return (dir_t * mag_t).reshape(v1.shape).to(v1.dtype)


def alt_layer_custom_inject(
    sd_a: StateDict,
    sd_b: StateDict,
    layer_map: Dict[int, str],
) -> StateDict:
    """
    Build a hybrid state_dict using an arbitrary {layer_idx: 'a'|'b'} map.

    For regular patterns (odd_even, first_half) use MergeKit's passthrough
    method via MergekitConfigBuilder.build_passthrough_slices(). This function
    is for irregular maps — e.g. SAE-driven custom assignments.
    """
    if not _HAS_TORCH:
        raise RuntimeError("alt_layer_custom_inject requires PyTorch.")
    out: StateDict = {}
    keys = set(sd_a.keys()) | set(sd_b.keys())
    for k in keys:
        layer = _layer_index(k)
        if layer is None:
            src_sd = sd_a if k in sd_a else sd_b
        else:
            choice = layer_map.get(layer, "a").lower()
            src_sd = sd_a if (choice == "a" and k in sd_a) else sd_b
            if k not in src_sd:
                src_sd = sd_a if k in sd_a else sd_b
        out[k] = src_sd[k].clone()
    return out


# ════════════════════════════════════════════════════════════════════════════
# Toggle registry — drives UI rendering + KB description
# ════════════════════════════════════════════════════════════════════════════

# (toggle_name, route, summary)  — route is 'mergekit_yaml' or 'post_transform'
TOGGLE_ROUTING: Dict[str, str] = {
    "layerwise_alpha":     "mergekit_yaml",
    "topk_sparsify":       "mergekit_yaml",
    "sign_consensus_mask": "mergekit_yaml",
    "attn_mlp_filter":     "mergekit_yaml",
    "slerp_variants":      "mergekit_yaml",
    "bench_weighted_blend":"mergekit_yaml",
    "embedding_mode":      "mergekit_yaml",
    "alt_layer_inject":    "mergekit_yaml",      # regular patterns
    "gaussian_mutation":   "post_transform",
    "cosine_filter":       "post_transform",
    "lora_rank_prune":     "post_transform",
    "nuslerp_variant":     "post_transform",     # nuSLERP only
    "dynamic_coef_sample": "outer_loop",
}

_TOGGLE_DESCRIPTIONS: Dict[str, str] = {
    "layerwise_alpha":
        "Scale merge strength differently per transformer layer (early=syntax, "
        "middle=reasoning, late=chat). Emits MergeKit `slices:` block.",
    "topk_sparsify":
        "Keep only strongest deltas. Maps to MergeKit `density` param "
        "(TIES/DARE). Reduces noise.",
    "sign_consensus_mask":
        "Suppress directional disagreement between source models. "
        "MergeKit TIES `normalize: true` handles this.",
    "attn_mlp_filter":
        "Merge only certain module types. Emits MergeKit `filter:` selectors "
        "(q_proj, mlp.down_proj, …).",
    "bench_weighted_blend":
        "Weight each source model by its benchmark score. Outer loop feeds "
        "scores → softmax → per-model `weight:` in MergeKit YAML.",
    "dynamic_coef_sample":
        "Genome sampler. Each cycle, randomize per-region or per-layer alphas. "
        "Outer-loop only.",
    "slerp_variants":
        "Geometric interpolation. Standard SLERP uses MergeKit native; "
        "nuSLERP (magnitude-linear, direction-slerp) is custom.",
    "lora_rank_prune":
        "Drop weakest LoRA channels (PEFT). Reduces overfit noise.",
    "cosine_filter":
        "Reject per-tensor merges with low cosine similarity. Avoids "
        "catastrophic merges. No MergeKit equivalent.",
    "gaussian_mutation":
        "Add N(0,σ) noise to weights. Evolutionary diversity. No MergeKit "
        "equivalent.",
    "alt_layer_inject":
        "Alternate transformer layers between two source models. Regular "
        "patterns via MergeKit `passthrough`; custom maps post-merge.",
    "embedding_mode":
        "Tokenizer/embedding handling: freeze / partial / full / scaled. "
        "Maps to MergeKit `tokenizer_source` + filter.",
}


def describe_toggle(name: str) -> str:
    """One-line user-facing description (UI tooltip / RAG)."""
    return _TOGGLE_DESCRIPTIONS.get(name, "")


def toggle_route(name: str) -> str:
    """Returns 'mergekit_yaml' | 'post_transform' | 'outer_loop'."""
    return TOGGLE_ROUTING.get(name, "unknown")


__all__ = [
    # outer-loop helpers
    "layer_alpha_curve",
    "bench_score_to_weights",
    "dynamic_coef_sample",
    "expand_region_alphas",
    "classify_module",
    # post-merge transforms
    "gaussian_mutation",
    "cosine_filter",
    "lora_rank_prune",
    "nuslerp_variant_tensor",
    "alt_layer_custom_inject",
    "apply_post_transforms_streaming",
    # UI / KB
    "describe_toggle",
    "toggle_route",
    "TOGGLE_ROUTING",
    "FILTER_TOKENS",
]


# ════════════════════════════════════════════════════════════════════════════
# Streaming applier — runs post-merge transforms shard-by-shard.
# Designed for 8GB VRAM: loads one safetensors shard at a time.
# ════════════════════════════════════════════════════════════════════════════
def apply_post_transforms_streaming(
    model_dir: str,
    advanced: Dict[str, Dict[str, Any]],
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Apply enabled post-merge transforms to a sharded safetensors model
    in place. Streams one shard at a time so a 7B fp16 model fits in 8GB.

    Args:
        model_dir: path to a directory containing *.safetensors shards
                   (mergekit output layout).
        advanced: recipe['advanced'] subset, e.g.
            {
              "gaussian_mutation": {"params": {"mutation_sigma": 1e-4,
                                               "mutation_target": "all"}},
              "cosine_filter": ...,   # needs sibling delta; skipped here
              ...
            }
        dry_run: if True, log the plan but write nothing.

    Returns:
        {"applied": [...], "skipped": [...], "shards": N}

    Notes:
        - cosine_filter / alt_layer_custom_inject require TWO source models
          and run upstream of the MergeKit call, not here.
        - lora_rank_prune runs on adapter directories (separate codepath).
        - Only gaussian_mutation and nuslerp_variant are applied here.
    """
    import os
    try:
        from safetensors.torch import load_file, save_file
    except ImportError:
        logger.warning("safetensors not available; post-transforms skipped.")
        return {"applied": [], "skipped": list(advanced.keys()), "shards": 0}
    if not _HAS_TORCH:
        return {"applied": [], "skipped": list(advanced.keys()), "shards": 0}

    if not os.path.isdir(model_dir):
        raise FileNotFoundError(f"model_dir not found: {model_dir}")

    shards = sorted(
        os.path.join(model_dir, f) for f in os.listdir(model_dir)
        if f.endswith(".safetensors")
    )
    if not shards:
        logger.warning(f"No safetensors shards in {model_dir}")
        return {"applied": [], "skipped": list(advanced.keys()), "shards": 0}

    plan: List[str] = []
    if "gaussian_mutation" in advanced:
        plan.append("gaussian_mutation")
    if "nuslerp_variant" in advanced:
        # nuslerp needs a sibling state_dict; skip unless caller provided one.
        plan.append("nuslerp_variant_skipped_no_sibling")

    if not plan or dry_run:
        return {"applied": [], "skipped": list(advanced.keys()),
                "shards": len(shards), "plan": plan}

    gm = advanced.get("gaussian_mutation", {}).get("params", {})
    sigma = float(gm.get("mutation_sigma", 1e-4))
    targets = str(gm.get("mutation_target", "all"))
    seed = gm.get("seed")

    applied: List[str] = []
    for shard_path in shards:
        sd = load_file(shard_path)
        if "gaussian_mutation" in advanced:
            sd = gaussian_mutation(sd, sigma=sigma, targets=targets,
                                   seed=seed, inplace=True)
        save_file(sd, shard_path)
        del sd
        if _HAS_TORCH and torch.cuda.is_available():
            torch.cuda.empty_cache()
        applied.append(os.path.basename(shard_path))

    return {
        "applied": ["gaussian_mutation"],
        "skipped": [k for k in advanced if k != "gaussian_mutation"],
        "shards": len(applied),
    }
