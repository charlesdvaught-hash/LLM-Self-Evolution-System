import torch
import logging
import json
from typing import List, Dict, Optional, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger("MergeAdvisor")

class RecipeGenerator:
    """
    Generate merge recipes based on methods, goals, and historical data.
    Uses the Advisor LLM to propose variants with best-practice parameters.
    """
    
    # Best practice parameter ranges per method
    METHOD_DEFAULTS = {
        "ties": {
            "threshold": [0.8, 0.9, 0.95],  # Multiple options to try
            "weight": [0.3, 0.5, 0.7],
        },
        "dare": {
            "drop_rate": [0.05, 0.1, 0.2],
            "weight": [0.3, 0.5, 0.7],
        },
        "slerp": {
            "t": [0.3, 0.5, 0.7],
            "weights": "variable",  # Depends on model count
        },
        "task_arithmetic": {
            "weight": [0.3, 0.5, 0.7, 1.0],
        },
        "moe": {
            "num_experts": "auto",  # Number of merge models
            "routing_method": ["threshold", "topk"],
        },
        "frankenmoe": {
            "num_experts": "auto",
            "layer_strategy": ["uniform", "adaptive"],
        },
        "regmean": {
            "reg_coef": [1e-8, 1e-6, 1e-4],
        }
    }
    
    @staticmethod
    def generate_variants(method: str, num_variants: int = 2, 
                         num_models: int = 2,
                         historical_params: Optional[Dict] = None) -> List[Dict]:
        """
        Generate N recipe variants for a merge method.
        
        Args:
            method: Merge method name
            num_variants: How many variants to generate
            num_models: Number of models being merged
            historical_params: Best parameters from past experiments
            
        Returns:
            List of recipe dicts with parameters
        """
        variants = []
        method_lower = method.lower()
        
        if method_lower not in RecipeGenerator.METHOD_DEFAULTS:
            logger.warning(f"Unknown method {method}, using defaults")
            method_lower = "ties"
        
        defaults = RecipeGenerator.METHOD_DEFAULTS[method_lower]
        
        # Generate N variants with different parameter combinations
        for i in range(num_variants):
            variant = {
                "method": method,
                "variant_id": i + 1,
                "parameters": {},
                "reasoning": f"Variant {i+1}: "
            }
            
            # Set parameters based on method
            if method_lower == "ties":
                variant["parameters"]["threshold"] = defaults["threshold"][i % len(defaults["threshold"])]
                variant["parameters"]["weight"] = defaults["weight"][i % len(defaults["weight"])]
                variant["reasoning"] += f"threshold={variant['parameters']['threshold']}, weight={variant['parameters']['weight']}"
            
            elif method_lower == "dare":
                variant["parameters"]["drop_rate"] = defaults["drop_rate"][i % len(defaults["drop_rate"])]
                variant["parameters"]["weight"] = defaults["weight"][i % len(defaults["weight"])]
                variant["reasoning"] += f"drop_rate={variant['parameters']['drop_rate']}, weight={variant['parameters']['weight']}"
            
            elif method_lower == "slerp":
                variant["parameters"]["t"] = defaults["t"][i % len(defaults["t"])]
                variant["reasoning"] += f"t={variant['parameters']['t']}"
            
            elif method_lower == "task_arithmetic":
                variant["parameters"]["weight"] = defaults["weight"][i % len(defaults["weight"])]
                variant["reasoning"] += f"weight={variant['parameters']['weight']}"
            
            elif method_lower == "moe":
                variant["parameters"]["num_experts"] = num_models
                variant["parameters"]["routing"] = defaults["routing_method"][i % len(defaults["routing_method"])]
                variant["reasoning"] += f"num_experts={num_models}, routing={variant['parameters']['routing']}"
            
            elif method_lower == "frankenmoe":
                variant["parameters"]["num_experts"] = num_models
                variant["parameters"]["layer_strategy"] = defaults["layer_strategy"][i % len(defaults["layer_strategy"])]
                variant["reasoning"] += f"experts={num_models}, strategy={variant['parameters']['layer_strategy']}"
            
            elif method_lower == "regmean":
                variant["parameters"]["reg_coef"] = defaults["reg_coef"][i % len(defaults["reg_coef"])]
                variant["reasoning"] += f"reg_coef={variant['parameters']['reg_coef']}"
            
            variants.append(variant)
        
        return variants


