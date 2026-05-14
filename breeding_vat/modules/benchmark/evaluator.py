"""
Tiered benchmark evaluator.

Tier 0 — Perplexity check (~15s):  catches completely broken merges fast.
Tier 1 — Fast tasks     (~2 min):  arc_easy; quick sanity on real tasks.
Tier 2 — Standard tasks (~10 min): hellaswag + arc_challenge; default.
Tier 3 — Full suite     (~30 min): + winogrande + truthfulqa_mc.

All evaluation runs inside Docker (breeding-vat-eval:latest).
Results are logged to ExperimentDatabase for MethodPredictor to learn from.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from breeding_vat.modules.benchmark.prediction_engine import ExperimentDatabase

logger = logging.getLogger("BenchmarkEvaluator")

# Tier definitions — tasks passed directly to lm-eval --tasks
TIERS = {
    "fast":     ["arc_easy"],
    "standard": ["hellaswag", "arc_challenge"],
    "full":     ["hellaswag", "arc_challenge", "winogrande", "truthfulqa_mc"],
}

# Perplexity threshold: anything above this is considered a broken merge
PERPLEXITY_FAIL_THRESHOLD = 1000.0

# Embedded script that runs inside the Docker eval container
_PERPLEXITY_SCRIPT = r"""
import sys, json, math, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path, output_path = sys.argv[1], sys.argv[2]

try:
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto"
    )
    model.eval()

    # Simple in-memory test corpus so we don't need datasets lib
    texts = [
        "The quick brown fox jumps over the lazy dog and runs away.",
        "Machine learning models are trained on large datasets to learn patterns.",
        "The capital of France is Paris, a city famous for the Eiffel Tower.",
        "In mathematics, a prime number is divisible only by one and itself.",
        "Python is a high-level programming language known for its readability.",
        "The human brain contains approximately 86 billion neurons connected by synapses.",
        "Climate change is driven primarily by greenhouse gas emissions from human activity.",
        "The speed of light in a vacuum is approximately 299,792 kilometres per second.",
        "Natural language processing enables computers to understand and generate text.",
        "Photosynthesis converts carbon dioxide and water into glucose using sunlight.",
    ] * 5  # 50 samples

    total_loss, n = 0.0, 0
    for text in texts:
        try:
            inputs = tok(
                text, return_tensors="pt", max_length=256, truncation=True
            ).to(model.device)
            with torch.no_grad():
                loss = model(**inputs, labels=inputs["input_ids"]).loss.item()
            if not (math.isnan(loss) or math.isinf(loss)):
                total_loss += loss
                n += 1
        except Exception:
            pass

    if n == 0:
        result = {"perplexity": 9999.0, "passed": False, "samples": 0,
                  "reason": "all samples failed"}
    else:
        ppl = math.exp(total_loss / n)
        result = {
            "perplexity": round(ppl, 2),
            "passed": ppl < """ + str(PERPLEXITY_FAIL_THRESHOLD) + r""",
            "samples": n,
            "reason": f"perplexity={ppl:.1f}",
        }

except Exception as e:
    result = {"perplexity": 9999.0, "passed": False, "samples": 0,
              "reason": f"model load failed: {e}"}

with open(output_path, "w") as f:
    json.dump(result, f)
