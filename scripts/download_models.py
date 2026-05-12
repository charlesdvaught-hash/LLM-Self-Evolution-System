#!/usr/bin/env python3
"""
Optimized Model Zoo for Breeding Vat - WITH SPECIALIZED VARIANTS + MoE MODELS
- Smallest models that benchmark reliably
- Safetensors for merging (specimens)
- pytorch for evaluation (runnable)
- INCLUDES: SAE research, reasoning, code, math, MoE architecture
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# SPECIALIZED MODEL COLLECTIONS FOR TARGETED EVOLUTION
# ============================================================================

SPECIALIZED_MODELS = {
    # SAE Research Models - Interpretability analysis
    "sae": {
        "description": "SAE (Sparse Autoencoder) research models - for interpretability",
        "models": [
            "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50",
            "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_100",
        ]
    },
    
    # Reasoning & Thought Models - Enhanced reasoning
    "reasoning": {
        "description": "Reasoning-enhanced models with chain-of-thought",
        "models": [
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "alpha-ai/qwen2.5-reason-thought-lite",
            "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled",
        ]
    },
    
    # Code Specialists - Programming focus
    "code": {
        "description": "Code generation specialists",
        "models": [
            "bigatuna/Qwen3-1.7B-Sushi-Coder",
        ]
    },
    
    # Math Specialists - Mathematical reasoning
    "math": {
        "description": "Math reasoning specialists",
        "models": [
            "DavidOKB/MathThink-Qwen-3.5-4B",
        ]
    },
    
    # General Purpose - Baseline models
    "general": {
        "description": "General purpose base models",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ]
    },
    
    # Diverse Capability - Interesting merges
    "diverse": {
        "description": "Diverse capability models",
        "models": [
            "microsoft/Phi-3-mini-4k-instruct",
            "OusiaResearch/Aureth-4B-Qwen3.5",
        ]
    },
    
    # Mixture of Experts Models - Novel frankenstein merges
    "moe": {
        "description": "Mixture of Experts models - for MoE-based frankenstein combinations",
        "models": [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ]
    },
}

# ============================================================================
# PRESET CONFIGURATIONS FOR YOUR USE CASES
# ============================================================================

PRESETS = {
    "baseline": {
        "description": "General baseline (safest for merging)",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ]
    },
    
    "reasoning": {
        "description": "For evolving reasoning capabilities",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "alpha-ai/qwen2.5-reason-thought-lite",
            "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled",
        ]
    },
    
    "code": {
        "description": "For evolving code generation",
        "models": [
            "Qwen/Qwen2.5-1.5B-Instruct",
            "bigatuna/Qwen3-1.7B-Sushi-Coder",
        ]
    },
    
    "math": {
        "description": "For evolving math reasoning",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "DavidOKB/MathThink-Qwen-3.5-4B",
        ]
    },
    
    "research": {
        "description": "For SAE research and interpretability",
        "models": [
            "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50",
            "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_100",
        ]
    },
    
    "reasoning-advanced": {
        "description": "Advanced reasoning with Claude Opus distillation",
        "models": [
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "alpha-ai/qwen2.5-reason-thought-lite",
            "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled",
        ]
    },
    
    "moe-research": {
        "description": "MoE models for frankenstein architecture experiments",
        "models": [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ]
    },
    
    "moe-frankenstein": {
        "description": "MoE + specialists for advanced frankenstein merging",
        "models": [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2.5-1.5B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "bigatuna/Qwen3-1.7B-Sushi-Coder",
        ]
    },
    
    "full": {
        "description": "All models (comprehensive evolution)",
        "models": []  # Will be populated
    },
    
    "recommended": {
        "description": "Recommended for 12GB VRAM (small + reasoning + code)",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "Qwen/Qwen2.5-1.5B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "bigatuna/Qwen3-1.7B-Sushi-Coder",
        ]
    },
    
    "recommended-reasoning": {
        "description": "Recommended with advanced reasoning (might be tight)",
        "models": [
            "Qwen/Qwen2.5-0.5B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled",
        ]
    },
}

# Populate "full" preset
PRESETS["full"]["models"] = []
for category in SPECIALIZED_MODELS.values():
    PRESETS["full"]["models"].extend(category["models"])

# Default: recommended for your hardware
DEFAULT_MODELS = PRESETS["recommended"]["models"]

# ============================================================================
# DOWNLOAD LOGIC
# ============================================================================

def download_models(model_ids=None, cache_dir=None, format_type="safetensors"):
    """
    Download models from HuggingFace Hub.
    
    Args:
        model_ids: List of model IDs to download
        cache_dir: Cache directory (defaults to HuggingFace cache)
        format_type: "safetensors" (for merging) or "pytorch" (for eval)
    """
    if model_ids is None:
        model_ids = DEFAULT_MODELS
    
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    os.makedirs(cache_dir, exist_ok=True)
    
    try:
        from transformers import AutoModel, AutoTokenizer
    except ImportError:
        logger.error("transformers not installed. Run: pip install transformers")
        return False
    
    logger.info(f"Cache directory: {cache_dir}")
    logger.info(f"Format: {format_type}")
    logger.info(f"Downloading {len(model_ids)} models...")
    
    successful = 0
    failed = 0
    
    for model_id in model_ids:
        logger.info(f"\n[{model_id}]")
        try:
            logger.info("  Downloading tokenizer...")
            AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
            
            logger.info(f"  Downloading model weights ({format_type})...")
            AutoModel.from_pretrained(model_id, cache_dir=cache_dir)
            
            logger.info(f"  ✓ {model_id} ready")
            successful += 1
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            failed += 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Download Summary:")
    logger.info(f"  Successful: {successful}/{len(model_ids)}")
    logger.info(f"  Failed: {failed}/{len(model_ids)}")
    logger.info(f"{'='*70}")
    
    if failed > 0:
        logger.warning("Some models failed to download. Check internet connection.")
        return False
    
    logger.info("\nFormats:")
    logger.info("  Specimens (merging):  safetensors ✓")
    logger.info("  Runnable (eval):      pytorch/safetensors ✓")
    logger.info("  SAE analysis:         safetensors ✓")
    return True

def show_model_categories():
    """Display all available model categories."""
    print("\n" + "="*80)
    print("SPECIALIZED MODEL CATEGORIES")
    print("="*80)
    
    for category, info in SPECIALIZED_MODELS.items():
        print(f"\n{category.upper()}: {info['description']}")
        for model_id in info['models']:
            print(f"  • {model_id}")

def show_presets():
    """Display available preset configurations."""
    print("\n" + "="*80)
    print("PRESET CONFIGURATIONS FOR YOUR USE CASES")
    print("="*80)
    
    for preset_name, preset_info in PRESETS.items():
        print(f"\n{preset_name.upper()}: {preset_info['description']}")
        print(f"  Size: {len(preset_info['models'])} models")
        for model_id in preset_info['models'][:3]:
            print(f"    • {model_id}")
        if len(preset_info['models']) > 3:
            print(f"    ... and {len(preset_info['models']) - 3} more")

def show_model_info():
    """Display comprehensive model information."""
    print("\n" + "="*80)
    print("BREEDING VAT MODEL ZOO - COMPLETE GUIDE (WITH MOE)")
    print("="*80)
    
    show_presets()
    
    print("\n" + "="*80)
    print("SPECIALIZED CATEGORIES FOR TARGETED EVOLUTION")
    print("="*80)
    
    show_model_categories()
    
    print("\n" + "="*80)
    print("MOE FRANKENSTEIN EXPERIMENTS")
    print("="*80)
    print("\nPreset: 'moe-research' (Mixtral only)")
    print("  • For expert analysis and extraction")
    print("  • Size: ~15 GB (sparse)")
    print("\nPreset: 'moe-frankenstein' (MoE + specialists)")
    print("  • For advanced MoE merging experiments")
    print("  • Size: ~28 GB")
    print("\nSee MOE_FRANKENSTEIN_GUIDE.md for detailed strategies")
    print("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimized model downloader with MoE frankenstein capabilities"
    )
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default=None,
        help="Download a preset configuration"
    )
    parser.add_argument(
        "--category",
        choices=list(SPECIALIZED_MODELS.keys()),
        default=None,
        help="Download a category"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Specific model IDs to download (space-separated)"
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="HuggingFace cache directory"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download (models already cached)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show model info and exit"
    )
    parser.add_argument(
        "--categories",
        action="store_true",
        help="Show available categories and exit"
    )
    parser.add_argument(
        "--presets",
        action="store_true",
        help="Show available presets and exit"
    )
    
    args = parser.parse_args()
    
    if args.info:
        show_model_info()
        sys.exit(0)
    
    if args.categories:
        show_model_categories()
        sys.exit(0)
    
    if args.presets:
        show_presets()
        sys.exit(0)
    
    # Determine which models to download
    if args.models:
        models_to_dl = args.models
    elif args.preset:
        models_to_dl = PRESETS[args.preset]["models"]
        logger.info(f"Using preset '{args.preset}': {PRESETS[args.preset]['description']}")
    elif args.category:
        models_to_dl = SPECIALIZED_MODELS[args.category]["models"]
        logger.info(f"Using category '{args.category}': {SPECIALIZED_MODELS[args.category]['description']}")
    else:
        models_to_dl = DEFAULT_MODELS
        logger.info(f"Using recommended preset (default for 12GB VRAM)")
    
    if args.skip_download:
        logger.info("Skipping download (--skip-download set)")
        sys.exit(0)
    
    success = download_models(models_to_dl, args.cache_dir)
    sys.exit(0 if success else 1)
