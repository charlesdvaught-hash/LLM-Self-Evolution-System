"""
Creativity Slider: Control the balance between predictability and innovation.

Maps a single 0-100 slider to all aspects of recipe generation:
- Allowed methods
- Parameter variance
- Algorithm combinations
- Introspection feedback strength
"""

import logging
from typing import Dict, List
import numpy as np

logger = logging.getLogger("CreativitySlider")


class CreativitySlider:
    """
    Maps creativity level (0-100) to evolution configuration.
    
    0 = Textbook (follow research exactly)
    50 = Balanced (proven methods + exploration)
    100 = YOLO (chaos mode, occasionally genius)
    """
    
    PRESETS = {
        "textbook": {
            "name": "Textbook",
            "icon": "🔒",
            "tagline": "Predictable, slow success",
            "description": "Follow best practices from literature exactly",
            "allowed_methods": ["ties", "dare", "task_arithmetic"],
            "parameter_variance": 0.05,
            "randomness": 0.05,
            "recipe_complexity": 1.0,
            "use_best_practices": True,
            "allow_combinations": False,
            "allow_exotic_approaches": False,
            "introspection_feedback": "strict",
            "mutation_strategy": "conservative"
        },
        
        "methodical": {
            "name": "Methodical",
            "icon": "📊",
            "tagline": "Predictable with exploration",
            "description": "Try variations on proven methods",
            "allowed_methods": ["ties", "dare", "task_arithmetic", "slerp", "regmean"],
            "parameter_variance": 0.20,
            "randomness": 0.20,
            "recipe_complexity": 1.0,
            "use_best_practices": True,
            "allow_combinations": False,
            "allow_exotic_approaches": False,
            "introspection_feedback": "moderate",
            "mutation_strategy": "controlled"
        },
        
        "balanced": {
            "name": "Balanced",
            "icon": "⚖️",
            "tagline": "Mix of proven + experimental",
            "description": "Good balance of speed and discovery",
            "allowed_methods": "all",
            "parameter_variance": 0.50,
            "randomness": 0.40,
            "recipe_complexity": 1.5,
            "use_best_practices": True,
            "allow_combinations": True,
            "allow_exotic_approaches": False,
            "introspection_feedback": "balanced",
            "mutation_strategy": "adaptive"
        },
        
        "adventurous": {
            "name": "Adventurous",
            "icon": "🚀",
            "tagline": "High innovation",
            "description": "Explore aggressively, expect breakthroughs + failures",
            "allowed_methods": "all",
            "parameter_variance": 1.0,
            "randomness": 0.65,
            "recipe_complexity": 2.0,
            "use_best_practices": True,
            "allow_combinations": True,
            "allow_exotic_approaches": True,
            "introspection_feedback": "loose",
            "mutation_strategy": "aggressive"
        },
        
        "yolo": {
            "name": "YOLO",
            "icon": "🎲",
            "tagline": "Occasionally genius",
            "description": "Pure chaos - occasionally genius, often nonsense",
            "allowed_methods": "all_random",
            "parameter_variance": 5.0,
            "randomness": 0.90,
            "recipe_complexity": 2.5,
            "use_best_practices": False,
            "allow_combinations": True,
            "allow_exotic_approaches": True,
            "introspection_feedback": "none",
            "mutation_strategy": "chaotic"
        }
    }
    
    @staticmethod
    def get_config_for_slider(value: int) -> Dict:
        """
        Map slider value (0-100) to evolution configuration.
        
        Args:
            value: Slider value 0-100
            
        Returns:
            Configuration dict for evolution
        """
        # Select closest preset
        if value <= 20:
            config = CreativitySlider.PRESETS["textbook"].copy()
        elif value <= 40:
            config = CreativitySlider.PRESETS["methodical"].copy()
        elif value <= 60:
            config = CreativitySlider.PRESETS["balanced"].copy()
        elif value <= 80:
            config = CreativitySlider.PRESETS["adventurous"].copy()
        else:
            config = CreativitySlider.PRESETS["yolo"].copy()
        
        # Interpolate for smooth transitions
        config["creativity_value"] = value
        config["randomness"] = 0.05 + (value / 100.0) * 0.85  # 5% to 90%
        config["parameter_variance"] = 0.05 + (value / 100.0) * 5.0  # 5% to 500%
        
        # Adjust recipe complexity
        if value < 20:
            config["recipe_complexity"] = 1.0
        elif value < 40:
            config["recipe_complexity"] = 1.0
        elif value < 60:
            config["recipe_complexity"] = 1.0 + (value - 40) / 20 * 0.5
        elif value < 80:
            config["recipe_complexity"] = 1.5 + (value - 60) / 20 * 0.5
        else:
            config["recipe_complexity"] = 2.0 + (value - 80) / 20 * 0.5
        
        return config
    
    @staticmethod
    def describe_slider_position(value: int) -> str:
        """Generate user-friendly description of slider position."""
        if value < 20:
            return "🔒 Conservative: Follow best practices closely. Predictable, slow progress."
        elif value < 40:
            return "📊 Methodical: Try variations on proven methods. Steady improvement."
        elif value < 60:
            return "⚖️ Balanced: Mix proven methods with exploration. Good for most goals. RECOMMENDED."
        elif value < 80:
            return "🚀 Adventurous: Explore aggressively. Expect breakthroughs and failures."
        else:
            return "🎲 YOLO: Pure chaos. Occasionally genius, often nonsense."
    
    @staticmethod
    def get_all_fusionbench_methods() -> List[str]:
        """Get all available FusionBench algorithms."""
        return [
            # Basic
            "ties", "dare", "slerp", "task_arithmetic", "regmean",
            # Advanced
            "adamerging", "fisher_merging", "weighted_averaging",
            # Specialized
            "model_stock", "isotropic_merging", "wudi_merging",
            # MOE
            "moe", "weight_ensembling_moe", "rankone_moe",
            # Compression
            "surgery", "tall_mask", "trust_region",
            # Experimental
            "dop", "fw_merging", "doget", "ada_svd",
            # Plus others
            "simple_averaging", "linear", "concrete_subspace"
        ]


