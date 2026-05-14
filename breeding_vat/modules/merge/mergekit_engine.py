import subprocess
import os
import yaml
import logging
from typing import Dict, List, Optional
from breeding_vat.orchestrator.runner import TaskRunner

logger = logging.getLogger("MergekitEngine")

class MergekitConfigBuilder:
    @staticmethod
    def build_slerp_config(base_model: str, merge_models: List[str], weights: Optional[List[float]] = None) -> Dict:
        return {
            "merge_method": "slerp",
            "base_model": base_model,
            "parameters": {"t": weights[0] if weights else 0.5},
            "slices": [{"sources": [{"model": base_model, "layer_range": [0, 32]}, {"model": merge_models[0], "layer_range": [0, 32]}]}]
        }

    @staticmethod
    def build_ties_config(base_model: str, merge_models: List[str], weights: Optional[List[float]] = None, threshold: float = 0.9) -> Dict:
        return {
            "merge_method": "ties",
            "base_model": base_model,
            "parameters": {"density": threshold},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }

    @staticmethod
    def build_dare_config(base_model: str, merge_models: List[str], weights: Optional[List[float]] = None, drop_rate: float = 0.1) -> Dict:
        return {
            "merge_method": "dare_linear",
            "base_model": base_model,
            "parameters": {"drop_rate": drop_rate},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }

    @staticmethod
    def build_task_arithmetic_config(base_model: str, merge_models: List[str], weights: Optional[List[float]] = None) -> Dict:
        return {
            "merge_method": "task_arithmetic",
            "base_model": base_model,
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in merge_models]
        }

    @staticmethod
    def build_linear_config(base_model: str, merge_models: List[str], weights: Optional[List[float]] = None) -> Dict:
        return {
            "merge_method": "linear",
            "parameters": {"normalize": True},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }

    @staticmethod
    def build_moe_config(base_model: str, merge_models: List[str], num_experts: Optional[int] = None) -> Dict:
        return {
            "merge_method": "moe",
            "base_model": base_model,
            "experts": [{"source_model": m} for m in merge_models]
        }

    @staticmethod
    def apply_density(config: Dict, density: float) -> Dict:
        config.setdefault("parameters", {})["density"] = density
        return config

    @staticmethod
    def apply_module_filters(config: Dict, **kwargs) -> Dict:
        config["_filters"] = kwargs
        return config

    @staticmethod
    def apply_tokenizer_mode(config: Dict, mode: str) -> Dict:
        config["tokenizer_source"] = mode
        return config

    @staticmethod
    def apply_per_model_weights(config: Dict, weights: List[float]) -> Dict:
        if "models" in config:
            for i, w in enumerate(weights):
                if i < len(config["models"]):
                    config["models"][i].setdefault("parameters", {})["weight"] = w
        return config

    @staticmethod
    def apply_layerwise_alpha(config: Dict, curve: List[float], total: int) -> Dict:
        slices = []
        for alpha in curve:
            slices.append({"parameters": {"weight": alpha}})
        config["slices"] = slices
        return config

class MergekitEngine:
    def __init__(self, runner: TaskRunner, output_dir: str = "breeding_vat/data/merged_models", image_name: str = "breeding-vat-merge:latest"):
        self.runner = runner
        self.output_dir = output_dir
        self.image_name = image_name
        self.config_builder = MergekitConfigBuilder()
        self.config_hook = None
        os.makedirs(output_dir, exist_ok=True)

    def create_config(self, method: str, base_model: str, merge_models: List[str], params: Optional[Dict] = None) -> str:
        params = params or {}
        method_map = {
            "slerp": self.config_builder.build_slerp_config,
            "ties": self.config_builder.build_ties_config,
            "dare": self.config_builder.build_dare_config,
            "task_arithmetic": self.config_builder.build_task_arithmetic_config,
            "linear": self.config_builder.build_linear_config,
            "moe": self.config_builder.build_moe_config,
        }

        builder = method_map.get(method.lower(), self.config_builder.build_linear_config)

        # Adjust arguments based on builder
        if method.lower() in ["ties", "dare"]:
            config = builder(base_model, merge_models, params.get("weights"), params.get("threshold", params.get("drop_rate", 0.1)))
        elif method.lower() == "moe":
            config = builder(base_model, merge_models, params.get("num_experts"))
        else:
            config = builder(base_model, merge_models, params.get("weights"))

        if callable(self.config_hook):
            config = self.config_hook(config, method, base_model, merge_models) or config

        config_path = os.path.join("breeding_vat/configs", f"mergekit_{method}.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config_path

    def run_merge(self, config_path: str, output_name: str) -> Optional[str]:
        if not self.runner.image_exists(self.image_name):
            logger.error(f"Image {self.image_name} not found")
            return None

        volumes = {
            "breeding_vat/configs": "/app/configs",
            "breeding_vat/data": "/app/data",
            "scripts/mergekit_wrapper.py": "/app/scripts/mergekit_wrapper.py"
        }

        command = [
            "python", "/app/scripts/mergekit_wrapper.py",
            f"/app/configs/{os.path.basename(config_path)}",
            f"/app/data/merged_models/{output_name}",
            "--cuda", "--copy-tokenizer", "--lazy-unpickle"
        ]

        self.runner.run_docker_task(self.image_name, command, volumes=volumes)

        output_path = os.path.join(self.output_dir, output_name)
        return output_path if os.path.exists(output_path) else None

class MergekitWrapper:
    def __init__(self, runner: TaskRunner, output_dir: str = "breeding_vat/data/merged_models"):
        self.engine = MergekitEngine(runner, output_dir)
    def create_config(self, method: str, base: str, models: List[str], params: Optional[Dict] = None) -> str:
        return self.engine.create_config(method, base, models, params)
    def run_merge(self, path: str, name: str) -> Optional[str]:
        return self.engine.run_merge(path, name)
