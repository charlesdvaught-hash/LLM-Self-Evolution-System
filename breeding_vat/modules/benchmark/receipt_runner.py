import os
import json
import logging
import random
from typing import Optional, Callable
from datasets import Dataset

logger = logging.getLogger(__name__)

CHANCE_LEVEL = 0.25
JSONL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "benchmark", "general_benchmark.jsonl"
)


def chance_corrected_score(n_correct: int, n_attempted: int) -> float:
    if n_attempted == 0:
        return 0.0
    raw = n_correct / n_attempted
    return round(max(0.0, (raw - CHANCE_LEVEL) / (1 - CHANCE_LEVEL)) * 100, 2)


def load_questions(jsonl_path: str, max_samples: int = None, seed: int = 42) -> list:
    questions = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    rng = random.Random(seed)
    rng.shuffle(questions)
    if max_samples:
        questions = questions[:max_samples]
    return questions


class BenchmarkRunner:
    """
    Thin wrapper around lighteval for running the general benchmark.
    Uses lighteval's Pipeline for evaluation when available,
    falls back to direct loglikelihood scoring via transformers.
    """

    def __init__(self, model_path: str, max_samples: int = 25,
                 pass_threshold: float = 65.0, deep_samples: int = 50,
                 seed: int = 42, jsonl_path: str = None):
        self.model_path = model_path
        self.max_samples = max_samples
        self.pass_threshold = pass_threshold
        self.deep_samples = deep_samples
        self.seed = seed
        self.jsonl_path = jsonl_path or JSONL_PATH

    def run(self, progress_callback: Optional[Callable] = None) -> dict:
        """
        Two-stage evaluation:
        Stage 1: run max_samples questions.
        Stage 2: if scaled_score >= pass_threshold, run deep_samples questions.
        Returns the deeper result if stage 2 ran, otherwise stage 1 result.
        """
        if progress_callback:
            progress_callback(f"Stage 1: running {self.max_samples} questions...")

        stage1 = self._run_stage(self.max_samples)

        if stage1["scaled_score"] >= self.pass_threshold:
            if progress_callback:
                progress_callback(
                    f"Stage 1 passed ({stage1['scaled_score']:.1f}). "
                    f"Stage 2: running {self.deep_samples} questions..."
                )
            stage2 = self._run_stage(self.deep_samples)
            stage2["stage1_score"] = stage1["scaled_score"]
            stage2["two_stage"] = True
            return stage2

        stage1["two_stage"] = False
        return stage1

    def _run_stage(self, max_samples: int) -> dict:
        questions = load_questions(self.jsonl_path, max_samples=max_samples, seed=self.seed)

        try:
            return self._run_lighteval(questions)
        except Exception as e:
            logger.warning(f"lighteval pipeline failed ({e}), falling back to direct scoring")
            return self._run_direct(questions)

    def _run_lighteval(self, questions: list) -> dict:
        from lighteval.pipeline import Pipeline, PipelineParameters, EnvConfig
        from lighteval.models.model_config import BaseModelConfig
        from lighteval.tasks.lighteval_task import LightevalTaskConfig, Doc
        from lighteval.metrics.metrics import Metrics

        dataset = Dataset.from_list(questions)

        def prompt_fn(doc, task_name=None):
            return Doc(
                task_name=task_name or "breeding_vat_general",
                query=doc["query"],
                choices=doc["choices"],
                gold_index=doc["gold"],
            )

        task_cfg = LightevalTaskConfig(
            name="breeding_vat_general",
            prompt_function=prompt_fn,
            suite=["custom"],
            hf_repo=None,
            hf_subset=None,
            metric=[Metrics.loglikelihood_acc_norm],
            trust_dataset=True,
        )

        pipeline_params = PipelineParameters(
            launcher_type="local",
            env_config=EnvConfig(cache_dir=".cache/lighteval"),
            custom_tasks_directory=None,
            max_samples=len(questions),
            override_batch_size=4,
        )

        model_cfg = BaseModelConfig(
            pretrained=self.model_path,
            dtype="float16",
            device_map="auto",
        )

        pipeline = Pipeline(
            tasks=task_cfg,
            pipeline_params=pipeline_params,
            model_config=model_cfg,
            dataset_loading_processes=1,
        )

        # inject our dataset directly
        pipeline._task_dict["custom|breeding_vat_general|0"] = (task_cfg, dataset)
        pipeline.evaluate()
        results = pipeline.get_results()

        scores = results.get("results", {})
        task_key = next(iter(scores), None)
        if task_key:
            acc = scores[task_key].get("acc_norm,none", scores[task_key].get("acc,none", 0.0))
            n = len(questions)
            n_correct = round(acc * n)
            return self._build_result(n_correct, n, questions)

        raise ValueError("lighteval returned no results")

    def _run_direct(self, questions: list) -> dict:
        """Fallback: score each question by comparing loglikelihoods of each choice."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path, torch_dtype=torch.float16, device_map="auto"
        )
        model.eval()

        n_correct = 0
        answer_log = []

        for q in questions:
            try:
                scores = []
                for choice_text in q["choices"]:
                    prompt = q["query"] + " " + choice_text
                    enc = tokenizer(prompt, return_tensors="pt").to(model.device)
                    with torch.no_grad():
                        out = model(**enc, labels=enc["input_ids"])
                    scores.append(-out.loss.item())

                pred_idx = scores.index(max(scores))
                correct = pred_idx == q["gold"]
                if correct:
                    n_correct += 1
                letters = ["A", "B", "C", "D"]
                answer_log.append({
                    "id": q["id"], "topic": q["topic"],
                    "predicted": letters[pred_idx],
                    "correct_answer": q["answer_letter"],
                    "correct": correct,
                })
            except Exception as e:
                logger.warning(f"Question {q.get('id')} failed: {e}")
                answer_log.append({"id": q.get("id"), "correct": False})

        del model
        import gc, torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        result = self._build_result(n_correct, len(questions), questions)
        result["answer_log"] = answer_log
        return result

    def _build_result(self, n_correct: int, n_attempted: int, questions: list) -> dict:
        raw_acc = n_correct / n_attempted if n_attempted > 0 else 0.0
        anomalies = []
        if raw_acc < CHANCE_LEVEL:
            anomalies.append({"type": "below_chance", "detail": f"Raw accuracy {raw_acc:.2%} is below chance (25%) — systematically wrong"})
        if n_attempted <= 10 and raw_acc < 0.5:
            anomalies.append({"type": "early_failure", "detail": f"Low accuracy ({raw_acc:.2%}) on first {n_attempted} questions"})
        if n_attempted >= self.deep_samples and raw_acc > 0.85:
            anomalies.append({"type": "strong_ceiling", "detail": f"Reached {n_attempted} questions at {raw_acc:.2%} accuracy"})

        topics_attempted = {}
        for q in questions:
            topics_attempted.setdefault(q["topic"], 0)
            topics_attempted[q["topic"]] += 1

        return {
            "questions_attempted": n_attempted,
            "questions_correct": n_correct,
            "raw_accuracy": round(raw_acc, 4),
            "scaled_score": chance_corrected_score(n_correct, n_attempted),
            "topics_attempted": topics_attempted,
            "anomalies": anomalies,
            "seed": self.seed,
            "model_path": self.model_path,
        }
