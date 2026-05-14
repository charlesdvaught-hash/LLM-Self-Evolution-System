"""
RecipeValidator — lightweight safety gate for advisor-generated merge recipes.

The advisor (a small LLM) produces structured JSON/YAML merge configs.  Before
any recipe is handed to Docker/MergeKit/FusionBench, this validator checks:

1. Method is in the known-allowed list.
2. Numeric parameters are within safe ranges.
3. No string field contains shell metacharacters (injection prevention).
4. Required fields are present.

On failure, ValidationError is raised with a human-readable explanation.
On success, the recipe dict is returned unchanged — the validator never mutates.
"""

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("RecipeValidator")

# ── Allowed methods ─────────────────────────────────────────────────────────

MERGEKIT_METHODS = {
    "slerp", "ties", "dare", "task_arithmetic", "moe", "linear",
    "rmm", "negmerge", "dare_ties",
}

FUSIONBENCH_METHODS = {
    "linear", "task_arithmetic", "regmean", "voting", "magnitude_prune",
    "git_rebasin", "dare_linear", "ties_linear", "frankenmerge",
    "layer_wise", "multi_task", "expert_selection", "variance_reduction",
}

ALLOWED_METHODS = MERGEKIT_METHODS | FUSIONBENCH_METHODS

# ── Parameter bounds ─────────────────────────────────────────────────────────
# Each entry: (min_inclusive, max_inclusive)
PARAM_BOUNDS: Dict[str, tuple] = {
    "drop_rate":   (0.0, 0.99),
    "threshold":   (0.0, 1.0),
    "prune_ratio": (0.0, 0.99),
    "reg":         (0.0, 1.0),
    "lambda_":     (0.0, 10.0),
    "rank":        (1,   256),
    "num_experts": (2,   32),
    # ── Advanced orthogonal toggles (opt-in) ─────────────────────────────
    "alpha":               (0.0, 2.5),
    "base_alpha":          (0.0, 2.5),
    "gamma":               (0.1, 8.0),
    "keep_percent":        (0.1, 100.0),
    "retain_rank_percent": (1.0, 100.0),
    "similarity_threshold": (-1.0, 1.0),
    "mutation_sigma":      (0.0, 0.01),
    "t":                   (0.0, 1.0),
}

# Categorical (non-numeric) param choices for advanced toggles.
PARAM_CHOICES: Dict[str, set] = {
    "layer_mode":      {"flat", "linear", "frontloaded", "backloaded",
                         "exponential", "sigmoid", "middle"},
    "sign_mode":       {"majority", "unanimous", "weighted"},
    "slerp_variant":   {"linear", "slerp", "nuslerp"},
    "mutation_target": {"all", "attention", "mlp", "embedding", "lora"},
    "alt_pattern":     {"odd_even", "even_odd", "first_half",
                         "second_half", "random", "custom"},
    "cosine_mode":     {"suppress", "keep_a", "keep_b", "report"},
    "coef_scope":      {"region", "layer", "tensor", "global"},
    "embedding_mode":  {"freeze", "partial", "full", "scaled"},
}

# Known advanced-toggle keys (used to scope validation of recipe['advanced']).
ADVANCED_TOGGLE_KEYS = {
    "layerwise_alpha",
    "topk_sparsify",
    "sign_consensus_mask",
    "attn_mlp_filter",
    "bench_weighted_blend",
    "dynamic_coef_sample",
    "slerp_variants",
    "lora_rank_prune",
    "cosine_filter",
    "gaussian_mutation",
    "alt_layer_inject",
}

# ── Shell injection pattern ───────────────────────────────────────────────────
# Reject any string value that contains these metacharacters.
_SHELL_RE = re.compile(r"[;&|`$<>\\\n\r]")

# ── Required top-level fields ────────────────────────────────────────────────
REQUIRED_FIELDS = {"method", "base_model", "merge_models"}


class ValidationError(ValueError):
    """Raised when a recipe fails validation."""


