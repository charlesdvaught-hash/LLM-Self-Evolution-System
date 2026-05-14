#!/usr/bin/env python3
"""
Model Zoo downloader for The Breeding Vat.

Two download paths:
  - HF repos (safetensors)  -> AutoModelForCausalLM.from_pretrained into HF cache
  - GGUF repos              -> hf_hub_download of best quant into model_zoo/<name>/

GGUF selection priority: Q4_K_M > Q4_K_S > Q5_K_M > Q4_0 > first .gguf found
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ZOO_DIR = "breeding_vat/data/model_zoo"

# Preferred quantisation order for GGUF repos
GGUF_QUANT_PRIORITY = [
    "Q4_K_M", "Q4_K_S", "Q5_K_M", "Q5_K_S", "Q4_0", "Q8_0",
]

# ============================================================================
# MODEL CATALOGUE
# Each entry is either:
#   {"hf":   "org/repo"}               - full HF safetensors repo
#   {"gguf": "org/repo",               - GGUF repo, auto-picks best quant
#    "zoo_name": "local-folder-name"}
# ============================================================================

SPECIALIZED_MODELS = {
    "advisor": {
        "description": "Advisor + KB retriever models",
        "models": [
            # Quick advisor: 0.8B GGUF, Claude 4.6 Opus CoT distilled
            {"gguf": "Jackrong/Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled-GGUF",
             "zoo_name": "Qwen3.5-0.8B-Reasoning-GGUF"},
            # LaSER KB retriever: 0.6B safetensors, CPU-friendly
            {"hf": "Alibaba-NLP/LaSER-Qwen3-0.6B",
             "zoo_name": "LaSER-Qwen3-0.6B"},
        ]
    },

    "sae": {
        "description": "SCOPE / SAE analysis models",
        "models": [
            {"hf": "Machine981/SCOPE-Deepseek-R1-Distill-Qwen-1.5B",
             "zoo_name": "SCOPE-Deepseek-R1-Distill-Qwen-1.5B"},
        ]
    },

    "reasoning": {
        "description": "Reasoning specimen models for merging",
        "models": [
            {"hf": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"},
            {"hf": "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled"},
        ]
    },

    "code": {
        "description": "Code generation specimen models",
        "models": [
            {"hf": "bigatuna/Qwen3-1.7B-Sushi-Coder"},
        ]
    },

    "general": {
        "description": "General purpose baseline specimens",
        "models": [
            {"hf": "Qwen/Qwen2.5-0.5B-Instruct"},
            {"hf": "Qwen/Qwen2.5-1.5B-Instruct"},
        ]
    },
}

# ============================================================================
# PRESETS
# ============================================================================

PRESETS = {
    "recommended": {
        "description": "RTX 5070 / 12GB VRAM — advisor + middle-size QA + core specimens",
        "models": [
            # Utility
            {"gguf": "Jackrong/Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled-GGUF",
             "zoo_name": "Qwen3.5-0.8B-Reasoning-GGUF"},
            {"hf": "Alibaba-NLP/LaSER-Qwen3-0.6B",
             "zoo_name": "LaSER-Qwen3-0.6B"},
            # Assistant (3B quantized)
            {"gguf": "InduwaraR/qwen-ai-research-qa-q4_k_m.gguf",
             "zoo_name": "Qwen-AI-Research-QA-3B"},
            # Specimens
            {"hf": "Qwen/Qwen2.5-1.5B-Instruct"},
            {"hf": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"},
            {"hf": "bigatuna/Qwen3-1.7B-Sushi-Coder"},
        ]
    },

    "baseline": {
        "description": "Minimal — two base specimens only",
        "models": [
            {"hf": "Qwen/Qwen2.5-0.5B-Instruct"},
            {"hf": "Qwen/Qwen2.5-1.5B-Instruct"},
        ]
    },

    "advisors-only": {
        "description": "Utility models only — no merge specimens",
        "models": [
            {"gguf": "Jackrong/Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled-GGUF",
             "zoo_name": "Qwen3.5-0.8B-Reasoning-GGUF"},
            {"hf": "Alibaba-NLP/LaSER-Qwen3-0.6B",
             "zoo_name": "LaSER-Qwen3-0.6B"},
            {"gguf": "InduwaraR/qwen-ai-research-qa-q4_k_m.gguf",
             "zoo_name": "Qwen-AI-Research-QA-3B"},
        ]
    },

    "reasoning": {
        "description": "Reasoning-focused specimens",
        "models": [
            {"hf": "Qwen/Qwen2.5-1.5B-Instruct"},
            {"hf": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"},
            {"hf": "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled"},
        ]
    },
}

PRESETS["full"] = {
    "description": "All models",
    "models": [m for cat in SPECIALIZED_MODELS.values() for m in cat["models"]]
}

DEFAULT_MODELS = PRESETS["recommended"]["models"]

# ============================================================================
# DOWNLOAD HELPERS
# ============================================================================

def _pick_gguf_file(repo_id: str) -> str:
    """
    List files in a GGUF repo and return the filename of the best quant.
    Priority: Q4_K_M > Q4_K_S > Q5_K_M > ... > first .gguf found.
    """
    try:
        from huggingface_hub import list_repo_files
        files = [f for f in list_repo_files(repo_id) if f.endswith(".gguf")]
    except Exception as e:
        raise RuntimeError(f"Could not list files in {repo_id}: {e}")

    if not files:
        raise RuntimeError(f"No .gguf files found in {repo_id}")

    for quant in GGUF_QUANT_PRIORITY:
        for f in files:
            if quant.lower() in f.lower():
                logger.info(f"  Selected quant: {f}")
                return f

    # fallback: smallest file
    logger.warning(f"  No preferred quant found, using first: {files[0]}")
    return files[0]


def _download_gguf(entry: dict) -> bool:
    repo_id  = entry["gguf"]
    zoo_name = entry.get("zoo_name", repo_id.split("/")[-1])
    dest_dir = os.path.join(ZOO_DIR, zoo_name)

    try:
        filename = _pick_gguf_file(repo_id)
    except Exception as e:
        logger.error(f"  {e}")
        return False

    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        logger.info(f"  Already present: {dest_path}")
        return True

    os.makedirs(dest_dir, exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
        logger.info(f"  Downloading {filename} ...")
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=dest_dir)
        logger.info(f"  Saved to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"  Download failed: {e}")
        return False


def _download_hf(entry: dict, cache_dir: str) -> bool:
    model_id = entry["hf"]
    zoo_name = entry.get("zoo_name", model_id.split("/")[-1])
    target   = os.path.join(ZOO_DIR, zoo_name)

    # Skip if safetensors already present
    if os.path.isdir(target):
        if list(Path(target).glob("*.safetensors")):
            logger.info(f"  Already present: {target}")
            return True

    os.makedirs(target, exist_ok=True)
    try:
        from huggingface_hub import snapshot_download
        logger.info(f"  Downloading {model_id} -> {target} ...")
        snapshot_download(
            repo_id=model_id,
            local_dir=target,
            ignore_patterns=["*.pt", "*.bin", "*.gguf", "*.ot"],  # safetensors only
        )
        logger.info(f"  Done: {target}")
        return True
    except Exception as e:
        logger.error(f"  Failed: {e}")
        return False


def download_models(model_entries=None, cache_dir=None):
    if model_entries is None:
        model_entries = DEFAULT_MODELS
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")

    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(ZOO_DIR, exist_ok=True)

    # Normalise legacy plain strings
    entries = [{"hf": e} if isinstance(e, str) else e for e in model_entries]

    successful, failed = 0, 0
    for entry in entries:
        label = entry.get("gguf") or entry.get("hf", "?")
        logger.info(f"\n[{label}]")
        ok = _download_gguf(entry) if "gguf" in entry else _download_hf(entry, cache_dir)
        if ok:
            successful += 1
        else:
            failed += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"Downloaded: {successful}/{len(entries)}   Failed: {failed}")
    logger.info(f"{'='*60}")
    return failed == 0


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Breeding Vat model downloader")
    parser.add_argument("--preset",   choices=list(PRESETS.keys()), default=None)
    parser.add_argument("--category", choices=list(SPECIALIZED_MODELS.keys()), default=None)
    parser.add_argument("--models",   nargs="+", default=None,
                        help="Explicit HF IDs (safetensors, space-separated)")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--info", action="store_true",
                        help="List all presets and exit")
    args = parser.parse_args()

    if args.info:
        for name, p in PRESETS.items():
            print(f"\n{name}: {p['description']}")
            for m in p["models"]:
                label = m.get("gguf") or m.get("hf", "?")
                fmt   = "GGUF" if "gguf" in m else "safetensors"
                print(f"  [{fmt}] {label}")
        sys.exit(0)

    if args.skip_download:
        logger.info("Skipping download (--skip-download)")
        sys.exit(0)

    if args.models:
        entries = [{"hf": m} for m in args.models]
    elif args.preset:
        entries = PRESETS[args.preset]["models"]
        logger.info(f"Preset '{args.preset}': {PRESETS[args.preset]['description']}")
    elif args.category:
        entries = SPECIALIZED_MODELS[args.category]["models"]
    else:
        entries = DEFAULT_MODELS
        logger.info("Using recommended preset (RTX 5070 / 12GB VRAM)")

    success = download_models(entries, args.cache_dir)
    sys.exit(0 if success else 1)
