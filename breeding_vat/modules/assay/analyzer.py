import torch
import numpy as np
import gc
import logging
from typing import List, Dict, Optional, Callable
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


class ASSAYAnalyzer:
    def __init__(self, model_path: str, vram_gb: int = 8):
        self.model_path = model_path
        self.vram_gb = vram_gb
        self.model = None
        self.tokenizer = None
        self.num_layers = None
        self.hidden_dim = None

    def load_model(self):
        logger.info(f"Loading model from {self.model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.num_layers = self.model.config.num_hidden_layers
        self.hidden_dim = self.model.config.hidden_size
        logger.info(f"Model loaded: {self.num_layers} layers, hidden_dim={self.hidden_dim}")

    def run(
        self,
        topic: str,
        n_mini: int = 12,
        n_full: int = 50,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        self.load_model()

        from breeding_vat.modules.assay.probe_strategies import generate_probes, STRATEGIES

        if progress_callback:
            progress_callback("Starting mini-rounds phase...")

        all_probes = generate_probes(topic, n_per_strategy=n_mini)
        strategy_scores = {}
        strategy_results = {}

        for strategy_name, questions in all_probes.items():
            if progress_callback:
                progress_callback(f"Mini-round: {strategy_name} ({len(questions)} questions)")
            results = self._run_strategy(questions, strategy_name)
            strategy_results[strategy_name] = results
            strategy_scores[strategy_name] = self._compute_strategy_discriminativeness(results)

        winning_strategy = max(strategy_scores, key=strategy_scores.get)

        if progress_callback:
            progress_callback(
                f"Winner: {winning_strategy} (score={strategy_scores[winning_strategy]:.3f}). "
                f"Running full {n_full}-question pass..."
            )

        full_questions = STRATEGIES[winning_strategy](topic, n_full)
        full_results_list = []

        for i, q in enumerate(full_questions):
            try:
                if progress_callback and i % 10 == 0:
                    progress_callback(f"Full run: {i}/{n_full}")
                result = self._process_question(q)
                full_results_list.append(result)
            except Exception as e:
                logger.warning(f"Failed to process question {i}: {e}")
                continue

        layer_stats, layer_vectors = self._build_layer_stats(full_results_list)

        quality_counts = {"great": 0, "acceptable": 0, "wrong": 0, "hallucinated": 0}
        for r in full_results_list:
            quality_counts[r["quality"]] += 1

        self.unload_model()

        return {
            "topic": topic,
            "winning_strategy": winning_strategy,
            "strategy_scores": strategy_scores,
            "layer_stats": layer_stats,
            "layer_vectors": {k: v.tolist() for k, v in layer_vectors.items()},
            "quality_counts": quality_counts,
            "n_questions": len(full_results_list),
            "signal_layers": [
                k for k, v in layer_stats.items() if v.get("contrast", 0) > 0.3
            ],
            "instability_layers": [
                k
                for k, v in layer_stats.items()
                if v.get("hallucinated", 0) > v.get("great", 0)
            ],
        }

    def _run_strategy(self, questions: List[str], strategy_name: str) -> dict:
        results_by_quality = {"great": [], "acceptable": [], "wrong": [], "hallucinated": []}

        for q in questions:
            try:
                result = self._process_question(q)
                quality = result["quality"]
                results_by_quality[quality].append(result["activations"])
            except Exception as e:
                logger.warning(f"Failed to process question in {strategy_name}: {e}")
                continue

        return results_by_quality

    def _process_question(self, question: str) -> dict:
        answer, activations = self._generate_and_capture(question)
        quality = self._score_answer(question, answer)

        return {"question": question, "answer": answer, "quality": quality, "activations": activations}

    def _generate_and_capture(self, prompt: str) -> tuple[str, Dict[int, np.ndarray]]:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.6,
                top_p=0.95,
            )

        answer_text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        activations = {}

        def make_hook(layer_idx):
            def hook_fn(module, input, output):
                if isinstance(output, tuple):
                    act = output[0]
                else:
                    act = output

                if isinstance(act, torch.Tensor):
                    activations[layer_idx] = (
                        act.detach()
                        .float()
                        .mean(dim=1)
                        .squeeze()
                        .cpu()
                        .numpy()
                    )

            return hook_fn

        hooks = []
        for i, layer in enumerate(self.model.model.layers):
            hooks.append(layer.register_forward_hook(make_hook(i)))

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            with torch.no_grad():
                _ = self.model(**inputs)
        finally:
            for h in hooks:
                h.remove()

        return answer_text, activations

    def _score_answer(self, question: str, answer: str) -> str:
        tokens = self.tokenizer.tokenize(answer)
        if len(tokens) < 10:
            return "wrong"

        bigrams = [
            (tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)
        ]
        if bigrams:
            unique_bigrams = len(set(bigrams))
            repetition_ratio = 1.0 - (unique_bigrams / len(bigrams))
            if repetition_ratio > 0.4:
                return "hallucinated"

        self_eval_prompt = (
            f"Rate this answer 1-4 where 1=wrong, 2=acceptable, 3=good, 4=excellent.\n"
            f"Q: {question}\n"
            f"A: {answer}\n"
            f"Rating:"
        )

        try:
            inputs = self.tokenizer(
                self_eval_prompt, return_tensors="pt", truncation=True, max_length=512
            )
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    do_sample=False,
                    temperature=1.0,
                )

            rating_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            for char in rating_text:
                if char in "1234":
                    rating = int(char)
                    if rating == 1:
                        return "wrong"
                    elif rating == 2:
                        return "acceptable"
                    else:
                        return "great"
        except Exception as e:
            logger.warning(f"Self-eval failed: {e}")

        return "acceptable"

    def _compute_strategy_discriminativeness(self, strategy_results: dict) -> float:
        layer_contrasts = []

        for layer_idx in range(self.num_layers):
            class_norms = {}

            for quality_class, activations_list in strategy_results.items():
                if not activations_list:
                    class_norms[quality_class] = 0.0
                    continue

                norms = []
                for act_dict in activations_list:
                    if layer_idx in act_dict:
                        act_vec = act_dict[layer_idx]
                        if isinstance(act_vec, np.ndarray):
                            norm = np.linalg.norm(act_vec)
                            norms.append(norm)

                if norms:
                    class_norms[quality_class] = np.mean(norms)
                else:
                    class_norms[quality_class] = 0.0

            if class_norms:
                max_norm = max(class_norms.values())
                min_norm = min(class_norms.values())
                contrast = max_norm - min_norm
                layer_contrasts.append(contrast)

        if layer_contrasts:
            return float(np.mean(layer_contrasts))
        return 0.0

    def _build_layer_stats(self, all_results: List[dict]) -> tuple[dict, dict]:
        layer_stats = {}
        layer_activations_by_quality = {
            layer_idx: {"great": [], "acceptable": [], "wrong": [], "hallucinated": []}
            for layer_idx in range(self.num_layers)
        }

        all_layer_activations = {layer_idx: [] for layer_idx in range(self.num_layers)}

        for result in all_results:
            quality = result["quality"]
            activations = result["activations"]

            for layer_idx, act_vec in activations.items():
                if isinstance(act_vec, np.ndarray):
                    layer_activations_by_quality[layer_idx][quality].append(act_vec)
                    all_layer_activations[layer_idx].append(act_vec)

        for layer_idx in range(self.num_layers):
            class_norms = {}

            for quality_class in ["great", "acceptable", "wrong", "hallucinated"]:
                acts = layer_activations_by_quality[layer_idx][quality_class]
                if acts:
                    norms = [np.linalg.norm(a) for a in acts]
                    class_norms[quality_class] = float(np.mean(norms))
                else:
                    class_norms[quality_class] = 0.0

            max_norm = max(class_norms.values()) if class_norms else 0.0
            min_norm = min(class_norms.values()) if class_norms else 0.0
            contrast = max_norm - min_norm

            layer_stats[layer_idx] = {
                **class_norms,
                "contrast": contrast,
            }

        layer_vectors = {}
        for layer_idx in range(self.num_layers):
            acts = all_layer_activations[layer_idx]
            if acts:
                mean_vec = np.mean([a for a in acts if isinstance(a, np.ndarray)], axis=0)
                layer_vectors[layer_idx] = mean_vec
            else:
                layer_vectors[layer_idx] = np.zeros(self.hidden_dim)

        return layer_stats, layer_vectors

    def unload_model(self):
        if self.model is not None:
            del self.model
        if self.tokenizer is not None:
            del self.tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
