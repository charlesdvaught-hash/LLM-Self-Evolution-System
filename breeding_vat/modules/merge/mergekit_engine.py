import yaml
import os
import json
import logging
import subprocess
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from breeding_vat.orchestrator.runner import TaskRunner

logger = logging.getLogger("MergekitEngine")

class MergekitConfigBuilder:
    """Build Mergekit YAML configurations programmatically."""
    
    @staticmethod
    def build_slerp_config(base_model: str, merge_models: List[str], 
                          weights: Optional[List[float]] = None) -> Dict:
        """Build SLERP merge configuration."""
        if weights is None:
            weights = [1.0 / len(merge_models)] * len(merge_models)
        
        models = [{"model": base_model, "weight": 1.0}]
        for model, weight in zip(merge_models, weights):
            models.append({"model": model, "weight": weight})
        
        return {
            "merge_method": "slerp",
            "base_model": base_model,
            "models": models,
            "parameters": {
                "t": [0.5] * (len(merge_models) + 1)
            },
            "dtype": "float16"
        }
    
    @staticmethod
    def build_ties_config(base_model: str, merge_models: List[str],
                         weights: Optional[List[float]] = None,
                         threshold: float = 0.9) -> Dict:
        """Build TIES merge configuration."""
        if weights is None:
            weights = [1.0 / len(merge_models)] * len(merge_models)
        
        models = [{"model": base_model}]
        for model, weight in zip(merge_models, weights):
            models.append({
                "model": model,
                "parameters": {"weight": weight, "density": threshold}
            })
        
        return {
            "merge_method": "ties",
            "base_model": base_model,
            "models": models,
            "dtype": "float16"
        }
    
    @staticmethod
    def build_dare_config(base_model: str, merge_models: List[str],
                         weights: Optional[List[float]] = None,
                         drop_rate: float = 0.1) -> Dict:
        """Build DARE merge configuration."""
        if weights is None:
            weights = [1.0 / len(merge_models)] * len(merge_models)
        
        models = [{"model": base_model}]
        for model, weight in zip(merge_models, weights):
            models.append({
                "model": model,
                "parameters": {"weight": weight, "drop_rate": drop_rate}
            })
        
        return {
            "merge_method": "dare_linear",
            "base_model": base_model,
            "models": models,
            "dtype": "float16"
        }
    
    @staticmethod
    def build_task_arithmetic_config(base_model: str, merge_models: List[str],
                                    weights: Optional[List[float]] = None) -> Dict:
        """Build Task Arithmetic merge configuration."""
        if weights is None:
            weights = [1.0 / len(merge_models)] * len(merge_models)
        
        models = [{"model": base_model}]
        for model, weight in zip(merge_models, weights):
            models.append({
                "model": model,
                "parameters": {"weight": weight}
            })
        
        return {
            "merge_method": "task_arithmetic",
            "base_model": base_model,
            "models": models,
            "dtype": "float16"
        }
    
    @staticmethod
    def build_moe_config(base_model: str, merge_models: List[str],
                        num_experts: Optional[int] = None) -> Dict:
        """Build Mixture-of-Experts merge configuration."""
        if num_experts is None:
            num_experts = len(merge_models)
        
        return {
            "merge_method": "moe",
            "base_model": base_model,
            "models": [{"model": m} for m in merge_models],
            "parameters": {
                "num_experts": num_experts,
                "expert_model_idx": list(range(len(merge_models)))
            },
            "dtype": "float16"
        }