class AdvisorWithCreativity:
    """
    Recipe generator that respects creativity slider.
    """
    
    def __init__(self):
        self.fusionbench_methods = CreativitySlider.get_all_fusionbench_methods()
    
    def generate_recipes(self, goal: str, base_models: List[str],
                        methods: List[str], creativity_value: int = 50) -> List[Dict]:
        """
        Generate recipes filtered and modified by creativity level.
        
        Args:
            goal: Evolution goal
            base_models: Base models to merge
            methods: Requested merge methods
            creativity_value: 0-100 slider value
            
        Returns:
            List of recipe dicts
        """
        config = CreativitySlider.get_config_for_slider(creativity_value)
        
        logger.info(f"Generating recipes at creativity={creativity_value}")
        logger.info(f"Config: randomness={config['randomness']:.1%}, variance=±{config['parameter_variance']*100:.0f}%")
        
        # Filter methods based on creativity
        available_methods = self._get_available_methods(config)
        
        # Filter requested methods
        selected_methods = [m for m in methods if m.lower() in available_methods]
        
        if not selected_methods:
            logger.warning(f"No methods available at creativity {creativity_value}")
            selected_methods = available_methods[:3]
        
        recipes = []
        
        # Generate single-algorithm variants
        for method in selected_methods:
            num_variants = 2 + int(config["recipe_complexity"])
            
            for variant_idx in range(num_variants):
                recipe = self._generate_single_recipe(
                    method=method,
                    variant_idx=variant_idx,
                    config=config,
                    base_models=base_models,
                    creativity_value=creativity_value
                )
                recipes.append(recipe)
        
        # Generate combination recipes if creativity allows
        if config["allow_combinations"] and creativity_value >= 40:
            num_combos = max(1, int(config["recipe_complexity"] / 2))
            for combo_idx in range(num_combos):
                combo_recipe = self._generate_combination_recipe(
                    available_methods=selected_methods,
                    combo_idx=combo_idx,
                    config=config,
                    base_models=base_models,
                    creativity_value=creativity_value
                )
                recipes.append(combo_recipe)
        
        logger.info(f"Generated {len(recipes)} recipes")
        return recipes
    
    def _get_available_methods(self, config: Dict) -> List[str]:
        """Get methods available at this creativity level."""
        if config["allowed_methods"] == "all":
            return self.fusionbench_methods
        elif config["allowed_methods"] == "all_random":
            return self.fusionbench_methods
        else:
            return config["allowed_methods"]
    
    def _generate_single_recipe(self, method: str, variant_idx: int,
                               config: Dict, base_models: List[str],
                               creativity_value: int) -> Dict:
        """Generate a single-algorithm recipe variant."""
        
        params = self._get_method_default_parameters(method)
        
        # Apply parameter variance based on creativity
        variance = config["parameter_variance"]
        
        if creativity_value < 20:
            # Textbook: use defaults exactly
            for param in params:
                params[param] = params[param]["default"]
        else:
            # Apply randomized variance
            for param in params:
                default = params[param]["default"]
                param_min = params[param]["min"]
                param_max = params[param]["max"]
                
                if creativity_value >= 80:
                    # YOLO: random within full range
                    params[param] = np.random.uniform(param_min, param_max)
                else:
                    # Bounded variation from default
                    variation = default * variance * (2 * np.random.random() - 1)
                    params[param] = np.clip(default + variation, param_min, param_max)
        
        recipe = {
            "method": method,
            "variant_id": variant_idx + 1,
            "parameters": params,
            "creativity_level": creativity_value,
            "base_models": base_models,
            "complexity": 1,
            "description": f"{method.upper()} variant {variant_idx + 1}"
        }
        
        return recipe
    
    def _generate_combination_recipe(self, available_methods: List[str],
                                    combo_idx: int, config: Dict,
                                    base_models: List[str],
                                    creativity_value: int) -> Dict:
        """Generate a multi-algorithm combination recipe."""
        
        # Decide how many methods to combine
        if creativity_value < 60:
            num_methods = 2
        elif creativity_value < 80:
            num_methods = 2 if np.random.random() < 0.8 else 3
        else:
            num_methods = np.random.randint(2, 4)
        
        # Select methods (with replacement allowed for YOLO)
        if creativity_value >= 80:
            selected = np.random.choice(available_methods, size=num_methods, replace=True)
        else:
            selected = np.random.choice(
                available_methods,
                size=min(num_methods, len(available_methods)),
                replace=False
            )
        
        # Determine combination type
        if creativity_value < 60:
            combo_type = "sequential"
        elif creativity_value < 80:
            combo_type = np.random.choice(["sequential", "parallel"])
        else:
            combo_type = np.random.choice(["sequential", "parallel", "layerwise_routing", "interleaved"])
        
        recipe = {
            "method": f"combined_{len(selected)}way",
            "algorithms": list(selected),
            "combination_type": combo_type,
            "variant_id": combo_idx + 1,
            "creativity_level": creativity_value,
            "base_models": base_models,
            "complexity": len(selected),
            "description": f"Combo: {'+'.join(selected)} ({combo_type})"
        }
        
        return recipe
    
    def _get_method_default_parameters(self, method: str) -> Dict:
        """Get parameter ranges for a method."""
        # Standard parameter ranges for common methods
        params_db = {
            "ties": {
                "threshold": {"default": 0.9, "min": 0.5, "max": 0.99},
                "weight": {"default": 0.5, "min": 0.1, "max": 0.9}
            },
            "dare": {
                "drop_rate": {"default": 0.1, "min": 0.0, "max": 0.5},
                "weight": {"default": 0.5, "min": 0.1, "max": 0.9}
            },
            "task_arithmetic": {
                "weight": {"default": 0.3, "min": 0.1, "max": 1.0}
            },
            "slerp": {
                "t": {"default": 0.5, "min": 0.0, "max": 1.0}
            },
            "regmean": {
                "reg_coef": {"default": 1e-6, "min": 1e-8, "max": 1e-3}
            },
            "moe": {
                "num_experts": {"default": 2, "min": 2, "max": 8},
                "routing": {"default": 0.5, "min": 0.0, "max": 1.0}
            }
        }
        
        return params_db.get(method.lower(), {"weight": {"default": 0.5, "min": 0.1, "max": 0.9}})


class EvolutionWithCreativity:
    """
    Evolution engine that uses creativity slider to guide generation.
    """
    
    def __init__(self, advisor: AdvisorWithCreativity):
        self.advisor = advisor
        self.creativity_history = []
    
    def run_generation(self, goal: str, base_models: List[str],
                      methods: List[str], cycle_num: int,
                      creativity_value: int) -> List[Dict]:
        """
        Run one generation with current creativity setting.
        """
        logger.info(f"Generation {cycle_num} at creativity={creativity_value}")
        
        # Generate recipes
        recipes = self.advisor.generate_recipes(
            goal=goal,
            base_models=base_models,
            methods=methods,
            creativity_value=creativity_value
        )
        
        # Execute recipes and collect results
        results = []
        for recipe in recipes:
            try:
                # Run merge, evaluate, etc.
                # (integration with FusionEngine happens here)
                result = {
                    "recipe": recipe,
                    "cycle": cycle_num,
                    "creativity": creativity_value
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Recipe execution failed: {e}")
        
        # Track creativity history
        self.creativity_history.append({
            "cycle": cycle_num,
            "creativity": creativity_value,
            "num_recipes": len(recipes),
            "success_rate": len(results) / len(recipes) if recipes else 0
        })
        
        return results
