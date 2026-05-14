"""
Recipe Executor: Parse and execute a breeding vat evolutionary recipe.

A recipe is a JSON config that specifies:
- Base models, merge methods, cycles, culling
- Fine-tuning strategy (method, dataset, target layers)
- ASSAY measurement points
- SAE analysis triggers
- AI guidance settings

The executor takes a recipe dict and configures the evolution pipeline,
then returns the execution context for the UI or CLI to run.

This is the master template that both advisor and pipeline understand.
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecipeValidationResult:
    """Result of validating a recipe against the schema."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    recipe: Optional[Dict[str, Any]] = None


class RecipeExecutor:
    """
    Parses and executes a breeding vat recipe.
    
    Usage:
        executor = RecipeExecutor()
        recipe = executor.load_recipe("reasoning_fusion_v1")
        validation = executor.validate(recipe)
        
        if validation.valid:
            config = executor.build_evolution_config(recipe)
            # Pass config to EvolutionEngine
    """
    
    TEMPLATE_PATH = "breeding_vat/data/templates/RECIPE_TEMPLATE.json"
    RECIPES_DIR = "breeding_vat/data/recipes"
    
    def __init__(self):
        os.makedirs(self.RECIPES_DIR, exist_ok=True)
    
    def load_template(self) -> Dict[str, Any]:
        """Load the canonical recipe template from disk."""
        if not os.path.exists(self.TEMPLATE_PATH):
            raise FileNotFoundError(f"Recipe template not found: {self.TEMPLATE_PATH}")
        
        with open(self.TEMPLATE_PATH, 'r') as f:
            return json.load(f)
    
    def load_recipe(self, recipe_name: str) -> Dict[str, Any]:
        """Load a saved recipe by name."""
        recipe_path = os.path.join(self.RECIPES_DIR, f"{recipe_name}.json")
        
        if not os.path.exists(recipe_path):
            raise FileNotFoundError(f"Recipe not found: {recipe_path}")
        
        with open(recipe_path, 'r') as f:
            return json.load(f)
    
    def save_recipe(self, recipe: Dict[str, Any], recipe_name: str = None) -> str:
        """Save a recipe to disk. Returns path."""
        name = recipe_name or recipe.get("metadata", {}).get("name", "untitled")
        recipe_path = os.path.join(self.RECIPES_DIR, f"{name}.json")
        
        with open(recipe_path, 'w') as f:
            json.dump(recipe, f, indent=2, default=str)
        
        logger.info(f"Saved recipe: {recipe_path}")
        return recipe_path
    
    def list_recipes(self) -> List[str]:
        """List all saved recipes."""
        if not os.path.isdir(self.RECIPES_DIR):
            return []
        
        recipes = [f.replace(".json", "") for f in os.listdir(self.RECIPES_DIR) if f.endswith(".json")]
        return sorted(recipes)
    
    def validate(self, recipe: Dict[str, Any]) -> RecipeValidationResult:
        """
        Validate a recipe against the schema.
        
        Returns:
            RecipeValidationResult with valid=True/False, errors, warnings
        """
        errors = []
        warnings = []
        
        try:
            template = self.load_template()
        except FileNotFoundError as e:
            return RecipeValidationResult(valid=False, errors=[str(e)], warnings=[])
        
        # Check required top-level keys
        required_keys = ["metadata", "evolution", "evaluation"]
        for key in required_keys:
            if key not in recipe:
                errors.append(f"Missing required key: {key}")
        
        # Validate evolution config
        if "evolution" in recipe:
            evo = recipe["evolution"]
            
            if not evo.get("base_models") or len(evo["base_models"]) < 2:
                errors.append("evolution.base_models: need 2+ models")
            
            if not evo.get("merge_methods"):
                errors.append("evolution.merge_methods: need at least one method")
            
            num_cycles = evo.get("num_cycles", 0)
            if num_cycles < 1 or num_cycles > 100:
                errors.append(f"evolution.num_cycles: must be 1-100 (got {num_cycles})")
            
            culling = evo.get("culling_rate", 50)
            if culling < 0 or culling > 100:
                errors.append(f"evolution.culling_rate: must be 0-100 (got {culling})")
        
        # Validate fine-tuning config (if enabled)
        if recipe.get("finetuning", {}).get("enabled"):
            ft = recipe["finetuning"]
            
            if ft.get("method") not in ["lora", "qlora", "full", "ia3"]:
                warnings.append(f"finetuning.method: unknown method '{ft.get('method')}'")
            
            if ft.get("num_epochs", 0) < 1 or ft.get("num_epochs") > 100:
                warnings.append(f"finetuning.num_epochs: reasonable range is 1-20 (got {ft.get('num_epochs')})")
        
        # Validate ASSAY config (if enabled)
        if recipe.get("assay", {}).get("enabled"):
            assay = recipe["assay"]
            
            if not assay.get("topic"):
                errors.append("assay.topic: required when assay is enabled")
        
        # Validate SAE config (if enabled)
        if recipe.get("sae", {}).get("enabled"):
            sae = recipe["sae"]
            
            vram = sae.get("vram_gb", 0)
            if vram < 4 or vram > 96:
                warnings.append(f"sae.vram_gb: unusual value {vram}")
        
        valid = len(errors) == 0
        return RecipeValidationResult(valid=valid, errors=errors, warnings=warnings, recipe=recipe)
    
    def build_evolution_config(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a recipe into EvolutionEngine config.
        
        Returns:
            {
                "base_models": [...],
                "num_cycles": 5,
                "culling_rate": 50,
                "merge_methods": ["slerp", "ties", ...],
                "method_params": {
                    "ties": {"threshold": 0.9},
                    ...
                },
                "eval_tier": "standard",
                "skip_perplexity": False,
                ...
            }
        """
        evo = recipe["evolution"]
        eval_config = recipe.get("evaluation", {})
        
        # Extract method parameters
        method_params = {}
        for method, config in evo.get("merge_methods", {}).items():
            if config.get("enabled"):
                params = {k: v for k, v in config.items() if k not in ["enabled", "weight"]}
                if params:
                    method_params[method] = params
        
        config = {
            "base_models": evo["base_models"],
            "num_cycles": evo.get("num_cycles", 3),
            "culling_rate": evo.get("culling_rate", 50),
            "merge_methods": [m for m, c in evo.get("merge_methods", {}).items() if c.get("enabled")],
            "method_params": method_params,
            "eval_tier": eval_config.get("tier", "standard"),
            "skip_perplexity": eval_config.get("skip_perplexity", False),
            "scope_prefilter": eval_config.get("scope_prefilter", False),
            # Advanced orthogonal toggles (opt-in). Engine reads enabled keys only.
            "advanced": self.build_advanced_config(recipe),
        }

        return config

    def build_advanced_config(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract recipe['advanced'] into a compact engine-side dict.

        Returns:
            {
              "<toggle_name>": {"params": {...}, "mutate": bool},
              ...
            }
        Only toggles with enabled=True appear. Mutate flag is preserved
        so the evolution genome can pick them up.
        """
        adv = recipe.get("advanced", {}) or {}
        out: Dict[str, Any] = {}
        for name, cfg in adv.items():
            if not isinstance(cfg, dict) or not cfg.get("enabled"):
                continue
            out[name] = {
                "params": dict(cfg.get("params", {}) or {}),
                "mutate": bool(cfg.get("mutate", False)),
            }
        return out
    
    def build_finetuning_config(self, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert recipe fine-tuning section into trainer config.
        
        Returns None if fine-tuning is disabled.
        """
        ft = recipe.get("finetuning", {})
        
        if not ft.get("enabled"):
            return None
        
        config = {
            "method": ft.get("method", "lora"),
            "dataset": ft.get("dataset", "synthetic_qa"),
            "target_layers": ft.get("target_layers"),
            "num_epochs": ft.get("num_epochs", 3),
            "batch_size": ft.get("batch_size", 4),
            "learning_rate": ft.get("learning_rate", 1e-4),
            "lora_rank": ft.get("lora_rank", 8),
            "lora_alpha": ft.get("lora_alpha", 16),
            "per_cycle": ft.get("per_cycle", False),
            "apply_to": ft.get("apply_to", "best_model"),
        }
        
        return config
    
    def build_assay_config(self, recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert recipe ASSAY section into analyzer config.
        
        Returns None if ASSAY is disabled.
        """
        assay = recipe.get("assay", {})
        
        if not assay.get("enabled"):
            return None
        
        config = {
            "topic": assay.get("topic"),
            "n_mini": assay.get("n_mini", 12),
            "n_full": assay.get("n_full", 50),
            "run_after_cycles": assay.get("run_after_cycles", []),
            "use_results_for_frankenmerge": assay.get("use_results_for_frankenmerge", False),
            "use_results_for_finetuning": assay.get("use_results_for_finetuning", False),
        }
        
        return config
    
    def merge_recipe(self, base_recipe: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge a base recipe with user overrides.
        
        Deep merge, so you can override just specific fields without losing others.
        """
        import copy
        result = copy.deepcopy(base_recipe)
        
        def deep_merge(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
        
        deep_merge(result, overrides)
        return result
    
    def describe(self, recipe: Dict[str, Any]) -> str:
        """Human-readable summary of a recipe."""
        evo = recipe.get("evolution", {})
        ft = recipe.get("finetuning", {})
        assay = recipe.get("assay", {})
        sae = recipe.get("sae", {})
        
        lines = [
            f"📋 Recipe: {recipe.get('metadata', {}).get('name', 'untitled')}",
            f"   {recipe.get('metadata', {}).get('description', '')}",
            "",
            "🔧 Evolution:",
            f"   Base models: {len(evo.get('base_models', []))} ({', '.join([m.split('/')[-1] for m in evo.get('base_models', [])[:2]])}...)",
            f"   Methods: {len([m for m, c in evo.get('merge_methods', {}).items() if c.get('enabled')])} enabled",
            f"   Cycles: {evo.get('num_cycles', 0)}, Culling: {evo.get('culling_rate', 50)}%",
            "",
        ]
        
        if ft.get("enabled"):
            lines.extend([
                "🎯 Fine-tuning:",
                f"   Method: {ft.get('method')}, Per-cycle: {ft.get('per_cycle', False)}",
                f"   Epochs: {ft.get('num_epochs', 3)}, LoRA rank: {ft.get('lora_rank', 8)}",
                "",
            ])
        
        if assay.get("enabled"):
            lines.extend([
                "⚗️ ASSAY:",
                f"   Topic: {assay.get('topic')}, Runs after cycles: {assay.get('run_after_cycles', [])}",
                "",
            ])
        
        if sae.get("enabled"):
            lines.extend([
                "🧠 SAE:",
                f"   Samples: {sae.get('num_samples', 30)}, VRAM: {sae.get('vram_gb', 12)}GB",
                "",
            ])
        
        return "\n".join(lines)
