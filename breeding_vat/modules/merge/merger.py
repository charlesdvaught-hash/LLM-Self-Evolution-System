import os
import logging
from typing import Dict, List, Optional
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.mergekit_engine import MergekitWrapper, MergekitEngine
from breeding_vat.modules.merge.fusionbench_engine import FusionBenchEngine

logger = logging.getLogger("Merger")

class MergeKitWrapper(MergekitWrapper):
    """
    Main merging interface using Mergekit via Docker.
    All merging operations are containerized - no local dependency hell.
    """
    pass


class AdvancedMerger:
    """Advanced merging techniques via Mergekit + FusionBench."""
    
    def __init__(self, runner: TaskRunner = None):
        self.runner = runner
        self.mergekit = MergeKitWrapper(runner) if runner else None
        self.fusionbench = FusionBenchEngine()
        logger.info("AdvancedMerger initialized with Mergekit + FusionBench backends")
    
    def dare_merge(self, base_model: str, models: List[str], 
                  output_path: str, drop_rate: float = 0.1,
                  **kwargs) -> Optional[str]:
        """
        Drop And REscale (DARE) merging via Mergekit.
        """
        logger.info(f"DARE merge: {len(models)} models, drop_rate={drop_rate}")
        
        config_path = self.mergekit.create_config(
            "dare",
            base_model,
            models,
            {"drop_rate": drop_rate}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def ties_merge(self, base_model: str, models: List[str],
                  output_path: str, threshold: float = 0.9,
                  **kwargs) -> Optional[str]:
        """
        TIES (Trim, Interleave, Elect Subnets) merging via Mergekit.
        """
        logger.info(f"TIES merge: {len(models)} models, threshold={threshold}")
        
        config_path = self.mergekit.create_config(
            "ties",
            base_model,
            models,
            {"threshold": threshold}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def slerp_merge(self, base_model: str, models: List[str],
                   output_path: str, weights: Optional[List[float]] = None,
                   **kwargs) -> Optional[str]:
        """
        Spherical Linear Interpolation (SLERP) merging via Mergekit.
        """
        logger.info(f"SLERP merge: {len(models)} models")
        
        config_path = self.mergekit.create_config(
            "slerp",
            base_model,
            models,
            {"weights": weights}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def moe_merge(self, base_model: str, models: List[str],
                 output_path: str, num_experts: Optional[int] = None,
                 **kwargs) -> Optional[str]:
        """
        Mixture-of-Experts merging via Mergekit.
        Combines models as specialized experts with routing.
        """
        logger.info(f"MOE merge: {len(models)} experts")
        
        config_path = self.mergekit.create_config(
            "moe",
            base_model,
            models,
            {"num_experts": num_experts or len(models)}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def rmm_merge(self, models: List[str], output_path: str,
                 threshold: float = 0.5,
                 **kwargs) -> Optional[str]:
        """
        Resurrection by Majority Merging (RMM).
        Uses majority voting on model weights.
        """
        logger.info(f"RMM merge: {len(models)} models, threshold={threshold}")
        # RMM is typically a variant of TIES, so we use TIES backend
        base_model = models[0]
        merge_models = models[1:]
        
        config_path = self.mergekit.create_config(
            "ties",
            base_model,
            merge_models,
            {"threshold": threshold}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def task_arithmetic_merge(self, base_model: str, models: List[str],
                             output_path: str, weights: Optional[List[float]] = None,
                             **kwargs) -> Optional[str]:
        """
        Task Arithmetic (FusionBench):
        Result = base + α*δ_A + β*δ_B where δ = model - base
        """
        logger.info(f"Task Arithmetic: {len(models)} models")
        return self.fusionbench.task_arithmetic_merge(base_model, models, output_path, weights, **kwargs)
    
    def negmerge(self, base_model: str, positive_models: List[str],
                negative_model: str, output_path: str,
                **kwargs) -> Optional[str]:
        """
        Negative Merging - subtract unwanted model directions.
        """
        logger.info(f"NegMerge: base={base_model}, positive={len(positive_models)}, negative={negative_model}")
        # NegMerge typically uses negative weights
        all_models = positive_models + [negative_model]
        weights = [1.0 / len(positive_models)] * len(positive_models) + [-1.0]
        
        config_path = self.mergekit.create_config(
            "linear",
            base_model,
            all_models,
            {"weights": weights}
        )
        
        output_name = os.path.basename(output_path)
        return self.mergekit.run_merge(config_path, output_name, **kwargs)
    
    def regmean_merge(self, base_model: str, models: List[str],
                     output_path: str, weights: Optional[List[float]] = None,
                     reg: float = 0.0) -> Optional[str]:
        """
        RegMean (FusionBench):
        Regression-based mean with regularization.
        """
        logger.info(f"RegMean: {len(models)} models, reg={reg}")
        return self.fusionbench.regmean_merge(base_model, models, output_path, weights, reg)
    
    def voting_merge(self, models: List[str], output_path: str,
                    voting_method: str = "majority") -> Optional[str]:
        """
        Voting (FusionBench):
        Majority voting on weight values.
        """
        logger.info(f"Voting: {len(models)} models")
        return self.fusionbench.voting_merge(models, output_path, voting_method)
    
    def magnitude_prune_merge(self, models: List[str], output_path: str,
                             prune_ratio: float = 0.1) -> Optional[str]:
        """
        Magnitude Prune (FusionBench):
        Sparse merging with magnitude-based pruning.
        """
        logger.info(f"Magnitude Prune: {len(models)} models, prune_ratio={prune_ratio}")
        return self.fusionbench.magnitude_prune_merge(models, output_path, prune_ratio)
    
    def frankenmerge(self, models: List[str], output_path: str,
                    layer_assignment: Optional[Dict[str, int]] = None,
                    rank: int = 8) -> Optional[str]:
        """
        Frankenmerge (FusionBench):
        Layer-wise expert selection and merging.
        """
        logger.info(f"Frankenmerge: {len(models)} models")
        return self.fusionbench.frankenmerge(models, output_path, layer_assignment, rank)
    
    def git_rebasin_merge(self, base_model: str, models: List[str],
                         output_path: str, weights: Optional[List[float]] = None,
                         lambda_: float = 0.1) -> Optional[str]:
        """
        Git Rebasin (FusionBench):
        Geometric mean in task vector space.
        """
        logger.info(f"Git Rebasin: {len(models)} models")
        return self.fusionbench.git_rebasin_merge(base_model, models, output_path, weights, lambda_)
    
    def get_available_methods(self) -> Dict[str, str]:
        """
        Return all available merging methods.
        Combines MergeKit (SLERP, TIES, DARE, MOE) + FusionBench methods.
        """
        mergekit_methods = {
            "slerp": "Spherical linear interpolation",
            "ties": "Trim, Interleave, Elect Subnets",
            "dare": "Drop And REscale",
            "task_arithmetic": "Vector arithmetic (MergeKit variant)",
            "moe": "Mixture of Experts",
            "rmm": "Resurrection by Majority Merging",
            "negmerge": "Negative direction subtraction"
        }
        
        fusionbench_methods = self.fusionbench.list_methods()
        
        # Merge both, preferring FusionBench for overlaps
        all_methods = {**mergekit_methods, **fusionbench_methods}
        return all_methods
