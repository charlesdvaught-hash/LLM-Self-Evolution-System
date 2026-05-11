import yaml
import os
import torch
import torch.nn as nn
from breeding_vat.orchestrator.runner import TaskRunner

class MergeKitWrapper:
    def __init__(self, runner: TaskRunner, output_dir="breeding_vat/data/merged_models"):
        self.runner = runner
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_config(self, method, base_model, merge_models, params):
        config = {
            "merge_method": method,
            "base_model": base_model,
            "models": [
                {"model": m, "parameters": params.get(m, {})} for m in merge_models
            ],
            "dtype": "float16",
        }
        config_path = os.path.join("breeding_vat/configs", f"merge_{method}.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def run_merge(self, config_path, output_name):
        output_path = os.path.join(self.output_dir, output_name)
        volumes = {
            os.path.abspath("breeding_vat/configs"): "/app/configs",
            os.path.abspath("breeding_vat/data"): "/app/data"
        }
        container_config = f"/app/configs/{os.path.basename(config_path)}"
        container_output = f"/app/data/merged_models/{output_name}"

        command = [container_config, container_output, "--cuda", "--lazy-unpickle"]
        self.runner.run_docker_task("vat-merge", command, volumes=volumes)
        return output_path

class AdvancedMerger:
    @staticmethod
    def rmm_merge(model_weights: list[torch.Tensor], rank=16):
        stacked = torch.stack(model_weights)
        U, S, V = torch.svd(stacked)
        merged_weights = torch.mm(U[:, :rank], torch.mm(torch.diag(S[:rank]), V[:, :rank].t()))
        return merged_weights.mean(dim=0)

    @staticmethod
    def neg_merge(base_weights: torch.Tensor, task_vectors: list[torch.Tensor]):
        stacked_tasks = torch.stack(task_vectors)
        consensus_sign = torch.sign(stacked_tasks.sum(dim=0))
        mask = (torch.sign(stacked_tasks) == consensus_sign).all(dim=0)
        final_vector = stacked_tasks.mean(dim=0) * mask
        return base_weights - final_vector

    @staticmethod
    def franken_moe(expert_weights: list[dict], gate_weights: torch.Tensor):
        config = {
            "type": "moe",
            "experts": len(expert_weights),
            "layers": [{"expert_index": i, "weight_ref": f"expert_{i}"} for i in range(len(expert_weights))],
            "router": "top-k"
        }
        return config

    def run_advanced_merge_task(self, method, models, output_name):
        """
        Placeholder for executing advanced math-heavy merges.
        These could either be run on the host (if small) or in a dedicated 'vat-sae' container.
        """
        print(f"Running advanced merge task: {method} for {output_name}")
        # In reality, this would perform the SVD or NegMerge operations on the loaded tensors
        return f"breeding_vat/data/merged_models/{output_name}"