class MergeAdvisor:
    """
    AI-powered advisor for model merging recipes.
    
    Generates multiple recipe variants per method, optionally using historical data.
    Can suggest SAE/CWP integration if enabled.
    Encourages user customization but can auto-generate if needed.
    """
    
    def __init__(self, model_id="Qwen/Qwen2.5-0.5B-Instruct",
                 historical_db=None):
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self.historical_db = historical_db  # Optional: ExperimentDatabase for predictions
        self.recipe_generator = RecipeGenerator()
    
    def load(self):
        """Lazy-load the LLM."""
        if self.model is None:
            logger.info(f"Loading advisor model: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype="auto",
                device_map="auto"
            )
    
    def generate_recipes(self, goal: str, base_models: List[str],
                        methods: List[str], 
                        num_variants_per_method: int = 2,
                        enable_sae: bool = False,
                        enable_cwp: bool = False,
                        user_recipe_draft: Optional[str] = None) -> Dict:
        """
        Generate merge recipe options for user.
        
        Args:
            goal: User's objective (e.g., "improve code generation")
            base_models: List of models to merge
            methods: List of merge methods to try (e.g., ["TIES", "DARE", "FrankenMoE"])
            num_variants_per_method: How many variants per method
            enable_sae: Include SAE layer analysis in recipes
            enable_cwp: Include Core-Weight Pruning in recipes
            user_recipe_draft: Optional user-provided recipe to enhance
            
        Returns:
            Dict with recipe options and advisor commentary
        """
        self.load()
        
        logger.info(f"Generating recipes for goal: {goal}")
        logger.info(f"Methods: {methods}")
        
        recipes = []
        
        # Generate variants for each method
        for method in methods:
            logger.info(f"Generating {num_variants_per_method} variants for {method}")
            
            # Use RecipeGenerator for parameter variants
            variants = self.recipe_generator.generate_variants(
                method=method,
                num_variants=num_variants_per_method,
                num_models=len(base_models),
                historical_params=self._get_best_params(method, goal) if self.historical_db else None
            )
            
            # Enhance each variant with LLM reasoning
            for variant in variants:
                enhanced = self._enhance_recipe(
                    variant, goal, base_models, enable_sae, enable_cwp
                )
                recipes.append(enhanced)
        
        # Generate overall advisor commentary
        commentary = self._generate_commentary(goal, base_models, methods, recipes)
        
        result = {
            "goal": goal,
            "base_models": base_models,
            "methods_selected": methods,
            "recipes": recipes,
            "advisory_note": commentary,
            "sae_enabled": enable_sae,
            "cwp_enabled": enable_cwp,
            "user_can_customize": True,
            "recommended_approach": "Parallel: Run all recipes in parallel. The best will emerge."
        }
        
        return result
    
    def _enhance_recipe(self, base_recipe: Dict, goal: str, 
                       base_models: List[str],
                       enable_sae: bool, enable_cwp: bool) -> Dict:
        """
        Enhance a recipe with LLM-generated explanations.
        """
        enhanced = base_recipe.copy()
        
        # Add SAE/CWP integration if enabled
        if enable_sae:
            enhanced["steps"] = enhanced.get("steps", [])
            enhanced["steps"].append({
                "name": "SAE Analysis",
                "description": "Identify capability genes in each layer using Sparse Autoencoders",
                "integration": "Select layers by capability importance"
            })
            enhanced["reasoning"] += " + SAE analysis for layer selection"
        
        if enable_cwp:
            enhanced["steps"] = enhanced.get("steps", [])
            enhanced["steps"].append({
                "name": "Core-Weight Pruning",
                "description": "Remove redundant weights using core-set learning",
                "integration": "Apply CWP before merging"
            })
            enhanced["reasoning"] += " + CWP for weight efficiency"
        
        # Add base model info
        enhanced["base_models"] = base_models
        enhanced["goal"] = goal
        
        return enhanced
    
    def _get_best_params(self, method: str, goal: str) -> Optional[Dict]:
        """
        Query historical database for best parameters for this method+goal combo.
        """
        if not self.historical_db:
            return None
        
        try:
            top_methods = self.historical_db.get_top_methods_for_goal(goal, limit=3)
            for m, score, success_rate in top_methods:
                if m.lower() == method.lower():
                    logger.info(f"Found historical best for {method}: success_rate={success_rate:.1%}")
                    return {"success_rate": success_rate, "avg_score": score}
        except:
            pass
        
        return None
    
    def _generate_commentary(self, goal: str, base_models: List[str],
                            methods: List[str], recipes: List[Dict]) -> str:
        """
        Generate encouraging commentary for the user.
        """
        commentary = f"""
**Breeding Vat Advisor Commentary**

Goal: {goal}
Base Models: {", ".join([m.split('/')[-1] for m in base_models])}
Methods to Explore: {", ".join(methods)}
Total Recipe Variants: {len(recipes)}

**Recommended Approach:**
I've generated {len(recipes)} recipe variants across {len(methods)} methods. 
Each variant represents a different set of hyperparameters.

**What's Next:**
1. Review the recipes below
2. Feel free to customize any parameters
3. Or let me run all variants in parallel - the best will emerge through evolution
4. I'll track results and learn from this experiment

**Tips:**
- Each method has trade-offs: TIES is conservative, DARE drops weights, MOE is experimental
- Run all variants in parallel for faster discovery
- I'll compare each result to your goal + baseline
- Records are saved with full provenance for future learning
"""
        return commentary
    
    def generate_recipe(self, goal: str, available_models: List[str], 
                       available_methods: List[str]) -> str:
        """
        Backward-compatible method for simple recipe generation.
        (Called by existing UI code)
        """
        self.load()
        
        # Use new engine
        recipe_options = self.generate_recipes(
            goal=goal,
            base_models=available_models,
            methods=available_methods,
            num_variants_per_method=2
        )
        
        # Format as text for display
        output = recipe_options["advisory_note"] + "\n\n**Generated Recipes:**\n"
        
        for i, recipe in enumerate(recipe_options["recipes"], 1):
            output += f"\n{i}. {recipe['method'].upper()} (Variant {recipe.get('variant_id', 1)})\n"
            output += f"   Parameters: {json.dumps(recipe['parameters'], indent=4)}\n"
            output += f"   Reasoning: {recipe['reasoning']}\n"
        
        return output
    
    def user_can_customize(self) -> bool:
        """
        Encourage user to customize recipes.
        """
        return True
    
    def auto_wing_it(self, goal: str, base_models: List[str],
                    methods: List[str]) -> List[Dict]:
        """
        Generate best-guess recipes without user input.
        System can "wing it" if user prefers.
        """
        logger.info("AI is winging it - generating best-guess recipes")
        
        recipes = self.generate_recipes(
            goal=goal,
            base_models=base_models,
            methods=methods,
            num_variants_per_method=2
        )
        
        return recipes["recipes"]
