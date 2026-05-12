# /scoring/premerge_risk_estimator.py

"""
Purpose:
Estimate whether a merge is likely to:
- fail catastrophically
- overfit benchmarks
- lose capabilities
- produce unstable routing
- hallucinate more often

This runs BEFORE expensive merges/benchmarks.

Inputs:
- model metadata
- tokenizer metadata
- latent embeddings (LaSER)
- prior merge history
- merge recipe
- architecture info

Outputs:
{
    "merge_instability": float,
    "catastrophic_forgetting": float,
    "benchmark_overfit_risk": float,
    "routing_conflict": float,
    "tokenizer_conflict": float,
    "architecture_conflict": float,
    "overall_risk": float,
    "recommendation": str
}
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np


# ============================================================
# CONFIG
# ============================================================

SAFE_TOKENIZER_MATCH = 0.95
SAFE_LATENT_SIMILARITY = 0.80
SAFE_ARCH_ALIGNMENT = 0.85


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ModelMetadata:
    name: str
    architecture: str
    tokenizer: str
    hidden_size: int
    num_layers: int
    rope_type: str
    latent_embedding: np.ndarray


@dataclass
class MergeRecipe:
    merge_method: str
    sparsity: float
    density: float
    layerwise: bool
    moe: bool


# ============================================================
# MAIN ESTIMATOR
# ============================================================

class PremergeRiskEstimator:

    def __init__(self):
        pass

    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def estimate(
        self,
        models: List[ModelMetadata],
        recipe: MergeRecipe
    ) -> Dict:

        latent_similarity = self._latent_similarity(models)

        tokenizer_conflict = self._tokenizer_conflict(models)

        architecture_conflict = self._architecture_conflict(models)

        routing_conflict = self._routing_conflict(
            recipe,
            latent_similarity
        )

        catastrophic_forgetting = (
            self._catastrophic_forgetting_risk(
                latent_similarity,
                recipe
            )
        )

        benchmark_overfit_risk = (
            self._benchmark_overfit_risk(recipe)
        )

        merge_instability = (
            self._merge_instability(
                recipe,
                architecture_conflict,
                tokenizer_conflict
            )
        )

        overall_risk = np.mean([
            merge_instability,
            catastrophic_forgetting,
            benchmark_overfit_risk,
            routing_conflict,
            tokenizer_conflict,
            architecture_conflict
        ])

        recommendation = self._generate_recommendation(
            overall_risk
        )

        return {
            "merge_instability": round(merge_instability, 3),
            "catastrophic_forgetting": round(catastrophic_forgetting, 3),
            "benchmark_overfit_risk": round(benchmark_overfit_risk, 3),
            "routing_conflict": round(routing_conflict, 3),
            "tokenizer_conflict": round(tokenizer_conflict, 3),
            "architecture_conflict": round(architecture_conflict, 3),
            "overall_risk": round(overall_risk, 3),
            "recommendation": recommendation
        }

    # ========================================================
    # LATENT SIMILARITY
    # ========================================================

    def _latent_similarity(
        self,
        models: List[ModelMetadata]
    ) -> float:

        similarities = []

        for i in range(len(models)):
            for j in range(i + 1, len(models)):

                a = models[i].latent_embedding
                b = models[j].latent_embedding

                sim = self._cosine_similarity(a, b)

                similarities.append(sim)

        return float(np.mean(similarities))

    def _cosine_similarity(self, a, b):

        return np.dot(a, b) / (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )

    # ========================================================
    # TOKENIZER CONFLICT
    # ========================================================

    def _tokenizer_conflict(
        self,
        models: List[ModelMetadata]
    ) -> float:

        tokenizers = [m.tokenizer for m in models]

        unique = len(set(tokenizers))

        if unique == 1:
            return 0.0

        return min(1.0, unique * 0.35)

    # ========================================================
    # ARCHITECTURE CONFLICT
    # ========================================================

    def _architecture_conflict(
        self,
        models: List[ModelMetadata]
    ) -> float:

        architectures = [m.architecture for m in models]

        unique_arch = len(set(architectures))

        layer_variance = np.std([
            m.num_layers for m in models
        ])

        hidden_variance = np.std([
            m.hidden_size for m in models
        ])

        score = (
            (unique_arch - 1) * 0.35
            + min(layer_variance / 50, 0.3)
            + min(hidden_variance / 4096, 0.3)
        )

        return min(score, 1.0)

    # ========================================================
    # ROUTING CONFLICT
    # ========================================================

    def _routing_conflict(
        self,
        recipe: MergeRecipe,
        latent_similarity: float
    ) -> float:

        if not recipe.moe:
            return 0.1

        if latent_similarity < 0.55:
            return 0.85

        if latent_similarity < 0.70:
            return 0.55

        return 0.2

    # ========================================================
    # CATASTROPHIC FORGETTING
    # ========================================================

    def _catastrophic_forgetting_risk(
        self,
        latent_similarity: float,
        recipe: MergeRecipe
    ) -> float:

        risk = 1.0 - latent_similarity

        if recipe.sparsity > 0.7:
            risk += 0.15

        if recipe.merge_method in [
            "frankenmerge",
            "passthrough"
        ]:
            risk += 0.20

        return min(risk, 1.0)

    # ========================================================
    # BENCHMARK OVERFIT
    # ========================================================

    def _benchmark_overfit_risk(
        self,
        recipe: MergeRecipe
    ) -> float:

        risky_methods = {
            "ties": 0.55,
            "dare": 0.45,
            "frankenmerge": 0.70,
            "task_arithmetic": 0.50,
            "slerp": 0.20,
            "breadcrumbs": 0.15
        }

        base = risky_methods.get(
            recipe.merge_method,
            0.35
        )

        if recipe.sparsity > 0.75:
            base += 0.15

        return min(base, 1.0)

    # ========================================================
    # MERGE INSTABILITY
    # ========================================================

    def _merge_instability(
        self,
        recipe: MergeRecipe,
        architecture_conflict: float,
        tokenizer_conflict: float
    ) -> float:

        instability = (
            architecture_conflict * 0.4
            + tokenizer_conflict * 0.3
        )

        unstable_methods = {
            "frankenmerge": 0.8,
            "passthrough": 0.65,
            "task_arithmetic": 0.5,
            "dare": 0.4,
            "ties": 0.3,
            "slerp": 0.15
        }

        instability += unstable_methods.get(
            recipe.merge_method,
            0.25
        )

        return min(instability, 1.0)

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    def _generate_recommendation(
        self,
        overall_risk: float
    ) -> str:

        if overall_risk < 0.25:
            return "SAFE_TO_MERGE"

        elif overall_risk < 0.50:
            return "MODERATE_RISK"

        elif overall_risk < 0.75:
            return "HIGH_RISK"

        return "LIKELY_UNSTABLE"


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":

    model_a = ModelMetadata(
        name="Qwen2.5-7B",
        architecture="qwen",
        tokenizer="qwen_tokenizer",
        hidden_size=4096,
        num_layers=32,
        rope_type="dynamic",
        latent_embedding=np.random.rand(4096)
    )

    model_b = ModelMetadata(
        name="DeepSeek-R1",
        architecture="qwen",
        tokenizer="qwen_tokenizer",
        hidden_size=4096,
        num_layers=32,
        rope_type="dynamic",
        latent_embedding=np.random.rand(4096)
    )

    recipe = MergeRecipe(
        merge_method="ties",
        sparsity=0.55,
        density=0.45,
        layerwise=True,
        moe=False
    )

    estimator = PremergeRiskEstimator()

    result = estimator.estimate(
        [model_a, model_b],
        recipe
    )

    print(result)