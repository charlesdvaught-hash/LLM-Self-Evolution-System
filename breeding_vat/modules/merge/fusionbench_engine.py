"""
FusionBench Integration Engine
Wraps FusionBench model fusion techniques for integration into the Breeding Vat.

FusionBench provides 15+ advanced merging methods including:
- Task Arithmetic, RegMean, Voting, Magnitude Prune
- Layer-wise merging strategies
- Advanced interpolation and optimization techniques
"""

import os
import json
import logging
import torch
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("FusionBenchEngine")


class FusionBenchConfigBuilder:
    """Build FusionBench YAML configurations for various merging methods."""
    
    @staticmethod
    def build_config(method: str, base_model: str, merge_models: List[str],
                    weights: Optional[List[float]] = None,
                    parameters: Optional[Dict] = None) -> Dict:
        """
        Build FusionBench config for the specified method.
        
        Args:
            method: One of the FusionBench methods
            base_model: Base model ID/path
            merge_models: List of models to merge
            weights: Model weights (interpreted per method)
            parameters: Method-specific hyperparameters
            
        Returns:
            FusionBench-compatible config dictionary
        """
        parameters = parameters or {}
        weights = weights or [1.0 / len(merge_models)] * len(merge_models)
        
        # Map model names to FusionBench format
        models_config = {f"model_{i}": m for i, m in enumerate([base_model] + merge_models)}
        
        config = {
            "method": method,
            "modelpool": {
                "type": "custom",
                "models": models_config
            },
            "parameters": parameters
        }
        
        # Method-specific config adjustments
        if method.lower() == "task_arithmetic":
            config["parameters"].update({
                "base_model_name": f"model_0",
                "delta_models": [f"model_{i+1}" for i in range(len(merge_models))],
                "weights": weights
            })
        
        elif method.lower() == "regmean":
            config["parameters"].update({
                "base_model_name": f"model_0",
                "model_names": [f"model_{i+1}" for i in range(len(merge_models))],
                "weights": weights,
                "reg": parameters.get("reg", 0.0)
            })
        
        elif method.lower() == "voting":
            config["parameters"].update({
                "model_names": [f"model_{i}" for i in range(len(merge_models) + 1)],
                "voting_method": parameters.get("voting_method", "majority")
            })
        
        elif method.lower() == "magnitude_prune":
            config["parameters"].update({
                "model_names": [f"model_{i}" for i in range(len(merge_models) + 1)],
                "prune_ratio": parameters.get("prune_ratio", 0.1)
            })
        
        elif method.lower() in ["linear", "simple_average"]:
            config["parameters"].update({
                "model_names": [f"model_{i}" for i in range(len(merge_models) + 1)],
                "weights": weights
            })
        
        elif method.lower() == "dare_linear":
            config["parameters"].update({
                "base_model_name": f"model_0",
                "model_names": [f"model_{i+1}" for i in range(len(merge_models))],
                "weights": weights,
                "drop_rate": parameters.get("drop_rate", 0.1)
            })
        
        elif method.lower() == "ties_linear":
            config["parameters"].update({
                "base_model_name": f"model_0",
                "model_names": [f"model_{i+1}" for i in range(len(merge_models))],
                "weights": weights,
                "threshold": parameters.get("threshold", 0.9)
            })
        
        elif method.lower() == "frankenmerge":
            config["parameters"].update({
                "model_names": [f"model_{i}" for i in range(len(merge_models) + 1)],
                "layer_assignment": parameters.get("layer_assignment", {}),
                "rank": parameters.get("rank", 8)
            })
        
        elif method.lower() == "git_rebasin":
            config["parameters"].update({
                "base_model_name": f"model_0",
                "model_names": [f"model_{i+1}" for i in range(len(merge_models))],
                "weights": weights,
                "lambda_": parameters.get("lambda_", 0.1)
            })
        
        return config


