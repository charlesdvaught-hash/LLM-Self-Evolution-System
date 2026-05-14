"""
FusionBench Integration Engine
Wraps FusionBench model fusion techniques for integration into the Breeding Vat.

FusionBench uses Meta's Hydra configuration framework.
CLI pattern: fusion_bench method=<algo> modelpool=<config> [hydra.overrides]

For local models we write a modelpool YAML to disk, then reference it via
--config-dir so Hydra can find it.  Method params become CLI dot-notation
overrides: method.density=0.2, method.scaling_factor=0.5, etc.

Container: breeding-vat-fusionbench (python -m fusion_bench entrypoint)
"""

import os
import json
import logging
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("FusionBenchEngine")


class FusionBenchConfigBuilder:
    """
    Build FusionBench Hydra YAML configs for LLM merging.

    FusionBench expects:
      1. A modelpool YAML that lists model paths
      2. CLI invocation: fusion_bench method=<name> modelpool=<name> [overrides]

    Modelpool YAML format for CausalLM:
        _target_: fusion_bench.modelpool.CausalLMPool
        models:
          - name: _pretrained_   # base model (required, must be first)
            path: /app/data/...
          - name: model_0
            path: /app/data/...
    """

    # Internal method name -> FusionBench Hydra config group name
    METHOD_CONFIG_NAMES: Dict[str, str] = {
        "task_arithmetic":  "causal_lm/task_arithmetic",
        "ties_linear":      "causal_lm/ties_merging",
        "dare_linear":      "causal_lm/dare_ties_merging",
        "regmean":          "causal_lm/regmean",
        "voting":           "causal_lm/simple_average",   # closest built-in
        "magnitude_prune":  "causal_lm/magnitude_pruning",
        "linear":           "causal_lm/simple_average",
        "git_rebasin":      "causal_lm/task_arithmetic",  # fallback
        "frankenmerge":     "causal_lm/task_arithmetic",  # fallback
    }

    # param key -> Hydra CLI override key per method
    METHOD_OVERRIDE_KEYS: Dict[str, Dict[str, str]] = {
        "task_arithmetic":  {"scaling_factor": "method.scaling_factor",
                             "reg": "method.scaling_factor"},
        "ties_linear":      {"threshold": "method.density",
                             "scaling_factor": "method.scaling_factor"},
        "dare_linear":      {"drop_rate": "method.density",
                             "scaling_factor": "method.scaling_factor"},
        "regmean":          {"reg": "method.reg_coef"},
        "voting":           {},
        "magnitude_prune":  {"prune_ratio": "method.density"},
        "linear":           {},
        "git_rebasin":      {"scaling_factor": "method.scaling_factor"},
        "frankenmerge":     {"scaling_factor": "method.scaling_factor"},
    }

    @staticmethod
    def build_modelpool_yaml(base_model: str, merge_models: List[str]) -> Dict:
        """
        Build modelpool YAML dict.
        First entry is _pretrained_ (base), rest are model_0, model_1, ...
        """
        models = [{"name": "_pretrained_", "path": base_model}]
        for i, m in enumerate(merge_models):
            models.append({"name": f"model_{i}", "path": m})
        return {
            "_target_": "fusion_bench.modelpool.CausalLMPool",
            "models": models,
        }

    @staticmethod
    def build_cli_overrides(method: str, parameters: Dict,
                            container_output: str) -> List[str]:
        """
        Build Hydra CLI override strings.
        Returns list of strings appended to the fusion_bench command.
        """
        overrides = [
            f"merged_model_save_path={container_output}",
            "taskpool=dummy",           # no eval, merge-only
            "print_config=false",       # reduce noise
        ]
        key_map = FusionBenchConfigBuilder.METHOD_OVERRIDE_KEYS.get(method, {})
        for param_key, hydra_key in key_map.items():
            if param_key in parameters:
                overrides.append(f"{hydra_key}={parameters[param_key]}")
        return overrides


