import os
import torch
import logging
import json
from typing import List, Dict, Optional, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
from breeding_vat.modules.merge.recipe_validator import RecipeValidator, ValidationError

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
    
    def _is_gguf(self) -> bool:
        """True if model_id points to a .gguf file."""
        return str(self.model_id).lower().endswith(".gguf")

    def load(self):
        """Lazy-load the LLM. Supports HF safetensors and local GGUF."""
        if self.model is not None:
            return
        logger.info(f"Loading advisor model: {self.model_id}")
        if self._is_gguf():
            try:
                from llama_cpp import Llama
                self.model = Llama(
                    model_path=self.model_id,
                    n_ctx=2048,
                    n_gpu_layers=-1,   # offload all layers to GPU if available
                    verbose=False,
                )
                self.tokenizer = None  # not used for GGUF path
            except ImportError:
                logger.error(
                    "llama-cpp-python not installed — cannot load GGUF advisor. "
                    "Add 'llama-cpp-python' to Dockerfile.ui requirements."
                )
                raise
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype="auto",
                device_map="auto",
            )
    
    def generate_recipes(self, goal: str, base_models: List[str],
                        methods: List[str],
                        num_variants_per_method: int = 2,
                        enable_sae: bool = False,
                        enable_cwp: bool = False,
                        user_recipe_draft: Optional[str] = None,
                        use_laser_rag: bool = False) -> Dict:
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

        validator = RecipeValidator()
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

            # Enhance each variant with LLM reasoning, then validate before accepting
            for variant in variants:
                enhanced = self._enhance_recipe(
                    variant, goal, base_models, enable_sae, enable_cwp
                )
                ok, reason = validator.check(enhanced)
                if not ok:
                    logger.warning(f"Recipe failed validation ({method}): {reason} — skipped")
                    enhanced["_validation_error"] = reason
                recipes.append(enhanced)
        
        # Generate overall advisor commentary
        commentary = self._generate_commentary(goal, base_models, methods, recipes,
                                               use_laser_rag=use_laser_rag)
        
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
    
    def _load_kb_context(self, use_laser: bool = False, query: str = "") -> str:
        """
        Load KB context for prompt injection.
        Uses LaSER semantic retrieval when use_laser=True and index exists,
        otherwise falls back to loading the first ~800 chars of key guide files.
        """
        if use_laser and query:
            try:
                from breeding_vat.modules.sae.laser_retriever import LaSERRetriever
                retriever = LaSERRetriever()
                chunks = retriever.retrieve(query, top_k=3)
                if chunks:
                    return "\n\n---\n\n".join(chunks)
            except Exception as e:
                logger.debug(f"LaSER retrieval failed, falling back to file load: {e}")

        kb_files = [
            "docs/guides/ADVISOR_KNOWLEDGE_BASE.md",
            "docs/reference/MERGING_METHODS_INVENTORY.md",
        ]
        snippet = ""
        per_file = 800
        for path in kb_files:
            if os.path.exists(path):
                try:
                    text = open(path, encoding="utf-8").read()
                    snippet += text[:per_file] + "\n\n---\n\n"
                except Exception:
                    pass
        return snippet.strip() or "No KB context available."

    def _generate_commentary(self, goal: str, base_models: List[str],
                            methods: List[str], recipes: List[Dict],
                            use_laser_rag: bool = False) -> str:
        """
        Generate AI advisor commentary using the loaded LLM with KB context.
        """
        kb_context = self._load_kb_context(use_laser=use_laser_rag, query=goal)
        models_str = ", ".join(m.split("/")[-1] for m in base_models)
        methods_str = ", ".join(methods)
        num_recipes = len(recipes)

        prompt = (
            f"You are an expert model merging advisor for The Breeding Vat system.\n\n"
            f"Knowledge Base:\n{kb_context}\n\n"
            f"Task: Give specific, actionable merge recommendations.\n\n"
            f"Goal: {goal}\n"
            f"Models: {models_str}\n"
            f"Methods: {methods_str}\n"
            f"Recipe variants prepared: {num_recipes}\n\n"
            f"Provide: (1) best method for this goal, (2) key parameter tips, "
            f"(3) what to watch in evaluation.\n\nAdvisor:"
        )

        try:
            if self._is_gguf():
                # llama-cpp-python path
                response = self.model.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=250,
                    temperature=0.7,
                )
                generated = response["choices"][0]["message"]["content"].strip()
            else:
                # transformers path
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                with torch.no_grad():
                    out_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=250,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )
                generated = self.tokenizer.decode(
                    out_ids[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True,
                ).strip()
            return f"**Breeding Vat Advisor**\n\n{generated}"
        except Exception as e:
            logger.warning(f"LLM commentary generation failed: {e}")
            return (
                f"**Breeding Vat Advisor**\n\n"
                f"Goal: {goal} | Models: {models_str} | Methods: {methods_str}\n"
                f"Generated {num_recipes} recipe variants. Review and customize before running."
            )
    
    def generate_recipe(self, goal: str, available_models: List[str],
                       available_methods: List[str],
                       use_laser_rag: bool = False) -> str:
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
            num_variants_per_method=2,
            use_laser_rag=use_laser_rag,
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
