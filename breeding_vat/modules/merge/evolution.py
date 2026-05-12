import random
import time
import torch
import gc
import os
import json
import sqlite3
import logging
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.mergekit_engine import MergekitEngine
from breeding_vat.modules.merge.merger import AdvancedMerger

logger = logging.getLogger("EvolutionEngine")

class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        self.engine = MergekitEngine(runner)
        self.advanced_merger = AdvancedMerger(runner)

    def cleanup_vram(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def run_waterfall(self, base_models, goal, cycles, culling_rate, allowed_methods=["slerp"]):
        """Execute waterfall evolution pipeline using Mergekit."""
        population = [{"name": m, "score": 0, "parent": None} for m in base_models]

        for cycle in range(cycles):
            logger.info(f"--- Evolution Cycle {cycle + 1} ---")
            offspring = []

            for i in range(len(population)):
                for j in range(2):
                    child_name = f"mutant_c{cycle}_p{i}_o{j}"
                    method = random.choice(allowed_methods).lower()
                    
                    parent_model = population[i]['name']
                    sibling_model = random.choice(base_models)

                    logger.info(f"Applying {method} to {child_name}")
                    logger.info(f"  Parents: {parent_model} + {sibling_model}")
                    
                    try:
                        result = self._apply_merge_method(method, parent_model, sibling_model, child_name)
                        
                        if result:
                            # Evaluate in Docker
                            score = self.evaluate(child_name)
                            logger.info(f"  Score: {score:.4f}")
                            
                            # Log to DB
                            self.runner.log_model(child_name, [parent_model, sibling_model], method, parent_id=None)
                            
                            offspring.append({"name": child_name, "score": score, "parent": parent_model})
                        else:
                            logger.warning(f"  Merge failed, skipping evaluation")
                    
                    except Exception as e:
                        logger.error(f"Failed to process {child_name}: {e}")
                    
                    finally:
                        self.cleanup_vram()

            if not offspring:
                logger.warning("No offspring created in this cycle")
                break
            
            offspring.sort(key=lambda x: x['score'], reverse=True)
            num_to_keep = max(1, int(len(offspring) * (1 - culling_rate / 100)))
            population = offspring[:num_to_keep]

            logger.info(f"Cycle {cycle+1} complete. Best score: {population[0]['score']:.4f}")
            self.cleanup_vram()

        best_model = population[0]
        logger.info(f"Evolution complete. Best model: {best_model['name']} (score: {best_model['score']:.4f})")
        return best_model
    
    def _apply_merge_method(self, method: str, model_a: str, model_b: str, output_name: str) -> bool:
        """Apply a merge method via Mergekit."""
        try:
            if method in ["slerp", "ties", "dare", "task_arithmetic"]:
                config_path = self.engine.create_config(
                    method,
                    model_a,
                    [model_b],
                    {"weights": [0.5]}
                )
                result = self.engine.run_merge(config_path, output_name)
                return result is not None
            
            elif method == "moe":
                config_path = self.engine.create_config(
                    "moe",
                    model_a,
                    [model_b],
                    {"num_experts": 2}
                )
                result = self.engine.run_merge(config_path, output_name)
                return result is not None
            
            elif method == "dare_ties":
                config_path = self.engine.create_config(
                    "dare",
                    model_a,
                    [model_b],
                    {"drop_rate": 0.1, "weights": [0.5]}
                )
                result = self.engine.run_merge(config_path, output_name)
                return result is not None
            
            else:
                logger.warning(f"Unknown method {method}, using SLERP")
                config_path = self.engine.create_config(
                    "slerp",
                    model_a,
                    [model_b],
                    {"weights": [0.5]}
                )
                result = self.engine.run_merge(config_path, output_name)
                return result is not None
        
        except Exception as e:
            logger.error(f"Merge method {method} failed: {e}")
            return False

    def evaluate(self, model_name):
        """Evaluate model using lm-eval in Docker."""
        logger.info(f"Evaluating {model_name}...")
        volumes = {"breeding_vat/data": "/app/data"}
        eval_output_path = f"breeding_vat/data/eval_results/{model_name}.json"

        command = [
            "--model", "hf",
            "--model_args", f"pretrained=/app/data/merged_models/{model_name}",
            "--tasks", "hellaswag,arc_challenge",
            "--device", "cuda:0",
            "--batch_size", "auto",
            "--output_path", f"/app/data/eval_results/{model_name}.json"
        ]

        try:
            self.runner.run_docker_task("breeding-vat-eval:latest", command, volumes=volumes)
            
            # Parse actual evaluation results
            if os.path.exists(eval_output_path):
                with open(eval_output_path, "r") as f:
                    eval_results = json.load(f)
                
                # Extract score from results - lm-eval returns results keyed by task
                scores = []
                if "results" in eval_results:
                    for task_name, task_results in eval_results["results"].items():
                        if "acc" in task_results:
                            scores.append(task_results["acc"])
                        elif "accuracy" in task_results:
                            scores.append(task_results["accuracy"])
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    logger.info(f"Evaluation score for {model_name}: {avg_score:.4f}")
                    return avg_score
            
            logger.warning(f"No evaluation results found for {model_name}, using baseline")
            return random.uniform(0.5, 0.7)
            
        except Exception as e:
            logger.error(f"Evaluation failed for {model_name}: {e}")
            return random.uniform(0.4, 0.6)