"""


class BenchmarkEvaluator:
    """
    Runs tiered evaluation for every merged model and logs results to
    ExperimentDatabase so MethodPredictor can learn over time.

    Usage:
        ev = BenchmarkEvaluator(runner)
        results = ev.evaluate(model_name, experiment_id=exp_id,
                              tier="standard", skip_perplexity=False)
        # Returns dict with score, perplexity, per-task scores, anomalies
    """

    def __init__(self, runner, db_path: str = "breeding_vat/data/experiments.db"):
        self.runner = runner
        self.db = ExperimentDatabase(db_path)
        self.eval_dir = "breeding_vat/data/eval_results"
        os.makedirs(self.eval_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Tier 0: perplexity
    # ------------------------------------------------------------------

    def run_perplexity(self, model_name: str) -> Tuple[bool, float, str]:
        """
        Run fast perplexity check in Docker.
        Returns (passed, perplexity, reason).
        Defaults to (True, 0.0, "skipped") on infra failure so we never
        silently block good models.
        """
        script_host = os.path.join(self.eval_dir, "_ppl_check.py")
        verdict_host = os.path.join(self.eval_dir, f"{model_name}_ppl.json")
        script_ctr = "/app/data/eval_results/_ppl_check.py"
        verdict_ctr = f"/app/data/eval_results/{model_name}_ppl.json"
        model_ctr = f"/app/data/merged_models/{model_name}"

        try:
            with open(script_host, "w") as f:
                f.write(_PERPLEXITY_SCRIPT)

            self.runner.run_docker_task(
                "breeding-vat-eval:latest",
                ["python", script_ctr, model_ctr, verdict_ctr],
                volumes={"breeding_vat/data": "/app/data"},
                gpus="all",
            )

            if os.path.exists(verdict_host):
                v = json.load(open(verdict_host))
                return v["passed"], v["perplexity"], v["reason"]

        except Exception as e:
            logger.error(f"Perplexity check failed for {model_name}: {e}")

        return True, 0.0, "check skipped (infra error)"

    # ------------------------------------------------------------------
    # Tier 1-3: lm-eval
    # ------------------------------------------------------------------

    def run_lm_eval(self, model_name: str, tier: str = "standard") -> Dict[str, float]:
        """
        Run lm-eval benchmark tasks in Docker.
        Returns {task_name: accuracy} or {} on failure.
        """
        tasks = TIERS.get(tier, TIERS["standard"])
        tasks_str = ",".join(tasks)
        output_host = os.path.join(self.eval_dir, f"{model_name}.json")
        output_ctr = f"/app/data/eval_results/{model_name}.json"
        model_ctr = f"/app/data/merged_models/{model_name}"

        command = [
            "--model", "hf",
            "--model_args", f"pretrained={model_ctr}",
            "--tasks", tasks_str,
            "--device", "cuda:0",
            "--batch_size", "auto",
            "--output_path", output_ctr,
        ]

        try:
            self.runner.run_docker_task(
                "breeding-vat-eval:latest", command,
                volumes={"breeding_vat/data": "/app/data"},
                gpus="all",
            )
        except Exception as e:
            logger.error(f"lm-eval failed for {model_name}: {e}")
            return {}

        if not os.path.exists(output_host):
            logger.warning(f"lm-eval output missing: {output_host}")
            return {}

        try:
            data = json.load(open(output_host))
            scores = {}
            for task, result in data.get("results", {}).items():
                for key in ("acc,none", "acc", "accuracy"):
                    if key in result:
                        scores[task] = float(result[key])
                        break
            return scores
        except Exception as e:
            logger.error(f"Score parse failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Combined tiered entrypoint
    # ------------------------------------------------------------------

    def evaluate(
        self,
        model_name: str,
        experiment_id: Optional[int] = None,
        tier: str = "standard",
        skip_perplexity: bool = False,
    ) -> Dict:
        """
        Full tiered evaluation with anomaly detection.

        Returns dict:
        {
            "score": 0.748,              # composite score (0-1)
            "perplexity": 8.234,
            "arc_easy": 0.612,
            "arc_challenge": 0.751,
            "hellaswag": 0.740,
            "raw_scores": {...},
            "anomalies": [
                {"type": "specialization", "detail": "..."},
                {"type": "high_perplexity", "detail": "..."}
            ],
            "timestamp": "2025-01-15T..."
        }
        """
        result = {
            "score": 0.0,
            "perplexity": None,
            "arc_easy": None,
            "arc_challenge": None,
            "hellaswag": None,
            "winogrande": None,
            "truthfulqa_mc": None,
            "raw_scores": {},
            "anomalies": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # --- Tier 0: Perplexity ---
        if not skip_perplexity:
            passed, ppl, reason = self.run_perplexity(model_name)
            result["perplexity"] = ppl
            logger.info(f"Perplexity [{model_name}]: {ppl:.1f} — {reason}")
            if not passed:
                logger.warning(f"Perplexity gate FAILED for {model_name} — skipping lm-eval")
                result["anomalies"].append({
                    "type": "perplexity_fail",
                    "detail": f"Perplexity {ppl:.1f} exceeds threshold {PERPLEXITY_FAIL_THRESHOLD}"
                })
                if experiment_id is not None:
                    self.db.log_scores(experiment_id, {"perplexity_fail": 0.0})
                return result

        # --- Tier 1-3: lm-eval ---
        scores = self.run_lm_eval(model_name, tier=tier)
        result["raw_scores"] = scores

        if not scores:
            logger.warning(f"No scores returned for {model_name}")
            result["anomalies"].append({
                "type": "eval_failure",
                "detail": "lm-eval returned no results"
            })
            return result

        # Extract per-task scores
        result["arc_easy"] = scores.get("arc_easy")
        result["arc_challenge"] = scores.get("arc_challenge")
        result["hellaswag"] = scores.get("hellaswag")
        result["winogrande"] = scores.get("winogrande")
        result["truthfulqa_mc"] = scores.get("truthfulqa_mc")

        # --- Anomaly Detection ---
        # Check for task disparity (possible specialization or degradation)
        if result.get("arc_challenge") is not None and result.get("arc_easy") is not None:
            diff = result["arc_challenge"] - result["arc_easy"]
            if diff > 0.2:  # Significant gap
                result["anomalies"].append({
                    "type": "specialization",
                    "detail": f"arc_challenge ({result['arc_challenge']:.3f}) >> arc_easy ({result['arc_easy']:.3f}) — possible specialization or degradation"
                })
        
        # Check for perplexity stability (if we have it)
        if result["perplexity"] and result["perplexity"] > 500:
            result["anomalies"].append({
                "type": "high_perplexity",
                "detail": f"Perplexity {result['perplexity']:.1f} is elevated — possible structural damage"
            })
        
        # --- Composite Score ---
        valid_scores = [s for s in [result.get("arc_easy"), result.get("arc_challenge"), 
                                     result.get("hellaswag")] if s is not None]
        if valid_scores:
            result["score"] = sum(valid_scores) / len(valid_scores)
        else:
            result["score"] = 0.0

        logger.info(f"Benchmark [{model_name}] tier={tier}: scores={scores} → composite={result['score']:.4f}")
        
        if result["anomalies"]:
            logger.warning(f"  Anomalies detected: {[a['type'] for a in result['anomalies']]}")

        if experiment_id is not None:
            self.db.log_scores(experiment_id, scores)

        return result
