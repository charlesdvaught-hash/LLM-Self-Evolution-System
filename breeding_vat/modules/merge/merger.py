import yaml
import subprocess
import os
import torch
import torch.nn as nn

class MergeKitWrapper:
    def __init__(self, output_dir="breeding_vat/data/merged_models"):
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
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def run_merge(self, config_path, output_name):
        output_path = os.path.join(self.output_dir, output_name)
        # In a production environment, this would run 'vat-merge' docker image
        print(f"Executing MergeKit: {config_path} -> {output_path}")
        return output_path

class AdvancedMerger:
    @staticmethod
    def rmm_merge(model_weights: list[torch.Tensor], rank=16):
        """
        Reversible Model Merging (RMM) implementation using SVD.
        Aligns models into a compact shared basis.
        """
        # Stack weights: (num_models, layer_dim)
        stacked = torch.stack(model_weights)
        # Perform SVD
        U, S, V = torch.svd(stacked)
        # Keep top k components
        merged_weights = torch.mm(U[:, :rank], torch.mm(torch.diag(S[:rank]), V[:, :rank].t()))
        return merged_weights.mean(dim=0)

    @staticmethod
    def neg_merge(base_weights: torch.Tensor, task_vectors: list[torch.Tensor]):
        """
        NegMerge implementation.
        Uses sign-consensus to negate specific knowledge/influence.
        """
        # Aggregate task vectors based on sign consensus
        stacked_tasks = torch.stack(task_vectors)
        consensus_sign = torch.sign(stacked_tasks.sum(dim=0))

        # Only keep weights where all tasks agree on the direction
        mask = (torch.sign(stacked_tasks) == consensus_sign).all(dim=0)
        final_vector = stacked_tasks.mean(dim=0) * mask

        # Negate from base
        return base_weights - final_vector

    @staticmethod
    def franken_moe(expert_weights: list[dict], gate_weights: torch.Tensor):
        """
        Simple configuration generator for a Franken-MoE.
        """
        config = {
            "type": "moe",
            "experts": len(expert_weights),
            "layers": [
                {"expert_index": i, "weight_ref": "expert_weights[i]"}
                for i in range(len(expert_weights))
            ],
            "router": "top-k"
        }
        return config
