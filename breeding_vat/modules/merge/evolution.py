import random
import time
import torch
import gc
import os
import json
import sqlite3
import logging
from datetime import datetime
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.mergekit_engine import (
    MergekitEngine, MergekitConfigBuilder,
)
from breeding_vat.modules.merge.merger import AdvancedMerger
from breeding_vat.modules.benchmark.evaluator import BenchmarkEvaluator
from breeding_vat.modules.merge import advanced_toggles as ATG

logger = logging.getLogger("EvolutionEngine")

class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        self.engine = MergekitEngine(runner)
        self.advanced_merger = AdvancedMerger(runner)
        self.scope_filter = None  # Set to SCOPEFilter instance to enable pre-filtering
        self.frankenmerge_layer_assignment = None  # Set from SAE analysis output
        self.eval_tier = "standard"          # fast / standard / full
        self.skip_perplexity = False         # skip Tier-0 perplexity gate
        self._benchmark = BenchmarkEvaluator(runner)
        
        # NEW: Injection points for genealogy tracking
        self._experiment_manager = None
        self._current_experiment = None

        # Advanced orthogonal toggles (opt-in, from recipe['advanced']).
        # Populated by RecipeExecutor.build_evolution_config(); empty by default.
        self.advanced: dict = {}
        # Per-cycle benchmark scores for bench_weighted_blend, set by run loop.
        self._last_parent_scores: dict = {}

    def cleanup_vram(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ── Advanced toggles ─────────────────────────────────────────────────
    def _advanced_params(self, name: str) -> dict:
        """Return params dict for an enabled advanced toggle, else {}."""
        cfg = self.advanced.get(name) or {}
        return dict(cfg.get("params") or {})

    def _apply_advanced_yaml(self, config: dict, method: str,
                              model_a: str, model_b: str) -> dict:
        """
        Rewrite a MergeKit YAML config to fold in MergeKit-native advanced
        toggles. Pure: returns a new dict, leaves input alone.
        See advanced_toggles.TOGGLE_ROUTING — only 'mergekit_yaml' route lands here.
        """
        if not self.advanced:
            return config
        cb = MergekitConfigBuilder

        # 1. topk_sparsify → density (TIES/DARE accept it natively)
        if "topk_sparsify" in self.advanced and method in ("ties", "dare", "dare_ties"):
            p = self._advanced_params("topk_sparsify")
            density = max(0.001, float(p.get("keep_percent", 10.0)) / 100.0)
            config = cb.apply_density(config, density)

        # 2. attn_mlp_filter → per-model filter selectors
        if "attn_mlp_filter" in self.advanced:
            p = self._advanced_params("attn_mlp_filter")
            config = cb.apply_module_filters(
                config,
                merge_attention=bool(p.get("merge_attention", True)),
                merge_mlp=bool(p.get("merge_mlp", True)),
                merge_norms=bool(p.get("merge_norms", True)),
                merge_embeddings=bool(p.get("merge_embeddings", True)),
            )

        # 3. embedding_mode → tokenizer_source + filter
        if "embedding_mode" in self.advanced:
            p = self._advanced_params("embedding_mode")
            config = cb.apply_tokenizer_mode(
                config, p.get("embedding_mode", "partial"),
            )

        # 4. bench_weighted_blend → per-model weight from scores
        if "bench_weighted_blend" in self.advanced and self._last_parent_scores:
            p = self._advanced_params("bench_weighted_blend")
            scores = [
                self._last_parent_scores.get(model_a, 0.0),
                self._last_parent_scores.get(model_b, 0.0),
            ]
            weights = ATG.bench_score_to_weights(scores, gamma=float(p.get("gamma", 2.0)))
            if weights:
                config = cb.apply_per_model_weights(config, weights)

        # 5. layerwise_alpha → slices block (overrides simple weight)
        if "layerwise_alpha" in self.advanced:
            p = self._advanced_params("layerwise_alpha")
            total = int(p.get("total_layers", 0))
            if total > 0:
                curve = ATG.layer_alpha_curve(
                    total_layers=total,
                    base_alpha=float(p.get("base_alpha", 1.0)),
                    mode=str(p.get("layer_mode", "flat")),
                    gamma=float(p.get("gamma", 1.0)),
                )
                config = cb.apply_layerwise_alpha(config, curve, total)

        return config

    def _mutate_advanced_for_cycle(self, cycle: int) -> None:
        """
        For every advanced toggle with `mutate: true`, jitter its numeric params
        in place. Categorical params are swapped uniformly at random. Called at
        the top of each cycle by run_waterfall().

        Bounds and choices are pulled from RecipeValidator so the mutation can
        never produce an invalid recipe.
        """
        if not self.advanced:
            return
        from breeding_vat.modules.merge.recipe_validator import (
            PARAM_BOUNDS, PARAM_CHOICES,
        )
        rng = random.Random(int(time.time() * 1000) ^ cycle)
        for tname, tcfg in self.advanced.items():
            if not tcfg.get("mutate"):
                continue
            params = tcfg.setdefault("params", {})
            for p, v in list(params.items()):
                if p in PARAM_BOUNDS and isinstance(v, (int, float)):
                    lo, hi = PARAM_BOUNDS[p]
                    span = (hi - lo) * 0.1  # 10 % of range = mutation step
                    nv = float(v) + rng.gauss(0.0, span)
                    params[p] = max(lo, min(hi, nv))
                elif p in PARAM_CHOICES:
                    params[p] = rng.choice(sorted(PARAM_CHOICES[p]))
        logger.debug(f"cycle {cycle}: advanced toggles mutated")

    def _apply_post_transforms(self, model_name: str) -> None:
        """Stream-apply post-merge transforms (gaussian noise, etc.)."""
        if not self.advanced:
            return
        post = {k: v for k, v in self.advanced.items()
                if ATG.toggle_route(k) == "post_transform"}
        if not post:
            return
        # Resolve to engine output dir (matches MergekitEngine.output_dir layout).
        import os
        model_dir = os.path.join(self.engine.output_dir, model_name)
        if not os.path.isdir(model_dir):
            logger.debug(f"post_transforms: dir not found {model_dir}; skip")
            return
        try:
            result = ATG.apply_post_transforms_streaming(model_dir, post)
            logger.info(f"post_transforms on {model_name}: {result}")
        except Exception as e:
            logger.warning(f"post_transforms failed for {model_name}: {e}")

    def run_waterfall(self, base_models, goal, cycles, culling_rate, allowed_methods=["slerp"]):
        """Execute waterfall evolution pipeline using Mergekit."""
        population = [{"name": m, "score": 0, "parent": None} for m in base_models]

        for cycle in range(cycles):
            logger.info(f"--- Evolution Cycle {cycle + 1} ---")
            offspring = []
            # Refresh parent-score map for bench_weighted_blend (advanced toggle).
            self._last_parent_scores = {m["name"]: m["score"] for m in population}
            # Mutate advanced toggles flagged with mutate=true.
            self._mutate_advanced_for_cycle(cycle)

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
                            # NEW: Evaluate returns dict, extract score and full results
                            eval_result = self.evaluate(child_name)
                            score = eval_result.get("score", 0.0)
                            logger.info(f"  Score: {score:.4f}")
                            
                            # Log to DB
                            self.runner.log_model(child_name, [parent_model, sibling_model], method, parent_id=None)
                            
                            # NEW: Enrich offspring metadata with full evaluation results
                            offspring.append({
                                "name": child_name,
                                "score": score,
                                "parent": parent_model,
                                "parents": [parent_model, sibling_model],  # NEW: both parents
                                "method": method,  # NEW
                                "method_params": {},  # NEW: add method params if available
                                "benchmark": eval_result,  # NEW: full eval results
                                "anomalies": eval_result.get("anomalies", [])  # NEW
                            })
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
            
            # NEW: Log cycle to ExperimentManager if injected
            if self._experiment_manager is not None:
                models_data = [
                    {
                        "name": m['name'],
                        "score": m['score'],
                        "method": m.get('method', 'unknown'),
                        "method_params": m.get('method_params', {}),
                        "parents": m.get('parents', []),
                        "benchmark": m.get('benchmark', {}),
                        "anomalies": m.get('anomalies', []),
                        "cycle": cycle + 1
                    }
                    for m in population
                ]
                self._experiment_manager.log_cycle(
                    self._current_experiment,
                    cycle_num=cycle + 1,
                    models=models_data,
                    best_model=population[0]
                )
            
            self.cleanup_vram()

        best_model = population[0]
        logger.info(f"Evolution complete. Best model: {best_model['name']} (score: {best_model['score']:.4f})")
        return best_model
    
    def _apply_merge_method(self, method: str, model_a: str, model_b: str,
                              output_name: str) -> bool:
        """Public dispatch: installs advanced hooks, runs merge, applies post-pass."""
        # Install the YAML hook so MergeKit configs pick up recipe['advanced'].
        if self.advanced:
            self.engine.config_hook = (
                lambda cfg, m, base, others, a=model_a, b=model_b:
                    self._apply_advanced_yaml(cfg, m, a, b)
            )
        else:
            self.engine.config_hook = None
        ok = self._apply_merge_method_raw(method, model_a, model_b, output_name)
        if ok and self.advanced:
            self._apply_post_transforms(output_name)
        return ok

    def _apply_merge_method_raw(self, method: str, model_a: str, model_b: str,
                                 output_name: str) -> bool:
        """Route a merge method to MergeKit or FusionBench as appropriate."""
        # Pull per-method params set by recipe (default empty)
        mp = getattr(self, 'method_params', {}).get(method, {})

        try:
            # ── MergeKit methods ──────────────────────────────────────────
            if method == "slerp":
                config_path = self.engine.create_config(
                    "slerp", model_a, [model_b], {"weights": [mp.get("t", 0.5)]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "ties":
                config_path = self.engine.create_config(
                    "ties", model_a, [model_b],
                    {"threshold": mp.get("threshold", 0.9), "weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "dare":
                config_path = self.engine.create_config(
                    "dare", model_a, [model_b],
                    {"drop_rate": mp.get("drop_rate", 0.1), "weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "task_arithmetic":
                config_path = self.engine.create_config(
                    "task_arithmetic", model_a, [model_b],
                    {"weights": [mp.get("scaling_factor", 0.5)]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "linear":
                config_path = self.engine.create_config(
                    "linear", model_a, [model_b], {"weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "moe":
                config_path = self.engine.create_config(
                    "moe", model_a, [model_b], {"num_experts": 2}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "rmm":
                # RMM approximated via TIES
                config_path = self.engine.create_config(
                    "ties", model_a, [model_b],
                    {"threshold": 0.5, "weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "negmerge":
                # NegMerge via linear with negative weight on model_b
                config_path = self.engine.create_config(
                    "linear", model_a, [model_b], {"weights": [-0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            elif method == "dare_ties":
                config_path = self.engine.create_config(
                    "dare", model_a, [model_b],
                    {"drop_rate": mp.get("drop_rate", 0.1), "weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

            # ── FusionBench via AdvancedMerger named wrappers ─────────────
            elif method == "frankenmerge":
                return self.advanced_merger.frankenmerge(
                    models=[model_a, model_b],
                    output_path=output_name,
                    layer_assignment=self.frankenmerge_layer_assignment,
                    rank=mp.get("rank", 8),
                ) is not None

            elif method == "regmean":
                return self.advanced_merger.regmean_merge(
                    base_model=model_a, models=[model_b],
                    output_path=output_name,
                    reg=mp.get("reg", 0.0),
                ) is not None

            elif method == "voting":
                return self.advanced_merger.voting_merge(
                    models=[model_a, model_b],
                    output_path=output_name,
                    voting_method=mp.get("voting_method", "majority"),
                ) is not None

            elif method == "magnitude_prune":
                return self.advanced_merger.magnitude_prune_merge(
                    models=[model_a, model_b],
                    output_path=output_name,
                    prune_ratio=mp.get("prune_ratio", 0.1),
                ) is not None

            elif method == "git_rebasin":
                return self.advanced_merger.git_rebasin_merge(
                    base_model=model_a, models=[model_b],
                    output_path=output_name,
                    lambda_=mp.get("scaling_factor", 0.1),
                ) is not None

            # ── FusionBench direct via run_merge (new signature) ──────────
            elif method in ["dare_linear", "ties_linear", "layer_wise",
                            "multi_task", "expert_selection",
                            "variance_reduction"]:
                return self.advanced_merger.fusionbench.run_merge(
                    method, model_a, [model_b], output_name, mp
                ) is not None

            else:
                logger.warning(f"No handler for '{method}', falling back to SLERP")
                config_path = self.engine.create_config(
                    "slerp", model_a, [model_b], {"weights": [0.5]}
                )
                return self.engine.run_merge(config_path, output_name) is not None

        except Exception as e:
            logger.error(f"Merge method {method} failed: {e}")
            return False

    def evaluate(self, model_name: str, experiment_id: int = None):
        """
        Tiered evaluation via BenchmarkEvaluator.

        Tier 0 (perplexity gate) → Tier 1-3 (lm-eval tasks).
        SCOPE pre-filter runs first if enabled; rejects obviously broken merges
        before any Docker eval container is launched.
        
        Returns dict with score, perplexity, per-task scores, and anomalies.
        """
        if self.scope_filter is not None:
            passed, reason = self.scope_filter.check(model_name)
            if not passed:
                logger.info(f"SCOPE pre-filter rejected {model_name}: {reason}")
                return {"score": 0.0, "anomalies": [{"type": "scope_filter_reject", "detail": reason}]}

        return self._benchmark.evaluate(
            model_name,
            experiment_id=experiment_id,
            tier=self.eval_tier,
            skip_perplexity=self.skip_perplexity,
        )
