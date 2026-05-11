import random
import time
import torch
import gc
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.merger import MergeKitWrapper

class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        self.merger = MergeKitWrapper()

    def cleanup_vram(self):
        """Forcefully clear VRAM and RAM."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def run_waterfall(self, base_models, goal, cycles, culling_rate):
        population = [{"name": m, "score": 0, "parent": None} for m in base_models]

        for cycle in range(cycles):
            print(f"--- Evolution Cycle {cycle + 1} ---")
            offspring = []

            for i in range(len(population)):
                for j in range(2):
                    child_name = f"mutant_c{cycle}_p{i}_o{j}"
                    recipe = f"Evolved from {population[i]['name']} using stochastic weight mutation."

                    # Log to DB
                    self.runner.log_model(child_name, [population[i]['name']], recipe, parent_id=None)

                    # Perform task (Simulated Docker run)
                    # In a real run, this would invoke the 'vat-merge' container
                    print(f"Creating mutant {child_name}...")

                    # Evaluate
                    score = self.evaluate(child_name)
                    offspring.append({"name": child_name, "score": score, "parent": population[i]['name']})

                    # Cleanup after each mutant to save VRAM
                    self.cleanup_vram()

            # Culling phase
            offspring.sort(key=lambda x: x['score'], reverse=True)
            num_to_keep = max(1, int(len(offspring) * (1 - culling_rate / 100)))
            population = offspring[:num_to_keep]

            print(f"Cycle {cycle+1} complete. Best mutant: {population[0]['name']} (Score: {population[0]['score']})")
            self.cleanup_vram()

        return population[0]

    def evaluate(self, model_name):
        # In reality, runs 'vat-eval' container
        return random.uniform(0.5, 0.95)