class RecipeValidator:
    """
    Validates advisor-generated merge recipe dicts.

    Usage:
        rv = RecipeValidator()
        rv.validate(recipe)        # raises ValidationError on failure
        ok, reason = rv.check(recipe)  # non-raising variant
    """

    def __init__(self, extra_allowed_methods: Optional[List[str]] = None):
        self._allowed = set(ALLOWED_METHODS)
        if extra_allowed_methods:
            self._allowed.update(m.lower() for m in extra_allowed_methods)

    # ── Public API ───────────────────────────────────────────────────────────

    def validate(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate recipe and return it unchanged.
        Raises ValidationError with a descriptive message on any failure.
        """
        if not isinstance(recipe, dict):
            raise ValidationError(f"Recipe must be a dict, got {type(recipe).__name__}")

        self._check_required_fields(recipe)
        self._check_method(recipe)
        self._check_string_fields(recipe)
        self._check_parameters(recipe.get("parameters", {}))
        self._check_weights(recipe)
        self._check_advanced(recipe.get("advanced", {}))

        logger.debug(f"Recipe validated OK: method={recipe['method']}")
        return recipe

    def check(self, recipe: Dict[str, Any]):
        """Non-raising wrapper. Returns (True, "") or (False, reason)."""
        try:
            self.validate(recipe)
            return True, ""
        except ValidationError as e:
            return False, str(e)

    # ── Internal checks ──────────────────────────────────────────────────────

    def _check_required_fields(self, recipe: Dict[str, Any]) -> None:
        missing = REQUIRED_FIELDS - recipe.keys()
        if missing:
            raise ValidationError(f"Recipe missing required fields: {sorted(missing)}")

    def _check_method(self, recipe: Dict[str, Any]) -> None:
        method = str(recipe.get("method", "")).lower().strip()
        if not method:
            raise ValidationError("Recipe 'method' is empty")
        if method not in self._allowed:
            raise ValidationError(
                f"Unknown/disallowed method '{method}'. "
                f"Allowed: {sorted(self._allowed)}"
            )

    def _check_string_fields(self, recipe: Dict[str, Any], _depth: int = 0) -> None:
        """Recursively scan all string values for shell metacharacters."""
        if _depth > 5:
            return  # guard against pathological nesting
        for key, val in recipe.items():
            if isinstance(val, str):
                if _SHELL_RE.search(val):
                    raise ValidationError(
                        f"Field '{key}' contains disallowed shell characters: {val!r}"
                    )
            elif isinstance(val, dict):
                self._check_string_fields(val, _depth + 1)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and _SHELL_RE.search(item):
                        raise ValidationError(
                            f"List field '{key}' contains disallowed shell characters: {item!r}"
                        )
                    elif isinstance(item, dict):
                        self._check_string_fields(item, _depth + 1)

    def _check_parameters(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            raise ValidationError(f"'parameters' must be a dict, got {type(params).__name__}")
        for param, (lo, hi) in PARAM_BOUNDS.items():
            if param in params:
                val = params[param]
                if not isinstance(val, (int, float)):
                    raise ValidationError(
                        f"Parameter '{param}' must be numeric, got {type(val).__name__}"
                    )
                if not (lo <= val <= hi):
                    raise ValidationError(
                        f"Parameter '{param}'={val} out of allowed range [{lo}, {hi}]"
                    )

    def _check_advanced(self, advanced: Dict[str, Any]) -> None:
        """
        Validate the optional `advanced` block:

            {
              "<toggle_name>": {
                "enabled": bool,
                "mutate":  bool,
                "params":  { ... numeric / categorical ... }
              },
              ...
            }

        All fields are opt-in. Unknown toggle keys raise ValidationError so a
        typo cannot silently no-op.
        """
        if not advanced:
            return
        if not isinstance(advanced, dict):
            raise ValidationError(
                f"'advanced' must be a dict, got {type(advanced).__name__}"
            )
        for tname, tcfg in advanced.items():
            if tname not in ADVANCED_TOGGLE_KEYS:
                raise ValidationError(
                    f"Unknown advanced toggle '{tname}'. "
                    f"Allowed: {sorted(ADVANCED_TOGGLE_KEYS)}"
                )
            if not isinstance(tcfg, dict):
                raise ValidationError(
                    f"advanced.{tname} must be a dict, got {type(tcfg).__name__}"
                )
            for flag in ("enabled", "mutate"):
                if flag in tcfg and not isinstance(tcfg[flag], bool):
                    raise ValidationError(
                        f"advanced.{tname}.{flag} must be bool"
                    )
            params = tcfg.get("params", {})
            if not isinstance(params, dict):
                raise ValidationError(
                    f"advanced.{tname}.params must be a dict"
                )
            # Numeric bounds
            for pname, val in params.items():
                if pname in PARAM_BOUNDS:
                    lo, hi = PARAM_BOUNDS[pname]
                    if not isinstance(val, (int, float)):
                        raise ValidationError(
                            f"advanced.{tname}.params.{pname} must be numeric"
                        )
                    if not (lo <= val <= hi):
                        raise ValidationError(
                            f"advanced.{tname}.params.{pname}={val} "
                            f"out of [{lo}, {hi}]"
                        )
                elif pname in PARAM_CHOICES:
                    if val not in PARAM_CHOICES[pname]:
                        raise ValidationError(
                            f"advanced.{tname}.params.{pname}={val!r} "
                            f"not in {sorted(PARAM_CHOICES[pname])}"
                        )
                # Unknown param names are permitted (forward-compat); they're
                # ignored by the engine unless wired in advanced_toggles.py.

    def _check_weights(self, recipe: Dict[str, Any]) -> None:
        weights = recipe.get("weights") or recipe.get("parameters", {}).get("weights")
        if weights is None:
            return
        if not isinstance(weights, list):
            raise ValidationError("'weights' must be a list of floats")
        for i, w in enumerate(weights):
            if not isinstance(w, (int, float)):
                raise ValidationError(f"Weight[{i}] must be numeric, got {type(w).__name__}")
            if not (-5.0 <= w <= 5.0):
                raise ValidationError(
                    f"Weight[{i}]={w} out of allowed range [-5.0, 5.0]. "
                    "Use negmerge for negative directions, not raw negative weights."
                )