class MergekitEngine:
    """
    Orchestrate model merging via Mergekit in a Docker container.
    Keeps all dependencies isolated and avoids dependency hell.
    """
    
    def __init__(self, runner: TaskRunner, output_dir="breeding_vat/data/merged_models",
                 image_name="breeding-vat-merge:latest"):
        self.runner = runner
        self.output_dir = output_dir
        self.image_name = image_name
        self.config_builder = MergekitConfigBuilder()
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"MergekitEngine initialized (image: {image_name})")
    
    def create_config(self, method: str, base_model: str, merge_models: List[str],
                     params: Optional[Dict] = None) -> str:
        """
        Create a Mergekit config file.
        
        Args:
            method: Merge method (slerp, ties, dare, task_arithmetic, moe, etc)
            base_model: Base model path/ID
            merge_models: List of models to merge
            params: Method-specific parameters
            
        Returns:
            Path to generated config file
        """
        params = params or {}
        
        logger.info(f"Building {method} config for {base_model}")
        
        # Build config based on method
        if method.lower() == "slerp":
            config = self.config_builder.build_slerp_config(
                base_model, merge_models, params.get("weights")
            )
        elif method.lower() == "ties":
            config = self.config_builder.build_ties_config(
                base_model, merge_models, params.get("weights"),
                params.get("threshold", 0.9)
            )
        elif method.lower() == "dare":
            config = self.config_builder.build_dare_config(
                base_model, merge_models, params.get("weights"),
                params.get("drop_rate", 0.1)
            )
        elif method.lower() == "task_arithmetic":
            config = self.config_builder.build_task_arithmetic_config(
                base_model, merge_models, params.get("weights")
            )
        elif method.lower() == "moe":
            config = self.config_builder.build_moe_config(
                base_model, merge_models, params.get("num_experts")
            )
        else:
            raise ValueError(f"Unsupported merge method: {method}")
        
        # Save config
        config_path = os.path.join("breeding_vat/configs", f"mergekit_{method}.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        logger.info(f"Config saved: {config_path}")
        return config_path
    
    def run_merge(self, config_path: str, output_name: str, 
                 chat_template: Optional[str] = None,
                 low_cpu_mem: bool = False,
                 copy_tokenizer: bool = True,
                 trust_remote_code: bool = False,
                 lazy_unpickle: bool = False) -> Optional[str]:
        """
        Execute merge via Mergekit in container.
        
        Args:
            config_path: Path to merge config (relative to project root)
            output_name: Output model directory name
            chat_template: Optional chat template for tokenizer
            low_cpu_mem: Use --low-cpu-mem flag
            copy_tokenizer: Use --copy-tokenizer flag
            trust_remote_code: Use --trust-remote-code flag
            lazy_unpickle: Use --lazy-unpickle flag
            
        Returns:
            Output path if successful, None otherwise
        """
        try:
            # Ensure image exists
            if not self._image_exists():
                logger.error(f"Image {self.image_name} not found")
                raise RuntimeError(f"Build image with: docker build -f docker/Dockerfile.merge -t {self.image_name} .")
            
            # Prepare volumes
            volumes = {
                "breeding_vat/configs": "/app/configs",
                "breeding_vat/data": "/app/data",
                "~/.cache/huggingface": "/root/.cache/huggingface"  # Model cache
            }
            
            # Mergekit command
            config_filename = os.path.basename(config_path)
            container_config = f"/app/configs/{config_filename}"
            container_output = f"/app/data/merged_models/{output_name}"
            
            command = [
                "mergekit-yaml",
                container_config,
                container_output,
                "--cuda",
                "--allow-patterns", "*"
            ]
            
            if low_cpu_mem:
                command.append("--low-cpu-mem")
            if copy_tokenizer:
                command.append("--copy-tokenizer")
            if trust_remote_code:
                command.append("--trust-remote-code")
            if lazy_unpickle:
                command.append("--lazy-unpickle")

            logger.info(f"Running merge: {' '.join(command)}")
            logger.info(f"Output: {container_output}")
            
            # Execute in container
            self.runner.run_docker_task(
                self.image_name,
                command,
                volumes=volumes,
                gpus="all"
            )
            
            output_path = f"breeding_vat/data/merged_models/{output_name}"
            
            # Verify output
            if os.path.exists(output_path):
                logger.info(f"Merge successful: {output_path}")
                return output_path
            else:
                logger.error(f"Output not found: {output_path}")
                return None
        
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_moe_merge(self, models: List[str], output_name: str,
                     num_experts: Optional[int] = None,
                     router_weights: Optional[List[float]] = None) -> Optional[str]:
        """
        Run Mixture-of-Experts merge.
        
        Args:
            models: List of model paths/IDs
            output_name: Output model name
            num_experts: Number of experts (defaults to len(models))
            router_weights: Expert routing weights
            
        Returns:
            Output path if successful
        """
        if len(models) < 2:
            raise ValueError("MOE merge requires at least 2 models")
        
        config_path = self.create_config(
            "moe",
            models[0],
            models[1:],
            {"num_experts": num_experts or len(models)}
        )
        
        return self.run_merge(config_path, output_name)
    
    def _image_exists(self) -> bool:
        """Check if Mergekit Docker image exists."""
        result = subprocess.run(
            ["docker", "images", "-q", self.image_name],
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())


class MergekitWrapper:
    """
    Backward compatibility wrapper for existing code.
    Delegates to MergekitEngine.
    """
    
    def __init__(self, runner: TaskRunner, output_dir="breeding_vat/data/merged_models"):
        self.engine = MergekitEngine(runner, output_dir)
    
    def create_config(self, method: str, base_model: str, merge_models: List[str],
                     params: Optional[Dict] = None) -> str:
        """Create merge config."""
        return self.engine.create_config(method, base_model, merge_models, params)
    
    def run_merge(self, config_path: str, output_name: str) -> Optional[str]:
        """Run merge via Mergekit."""
        return self.engine.run_merge(config_path, output_name)
