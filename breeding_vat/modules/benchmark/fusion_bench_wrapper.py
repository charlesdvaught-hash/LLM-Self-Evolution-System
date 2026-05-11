import yaml
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from breeding_vat.orchestrator.runner import TaskRunner

logger = logging.getLogger("FusionBenchWrapper")

class FusionBenchWrapper:
    """
    Orchestrate FusionBench merging + evaluation via Docker.
    
    FusionBench provides:
    - 20+ merge algorithms with research-grade implementations
    - Integrated LM-Eval harness for standardized benchmarking
    - Experiment tracking and meta-learning
    - Statistical analysis and method recommendation
    """
    
    def __init__(self, runner: TaskRunner, output_dir="breeding_vat/data/fusion_results",
                 image_name="breeding-vat-fusionbench:latest"):
        self.runner = runner
        self.output_dir = output_dir
        self.image_name = image_name
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"FusionBenchWrapper initialized (image: {image_name})")
    
    def create_fusion_config(self, algorithm: str, base_model: str, 
                            merge_models: List[str], task_names: List[str],
                            params: Optional[Dict] = None) -> str:
        """
        Create a FusionBench configuration YAML.
        
        Args:
            algorithm: FusionBench algorithm (ties, dare, task_arithmetic, etc.)
            base_model: Base model path/ID
            merge_models: List of models to merge
            task_names: Evaluation tasks (mmlu, arc_challenge, hellaswag, etc.)
            params: Algorithm-specific parameters
            
        Returns:
            Path to generated config file
        """
        params = params or {}
        
        logger.info(f"Building FusionBench config: {algorithm}")
        
        # FusionBench config structure
        config = {
            "algorithm": algorithm,
            "model_pool": {
                "type": "huggingface",
                "base_model": base_model,
                "models": merge_models
            },
            "task_pool": {
                "type": "lm_eval_harness",
                "tasks": task_names
            },
            "parameters": params or {},
            "save_dir": "/app/results",
            "dtype": "float16"
        }
        
        # Add algorithm-specific defaults
        if algorithm == "ties":
            config["parameters"].setdefault("threshold", 0.9)
            config["parameters"].setdefault("weight", 0.5)
        elif algorithm == "dare":
            config["parameters"].setdefault("drop_rate", 0.1)
            config["parameters"].setdefault("weight", 0.5)
        elif algorithm == "task_arithmetic":
            config["parameters"].setdefault("weight", 0.5)
        elif algorithm == "regmean":
            config["parameters"].setdefault("reg_coef", 1e-8)
        elif algorithm == "moe":
            config["parameters"].setdefault("num_experts", len(merge_models))
        
        # Save config
        config_path = os.path.join("breeding_vat/configs", f"fusionbench_{algorithm}.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        logger.info(f"Config saved: {config_path}")
        return config_path
    
    def run_fusion(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        Execute FusionBench merge + evaluation in container.
        
        Args:
            config_path: Path to FusionBench config
            
        Returns:
            Dictionary with results: {merged_model, scores, metadata}
        """
        try:
            # Prepare volumes
            volumes = {
                "breeding_vat/configs": "/app/configs",
                "breeding_vat/data": "/app/data",
                "~/.cache/huggingface": "/root/.cache/huggingface"
            }
            
            config_filename = os.path.basename(config_path)
            container_config = f"/app/configs/{config_filename}"
            
            # FusionBench command
            command = [
                "fusion_bench",
                "run",
                f"--config-path=/app/configs",
                f"--config-name={os.path.splitext(config_filename)[0]}"
            ]
            
            logger.info(f"Running FusionBench: {' '.join(command)}")
            
            # Execute in container
            self.runner.run_docker_task(
                self.image_name,
                command,
                volumes=volumes,
                gpus="all"
            )
            
            # Parse results
            results_dir = "breeding_vat/data/fusion_results"
            result_file = os.path.join(results_dir, "results.json")
            
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    results = json.load(f)
                logger.info(f"FusionBench run complete")
                return results
            else:
                logger.warning("No results found")
                return None
        
        except Exception as e:
            logger.error(f"FusionBench execution failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_merge_with_eval(self, algorithm: str, base_model: str,
                           merge_models: List[str], 
                           eval_tasks: Optional[List[str]] = None,
                           params: Optional[Dict] = None,
                           output_name: Optional[str] = None) -> Optional[Dict]:
        """
        Complete pipeline: merge + evaluate using FusionBench.
        
        Args:
            algorithm: Merge algorithm
            base_model: Base model
            merge_models: Models to merge
            eval_tasks: Tasks to evaluate on (defaults to standard set)
            params: Algorithm parameters
            output_name: Output model name
            
        Returns:
            Results dict with merged model path and evaluation scores
        """
        if eval_tasks is None:
            eval_tasks = ["mmlu", "arc_challenge", "hellaswag"]
        
        if output_name is None:
            output_name = f"{algorithm}_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Running FusionBench pipeline")
        logger.info(f"  Algorithm: {algorithm}")
        logger.info(f"  Base: {base_model}")
        logger.info(f"  Merge: {merge_models}")
        logger.info(f"  Eval tasks: {eval_tasks}")
        
        # Create config
        config_path = self.create_fusion_config(
            algorithm, base_model, merge_models, eval_tasks, params
        )
        
        # Run fusion
        results = self.run_fusion(config_path)
        
        if results:
            results["output_name"] = output_name
            results["algorithm"] = algorithm
            results["timestamp"] = datetime.now().isoformat()
        
        return results