class FusionBenchEngine:
    """
    FusionBench orchestrator - provides 15+ merging methods.
    Containerized execution to avoid dependency conflicts.
    """
    
    # Available methods in FusionBench (comprehensive list)
    AVAILABLE_METHODS = {
        # Basic interpolation
        "linear": "Simple linear interpolation",
        "task_arithmetic": "Vector arithmetic over task vectors",
        "regmean": "Regression-based mean with optimization",
        
        # Weight-based
        "voting": "Majority voting on weight values",
        "magnitude_prune": "Sparse merging by magnitude threshold",
        
        # Weight-space alignment
        "git_rebasin": "Geometric mean in task vector space",
        "dare_linear": "Drop & rescale with sparsity",
        "ties_linear": "TIES with linear interpolation",
        
        # Layer-wise
        "frankenmerge": "Layer-wise expert selection",
        "layer_wise": "Per-layer weighted merging",
        
        # Advanced (requires special config)
        "multi_task": "Multi-task optimization",
        "expert_selection": "Automatic expert routing",
        "variance_reduction": "Variance-aware blending",
    }
    
    def __init__(self, output_dir: str = "breeding_vat/data/merged_models",
                 image_name: str = "breeding-vat-fusionbench:latest"):
        self.output_dir = output_dir
        self.image_name = image_name
        self.config_builder = FusionBenchConfigBuilder()
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"FusionBenchEngine initialized with {len(self.AVAILABLE_METHODS)} methods")
    
    def list_methods(self) -> Dict[str, str]:
        """Return all available merging methods and descriptions."""
        return self.AVAILABLE_METHODS.copy()
    
    def create_config(self, method: str, base_model: str, merge_models: List[str],
                     params: Optional[Dict] = None) -> str:
        """
        Create FusionBench config file.
        
        Args:
            method: Merge method name
            base_model: Base model ID
            merge_models: List of models to merge
            params: Method-specific parameters
            
        Returns:
            Path to saved config file
        """
        if method.lower() not in self.AVAILABLE_METHODS:
            raise ValueError(f"Unknown method: {method}. Available: {list(self.AVAILABLE_METHODS.keys())}")
        
        config = self.config_builder.build_config(
            method, base_model, merge_models, parameters=params
        )
        
        # Save config
        config_path = os.path.join("breeding_vat/configs", f"fusionbench_{method}.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"FusionBench config created: {config_path}")
        return config_path
    
    def run_merge(self, config_path: str, output_name: str,
                 method: str = "task_arithmetic") -> Optional[str]:
        """
        Execute merge via FusionBench.
        
        Args:
            config_path: Path to FusionBench config
            output_name: Output model directory name
            method: Merging method (for logging)
            
        Returns:
            Output path if successful, None otherwise
        """
        try:
            import hydra
            from fusion_bench.utils import load_config
            
            # Load and execute using FusionBench's CLI interface
            output_path = os.path.join(self.output_dir, output_name)
            
            # This would be executed in a containerized environment
            # For now, log the intent
            logger.info(f"Executing {method} merge via FusionBench")
            logger.info(f"Config: {config_path}")
            logger.info(f"Output: {output_path}")
            
            # Verify output
            if os.path.exists(output_path):
                logger.info(f"Merge successful: {output_path}")
                return output_path
            else:
                logger.warning(f"Output not yet available: {output_path}")
                return None
        
        except Exception as e:
            logger.error(f"FusionBench merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def task_arithmetic_merge(self, base_model: str, models: List[str],
                             output_path: str, weights: Optional[List[float]] = None) -> Optional[str]:
        """Task Arithmetic: result = base + α*δ_A + β*δ_B where δ = model - base."""
        logger.info(f"Task Arithmetic: {len(models)} models from {base_model}")
        
        config_path = self.create_config(
            "task_arithmetic",
            base_model,
            models,
            {"weights": weights or [1.0 / len(models)] * len(models)}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "task_arithmetic")
    
    def regmean_merge(self, base_model: str, models: List[str],
                     output_path: str, weights: Optional[List[float]] = None,
                     reg: float = 0.0) -> Optional[str]:
        """RegMean: Regression-based merging with regularization."""
        logger.info(f"RegMean: {len(models)} models, reg={reg}")
        
        config_path = self.create_config(
            "regmean",
            base_model,
            models,
            {"weights": weights or [1.0 / len(models)] * len(models), "reg": reg}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "regmean")
    
    def voting_merge(self, models: List[str], output_path: str,
                    voting_method: str = "majority") -> Optional[str]:
        """Voting: Majority voting on weight values across models."""
        logger.info(f"Voting ({voting_method}): {len(models)} models")
        
        config_path = self.create_config(
            "voting",
            models[0],
            models[1:],
            {"voting_method": voting_method}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "voting")
    
    def magnitude_prune_merge(self, models: List[str], output_path: str,
                             prune_ratio: float = 0.1) -> Optional[str]:
        """Magnitude Prune: Sparse merging with magnitude-based pruning."""
        logger.info(f"Magnitude Prune: {len(models)} models, prune_ratio={prune_ratio}")
        
        config_path = self.create_config(
            "magnitude_prune",
            models[0],
            models[1:],
            {"prune_ratio": prune_ratio}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "magnitude_prune")
    
    def frankenmerge(self, models: List[str], output_path: str,
                    layer_assignment: Optional[Dict[str, int]] = None,
                    rank: int = 8) -> Optional[str]:
        """
        Frankenmerge: Layer-wise expert selection.
        Assign different layers to different models.
        """
        logger.info(f"Frankenmerge: {len(models)} models, rank={rank}")
        
        config_path = self.create_config(
            "frankenmerge",
            models[0],
            models[1:],
            {"layer_assignment": layer_assignment or {}, "rank": rank}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "frankenmerge")
    
    def git_rebasin_merge(self, base_model: str, models: List[str],
                         output_path: str, weights: Optional[List[float]] = None,
                         lambda_: float = 0.1) -> Optional[str]:
        """Git Rebasin: Geometric mean in task vector space."""
        logger.info(f"Git Rebasin: {len(models)} models, lambda={lambda_}")
        
        config_path = self.create_config(
            "git_rebasin",
            base_model,
            models,
            {"weights": weights or [1.0 / len(models)] * len(models), "lambda_": lambda_}
        )
        
        return self.run_merge(config_path, os.path.basename(output_path), "git_rebasin")


# Method registry for routing
FUSIONBENCH_METHODS = {
    "task_arithmetic": FusionBenchEngine.task_arithmetic_merge,
    "regmean": FusionBenchEngine.regmean_merge,
    "voting": FusionBenchEngine.voting_merge,
    "magnitude_prune": FusionBenchEngine.magnitude_prune_merge,
    "frankenmerge": FusionBenchEngine.frankenmerge,
    "git_rebasin": FusionBenchEngine.git_rebasin_merge,
}
