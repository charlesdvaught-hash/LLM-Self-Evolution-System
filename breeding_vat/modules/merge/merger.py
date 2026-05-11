import yaml
import os
from breeding_vat.orchestrator.runner import TaskRunner

class MergeKitWrapper:
    def __init__(self, runner: TaskRunner, output_dir="breeding_vat/data/merged_models"):
        self.runner = runner
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_config(self, method, base_model, merge_models, params):
        resolved_models = []
        for m in merge_models:
            # Inside the merge container, data is at /app/data
            local_path = os.path.join("/app/data/merged_models", m)
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
        # We pass relative paths to the runner which will resolve them using HOST_PWD
        volumes = {
            "breeding_vat/configs": "/app/configs",
            "breeding_vat/data": "/app/data"
        }
        container_config = f"/app/configs/{os.path.basename(config_path)}"
        container_output = f"/app/data/merged_models/{output_name}"

        command = [container_config, container_output, "--cuda", "--lazy-unpickle"]
        self.runner.run_docker_task("vat-merge", command, volumes=volumes)
        return f"breeding_vat/data/merged_models/{output_name}"
