import subprocess
import os
import yaml
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("MergekitEngine")

class MergekitConfigBuilder:
    @staticmethod
    def build_slerp_config(base_model, merge_models, weights=None):
        return {
            "merge_method": "slerp",
            "base_model": base_model,
            "parameters": {"t": weights[0] if weights else 0.5},
            "slices": [{"sources": [{"model": base_model, "layer_range": [0, 32]}, {"model": merge_models[0], "layer_range": [0, 32]}]}]
        }
    @staticmethod
    def build_ties_config(base_model, merge_models, weights=None, threshold=0.9):
        return {
            "merge_method": "ties",
            "base_model": base_model,
            "parameters": {"density": threshold},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }
    @staticmethod
    def build_dare_config(base_model, merge_models, weights=None, drop_rate=0.1):
        return {
            "merge_method": "dare_linear",
            "base_model": base_model,
            "parameters": {"drop_rate": drop_rate},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }
    @staticmethod
    def build_task_arithmetic_config(base_model, merge_models, weights=None):
        return {
            "merge_method": "task_arithmetic",
            "base_model": base_model,
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in merge_models]
        }
    @staticmethod
    def build_linear_config(base_model, merge_models, weights=None):
        return {
            "merge_method": "linear",
            "parameters": {"normalize": True},
            "models": [{"model": m, "parameters": {"weight": 1.0}} for m in [base_model] + merge_models]
        }
    @staticmethod
    def build_moe_config(base_model, merge_models, num_experts=None):
        return {
            "merge_method": "moe",
            "base_model": base_model,
            "experts": [{"source_model": m} for m in merge_models]
        }

    @staticmethod
    def apply_density(config, density):
        config.setdefault("parameters", {})["density"] = density
        return config
    @staticmethod
    def apply_module_filters(config, **kwargs):
        config["_filters"] = kwargs
        return config
    @staticmethod
    def apply_tokenizer_mode(config, mode):
        config["tokenizer_source"] = mode
        return config
    @staticmethod
    def apply_per_model_weights(config, weights):
        for i, w in enumerate(weights):
            if i < len(config.get("models", [])):
                config["models"][i]["parameters"]["weight"] = w
        return config
    @staticmethod
    def apply_layerwise_alpha(config, curve, total):
        slices = []
        for alpha in curve:
            slices.append({"parameters": {"weight": alpha}})
        config["slices"] = slices
        return config

class MergekitEngine:
    def __init__(self, runner, output_dir="breeding_vat/data/merged_models", image_name="breeding-vat-merge:latest"):
        self.runner = runner
        self.output_dir = output_dir
        self.image_name = image_name
        self.config_builder = MergekitConfigBuilder()
        self.config_hook = None
        os.makedirs(output_dir, exist_ok=True)
    def create_config(self, method, base, merge_models, params=None):
        params = params or {}
        if method == "slerp": config = self.config_builder.build_slerp_config(base, merge_models, params.get("weights"))
        elif method == "ties": config = self.config_builder.build_ties_config(base, merge_models, params.get("weights"), params.get("threshold", 0.9))
        elif method == "dare": config = self.config_builder.build_dare_config(base, merge_models, params.get("weights"), params.get("drop_rate", 0.1))
        elif method == "task_arithmetic": config = self.config_builder.build_task_arithmetic_config(base, merge_models, params.get("weights"))
        elif method == "linear": config = self.config_builder.build_linear_config(base, merge_models, params.get("weights"))
        elif method == "moe": config = self.config_builder.build_moe_config(base, merge_models, params.get("num_experts"))
        else: config = self.config_builder.build_linear_config(base, merge_models)
        if callable(self.config_hook):
             config = self.config_hook(config, method, base, merge_models) or config
        p = os.path.join("breeding_vat/configs", f"mergekit_{method}.yaml")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w') as f: yaml.dump(config, f)
        return p
    def run_merge(self, config_path, output_name):
        if not self.runner.image_exists(self.image_name): return None
        v = {"breeding_vat/configs": "/app/configs", "breeding_vat/data": "/app/data", "scripts/mergekit_wrapper.py": "/app/scripts/mergekit_wrapper.py"}
        # Use python scripts/mergekit_wrapper.py instead of mergekit-yaml directly
        c = ["python", "/app/scripts/mergekit_wrapper.py", f"/app/configs/{os.path.basename(config_path)}", f"/app/data/merged_models/{output_name}", "--cuda", "--copy-tokenizer"]
        self.runner.run_docker_task(self.image_name, c, volumes=v)
        o = os.path.join(self.output_dir, output_name)
        return o if os.path.exists(o) else None

class MergekitWrapper:
    def __init__(self, runner, output_dir="breeding_vat/data/merged_models"):
        self.engine = MergekitEngine(runner, output_dir)
    def create_config(self, m, b, ms, p=None): return self.engine.create_config(m, b, ms, p)
    def run_merge(self, p, n): return self.engine.run_merge(p, n)
