import os
import json
import logging
from typing import Tuple

logger = logging.getLogger("SCOPEFilter")

# Script runs inside the breeding-vat-eval Docker container
_SCOPE_SCRIPT = r"""
import sys, json, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path, verdict_path = sys.argv[1], sys.argv[2]

TEST_PROMPTS = [
    "The capital of France is",
    "2 + 2 = ",
    "Hello, my name is",
]

try:
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto"
    )
    model.eval()

    coherent_count = 0
    outputs = []

    for prompt in TEST_PROMPTS:
        try:
            inputs = tok(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out_ids = model.generate(
                    **inputs,
                    max_new_tokens=15,
                    do_sample=False,
                    pad_token_id=tok.eos_token_id,
                )
            text = tok.decode(out_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            outputs.append(text.strip())
            # Coherence: non-empty, more than one unique word (rules out <eos><eos><eos>...)
            if text.strip() and len(set(text.split())) > 1:
                coherent_count += 1
        except Exception as e:
            outputs.append(f"ERROR: {e}")

    passed = coherent_count >= 2
    result = {
        "passed": passed,
        "coherent_count": coherent_count,
        "total": len(TEST_PROMPTS),
        "outputs": outputs,
        "reason": f"{coherent_count}/{len(TEST_PROMPTS)} prompts produced coherent output",
    }

except Exception as e:
    result = {
        "passed": False,
        "coherent_count": 0,
        "total": len(TEST_PROMPTS),
        "outputs": [],
        "reason": f"Model load failed: {e}",
    }

with open(verdict_path, "w") as f:
    json.dump(result, f)
"""


class SCOPEFilter:
    """
    Lightweight pre-filter that runs merged models through basic coherence checks
    before the expensive lm-eval Docker job.

    Catches obviously broken merges (crashes, all-<eos> output, infinite repetition)
    in seconds instead of minutes.

    Enable via EvolutionEngine.scope_filter = SCOPEFilter(runner).
    """

    def __init__(self, runner):
        self.runner = runner

    def check(self, model_name: str) -> Tuple[bool, str]:
        """
        Spin up a container, run three test prompts, return (passed, reason).
        Defaults to True (pass) on any infra error so we never silently skip good models.
        """
        eval_dir = "breeding_vat/data/eval_results"
        os.makedirs(eval_dir, exist_ok=True)

        script_host = os.path.join("breeding_vat/modules/benchmark/scripts", "_scope_check.py")
        verdict_host = os.path.join(eval_dir, f"{model_name}_scope.json")

        script_container = "/app/modules/benchmark/scripts/_scope_check.py"
        verdict_container = f"/app/data/eval_results/{model_name}_scope.json"
        model_container = f"/app/data/merged_models/{model_name}"

        try:
            os.makedirs(os.path.dirname(script_host), exist_ok=True)
            with open(script_host, "w") as f:
                f.write(_SCOPE_SCRIPT)

            volumes = {
                "breeding_vat/data": "/app/data",
                "breeding_vat/modules/benchmark/scripts": "/app/modules/benchmark/scripts"
            }
            command = ["python", script_container, model_container, verdict_container]

            self.runner.run_docker_task("breeding-vat-eval:latest", command, volumes=volumes)

            if os.path.exists(verdict_host):
                with open(verdict_host) as f:
                    v = json.load(f)
                passed = v.get("passed", True)
                reason = v.get("reason", "check complete")
                logger.info(f"SCOPE [{model_name}]: {'PASS' if passed else 'FAIL'} — {reason}")
                return passed, reason

            if not self.runner.simulation_mode:
                logger.error(f"SCOPE verdict missing for {model_name} - Infrastructure failure")
                return False, "verdict missing (Infrastructure failure)"

            logger.warning(f"SCOPE verdict missing for {model_name}, defaulting to pass (Simulation)")
            return True, "verdict missing (defaulting to pass)"

        except Exception as e:
            logger.error(f"SCOPE check error for {model_name}: {e}")
            if not self.runner.simulation_mode:
                return False, f"Infrastructure error: {e}"
            return True, f"infra error ({e}), defaulting to pass"