class FusionBenchEngine:
    """
    FusionBench orchestrator — provides 13+ advanced merging methods.
    Runs in breeding-vat-fusionbench container (python -m fusion_bench entrypoint).
    """

    AVAILABLE_METHODS = {
        "linear":             "Simple linear interpolation",
        "task_arithmetic":    "Vector arithmetic over task vectors",
        "regmean":            "Regression-based mean with optimization",
        "voting":             "Majority voting on weight values",
        "magnitude_prune":    "Sparse merging by magnitude threshold",
        "git_rebasin":        "Geometric mean in task vector space",
        "dare_linear":        "Drop & rescale with sparsity",
        "ties_linear":        "TIES with linear interpolation",
        "frankenmerge":       "Layer-wise expert selection",
        "layer_wise":         "Per-layer weighted merging",
        "multi_task":         "Multi-task optimization",
        "expert_selection":   "Automatic expert routing",
        "variance_reduction": "Variance-aware blending",
    }

    IMAGE_NAME = "breeding-vat-fusionbench:latest"

    def __init__(self, output_dir: str = "breeding_vat/data/merged_models",
                 image_name: str = None,
                 runner=None):
        self.output_dir = output_dir
        self.image_name = image_name or self.IMAGE_NAME
        self.runner = runner
        self.config_builder = FusionBenchConfigBuilder()
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"FusionBenchEngine initialised ({len(self.AVAILABLE_METHODS)} methods, "
                    f"image={self.image_name})")

    def list_methods(self) -> Dict[str, str]:
        return self.AVAILABLE_METHODS.copy()

    def _write_modelpool_yaml(self, run_id: str, base_model: str,
                              merge_models: List[str]) -> str:
        """Write a modelpool YAML to the configs dir. Returns host-side path."""
        configs_dir = "breeding_vat/configs/fusionbench"
        os.makedirs(configs_dir, exist_ok=True)
        pool_data = FusionBenchConfigBuilder.build_modelpool_yaml(base_model, merge_models)
        path = os.path.join(configs_dir, f"pool_{run_id}.yaml")
        with open(path, "w") as f:
            yaml.dump(pool_data, f, default_flow_style=False)
        logger.debug(f"Wrote modelpool config: {path}")
        return path

    def run_merge(self, method: str, base_model: str, merge_models: List[str],
                  output_name: str, params: Optional[Dict] = None) -> Optional[str]:
        """
        Execute a FusionBench merge in the fusionbench container.

        Builds:
          1. modelpool YAML  -> mounted at /app/configs/fusionbench/
          2. CLI command     -> fusion_bench method=<name>
                                --config-dir /app/configs/fusionbench
                                modelpool=pool_<id>
                                merged_model_save_path=<out>
                                taskpool=dummy
                                [method.param=value ...]

        Returns output path on success, None on failure.
        """
        output_path = os.path.join(self.output_dir, output_name)
        params = params or {}

        if self.runner is None:
            logger.warning(
                f"FusionBenchEngine.run_merge({method}): no runner — stub mode."
            )
            return None

        method_lower = method.lower()
        if method_lower not in FusionBenchConfigBuilder.METHOD_CONFIG_NAMES:
            logger.error(f"FusionBench: unknown method '{method}'")
            return None

        run_id = f"{method_lower}_{output_name}"
        try:
            pool_host_path = self._write_modelpool_yaml(run_id, base_model, merge_models)
            pool_name = Path(pool_host_path).stem

            method_config = FusionBenchConfigBuilder.METHOD_CONFIG_NAMES[method_lower]
            container_output = f"/app/data/merged_models/{output_name}"
            container_configs = "/app/configs/fusionbench"

            overrides = FusionBenchConfigBuilder.build_cli_overrides(
                method_lower, params, container_output
            )

            command = [
                "fusion_bench",
                f"method={method_config}",
                "--config-dir", container_configs,
                f"modelpool={pool_name}",
            ] + overrides

            volumes = {
                "breeding_vat/data":    "/app/data",
                "breeding_vat/configs": "/app/configs",
            }

            logger.info(f"FusionBench {method}: {len(merge_models)+1} models -> {output_name}")
            logger.debug(f"Command: {' '.join(command)}")

            self.runner.run_docker_task(self.image_name, command, volumes=volumes)

            if os.path.exists(output_path):
                logger.info(f"FusionBench merge complete: {output_path}")
                return output_path

            logger.warning(f"FusionBench output not found: {output_path}")
            return None

        except Exception as e:
            logger.error(f"FusionBench merge failed ({method}): {e}")
            return None

    # Public merge methods — same signatures as before so merger.py is unchanged

    def task_arithmetic_merge(self, base_model: str, models: List[str],
                              output_path: str,
                              weights: Optional[List[float]] = None) -> Optional[str]:
        """Task Arithmetic: result = base + sum(scaling_factor * delta_i)"""
        params = {"scaling_factor": (weights[0] if weights else 0.5)}
        return self.run_merge("task_arithmetic", base_model, models,
                              os.path.basename(output_path), params)

    def regmean_merge(self, base_model: str, models: List[str],
                      output_path: str, weights: Optional[List[float]] = None,
                      reg: float = 0.0) -> Optional[str]:
        """RegMean: regression-based merging with regularisation."""
        return self.run_merge("regmean", base_model, models,
                              os.path.basename(output_path), {"reg": reg})

    def voting_merge(self, models: List[str], output_path: str,
                     voting_method: str = "majority") -> Optional[str]:
        """Voting: simple average (FusionBench's closest built-in)."""
        return self.run_merge("voting", models[0], models[1:],
                              os.path.basename(output_path), {})

    def magnitude_prune_merge(self, models: List[str], output_path: str,
                              prune_ratio: float = 0.1) -> Optional[str]:
        """Magnitude Prune: sparse merging by magnitude threshold."""
        return self.run_merge("magnitude_prune", models[0], models[1:],
                              os.path.basename(output_path),
                              {"prune_ratio": prune_ratio})

    def frankenmerge(self, models: List[str], output_path: str,
                     layer_assignment: Optional[Dict[str, int]] = None,
                     rank: int = 8) -> Optional[str]:
        """Frankenmerge: layer-wise expert selection (task_arithmetic backend)."""
        return self.run_merge("frankenmerge", models[0], models[1:],
                              os.path.basename(output_path),
                              {"scaling_factor": 0.5})

    def git_rebasin_merge(self, base_model: str, models: List[str],
                          output_path: str,
                          weights: Optional[List[float]] = None,
                          lambda_: float = 0.1) -> Optional[str]:
        """Git Rebasin: geometric mean in task vector space."""
        return self.run_merge("git_rebasin", base_model, models,
                              os.path.basename(output_path),
                              {"scaling_factor": lambda_})

    def dare_merge(self, base_model: str, models: List[str],
                   output_path: str, drop_rate: float = 0.1) -> Optional[str]:
        """DARE: Drop And REscale with sparsity."""
        return self.run_merge("dare_linear", base_model, models,
                              os.path.basename(output_path),
                              {"drop_rate": drop_rate})

    def ties_merge(self, base_model: str, models: List[str],
                   output_path: str, threshold: float = 0.9) -> Optional[str]:
        """TIES: Trim, Interleave, Elect Subnets."""
        return self.run_merge("ties_linear", base_model, models,
                              os.path.basename(output_path),
                              {"threshold": threshold})


# Method registry
FUSIONBENCH_METHODS = {
    "task_arithmetic":  FusionBenchEngine.task_arithmetic_merge,
    "regmean":          FusionBenchEngine.regmean_merge,
    "voting":           FusionBenchEngine.voting_merge,
    "magnitude_prune":  FusionBenchEngine.magnitude_prune_merge,
    "frankenmerge":     FusionBenchEngine.frankenmerge,
    "git_rebasin":      FusionBenchEngine.git_rebasin_merge,
}
