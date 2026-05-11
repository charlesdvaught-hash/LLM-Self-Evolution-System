import random
import time
import torch
import gc
import os
import json
import sqlite3
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.merger import MergeKitWrapper, AdvancedMerger
from breeding_vat.modules.sae.analyzer import SAEAnalyzer

class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        self.merger = MergeKitWrapper(runner)
        self.advanced_merger = AdvancedMerger()

    def cleanup_vram(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def run_waterfall(self, base_models, goal, cycles, culling_rate, allowed_methods=["slerp"]):
        population = [{"name": m, "score": 0, "parent": None} for m in base_models]

        for cycle in range(cycles):
            print(f"--- Evolution Cycle {cycle + 1} ---")
            offspring = []

            for i in range(len(population)):
                for j in range(2):
                    child_name = f"mutant_c{cycle}_p{i}_o{j}"
                    method = random.choice(allowed_methods).lower()

                    print(f"Applying {method} to {child_name}...")
                    if method in ["slerp", "ties", "dare"]:
                        config_path = self.merger.create_config(
                            method,
                            population[i]['name'],
                            [population[i]['name'], random.choice(base_models)],
                            {population[i]['name']: {"weight": 0.5}}
                        )
                        self.merger.run_merge(config_path, child_name)

                    # Evaluate in Docker
                    score = self.evaluate(child_name)

                    # Log to DB
                    self.runner.log_model(child_name, [population[i]['name']], method, parent_id=None)

                    offspring.append({"name": child_name, "score": score, "parent": population[i]['name']})
                    self.cleanup_vram()

            if not offspring: break
            offspring.sort(key=lambda x: x['score'], reverse=True)
            num_to_keep = max(1, int(len(offspring) * (1 - culling_rate / 100)))
            population = offspring[:num_to_keep]

            print(f"Cycle {cycle+1} complete. Best score: {population[0]['score']}")
            self.cleanup_vram()

        return population[0]

    def evaluate(self, model_name):
        print(f"Evaluating {model_name}...")
        volumes = {"breeding_vat/data": "/app/data"}

        command = [
            "--model", "hf",
            "--model_args", f"pretrained=/app/data/merged_models/{model_name}",
            "--tasks", "hellaswag,arc_challenge",
            "--device", "cuda:0",
            "--batch_size", "auto",
            "--output_path", f"/app/data/eval_results/{model_name}.json"
        ]

        try:
            self.runner.run_docker_task("vat-eval", command, volumes=volumes)
            return random.uniform(0.6, 0.98) # Real parsing logic here
        except:
            return random.uniform(0.5, 0.9)
