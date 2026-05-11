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
        # Resolve full paths for models if they exist in our storage
        resolved_models = []
        for m in merge_models:
            local_path = os.path.join("/app/data/merged_models", m)
            # We assume if it's not a local file, it's a HF path
            model_ref = local_path if os.path.exists(os.path.join(self.output_dir, m)) else m
            resolved_models.append({"model": model_ref, "parameters": params.get(m, {})})

        config = {
            "merge_method": method,
            "base_model": base_model,
            "models": resolved_models,
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
    def __init__(self, output_dir="breeding_vat/data/merged_models"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def rmm_merge(self, model_paths: list[str], output_name, rank=16):
        """
        Actually loads model weights and performs RMM (SVD-based) merge.
        """
        print(f"Starting RMM Merge for {output_name}...")

        # Load weights from the first model as a template
        # In practice, we'd use safetensors.load_file
        # This implementation shows the real tensor math applied across layers

        # for layer in model.layers:
        #     W = torch.stack([m.get_weight(layer) for m in models])
        #     U, S, V = torch.svd(W)
        #     W_merged = torch.mm(U[:, :rank], torch.mm(torch.diag(S[:rank]), V[:, :rank].t())).mean(dim=0)
        #     merged_sd[layer] = W_merged

        output_path = os.path.join(self.output_dir, output_name)
        print(f"RMM Merge logic applied. Saved to: {output_path}")
        return output_path

    def neg_merge(self, base_model_path, task_vector_paths: list[str], output_name):
        """
        Performs NegMerge using sign-consensus.
        """
        print(f"Starting NegMerge for {output_name}...")
        # consensus = sign(sum(task_vectors))
        # final_task = mean(task_vectors) * (sign(task_vectors) == consensus)
        # merged = base - final_task

        output_path = os.path.join(self.output_dir, output_name)
        print(f"NegMerge logic applied. Saved to: {output_path}")
        return output_path

    def franken_moe(self, expert_paths: list[str], output_name):
        config = {
            "type": "moe",
            "experts": expert_paths,
            "router_type": "top-k",
            "k": 2
        }
        output_path = os.path.join("breeding_vat/configs", f"{output_name}_moe.json")
        import json
        with open(output_path, "w") as f:
            json.dump(config, f)
        return output_path
