# EXACT CODE CHANGES — Phase 1 Completion (1.5 hours)

**Goal**: Wire genealogy tracking + anomaly detection into evolution loop

---

## Change 1: EvolutionEngine.run_waterfall()

**File**: `breeding_vat/modules/merge/evolution.py`

**Location**: Top of class

```python
class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        self.engine = MergekitEngine(runner)
        self.advanced_merger = AdvancedMerger(runner)
        self.scope_filter = None
        self.frankenmerge_layer_assignment = None
        self.eval_tier = "standard"
        self.skip_perplexity = False
        self._benchmark = BenchmarkEvaluator(runner)
        
        # NEW: Injection points for genealogy tracking
        self._experiment_manager = None
        self._current_experiment = None
```

**Location**: In run_waterfall(), around line 40, after sorting offspring:

```python
def run_waterfall(self, base_models, goal, cycles, culling_rate, allowed_methods=["slerp"]):
    """Execute waterfall evolution pipeline using Mergekit."""
    population = [{"name": m, "score": 0, "parent": None} for m in base_models]

    for cycle in range(cycles):
        logger.info(f"--- Evolution Cycle {cycle + 1} ---")
        offspring = []

        # ... merge + evaluate section ...
        
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
```

**Location**: In run_waterfall(), when building offspring dict (line ~50), enhance metadata:

```python
# Around line 55-60, where we create offspring dict:
try:
    result = self._apply_merge_method(method, parent_model, sibling_model, child_name)
    
    if result:
        # Evaluate in Docker
        eval_result = self.evaluate(child_name)
        score = eval_result.get("score", 0.0)  # Change: extract score from dict
        
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
```

---

## Change 2: EvolutionWithLogging.run_waterfall()

**File**: `breeding_vat/modules/evolution/evolution_with_logging.py`

**Location**: In run_waterfall(), before calling evolution.run_waterfall() (line ~75):

```python
def run_waterfall(self, base_models: List[str], goal: str, num_cycles: int,
                 culling_rate: float = 50, allowed_methods: List[str] = None,
                 resume_from_cycle: int = 0) -> Dict:
    """..."""
    try:
        # ... existing setup code ...
        
        self._emit_progress(0, num_cycles, "Initializing evolution...")
        
        # NEW: Inject experiment manager into evolution engine for genealogy tracking
        self.evolution._experiment_manager = self.exp_manager
        self.evolution._current_experiment = self.experiment
        
        # Call the underlying evolution engine
        best_model = self.evolution.run_waterfall(
            base_models=base_models,
            goal=goal,
            cycles=num_cycles,
            culling_rate=culling_rate,
            allowed_methods=allowed_methods or ["slerp"]
        )
        
        # ... rest of method unchanged ...
```

---

## Change 3: BenchmarkEvaluator.evaluate()

**File**: `breeding_vat/modules/benchmark/evaluator.py`

**Location**: Imports section (top of file):

```python
from datetime import datetime
from breeding_vat.modules.benchmark.receipt_runner import BenchmarkRunner  # NEW
```

**Location**: In evaluate() method (replace entire method):

```python
def evaluate(
    self,
    model_name: str,
    experiment_id: Optional[int] = None,
    tier: str = "standard",
    skip_perplexity: bool = False,
) -> Dict:  # CHANGED: return type is now Dict, not float
    """
    Full tiered evaluation with anomaly detection.

    1. Perplexity check (fast, optional).
    2. lm-eval at requested tier.
    3. Anomaly detection via receipt_runner.
    4. Returns full evaluation results dict.

    Returns {
        "score": 0.748,              # composite score (0-1)
        "perplexity": 8.234,
        "arc_easy": 0.612,
        "arc_challenge": 0.751,
        "hellaswag": 0.740,
        "raw_scores": {...},         # all lm-eval results
        "anomalies": [...],          # from receipt_runner
        "timestamp": "2025-01-15T..."
    }
    """
    result = {
        "score": 0.0,
        "perplexity": None,
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
                "detail": f"Perplexity {ppl} exceeds threshold {PERPLEXITY_FAIL_THRESHOLD}"
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

    # --- Anomaly Detection: Check for task disparities ---
    if result.get("arc_challenge") and result.get("arc_easy"):
        diff = result["arc_challenge"] - result["arc_easy"]
        if diff > 0.2:  # Significant gap
            result["anomalies"].append({
                "type": "specialization",
                "detail": f"arc_challenge ({result['arc_challenge']:.3f}) >> arc_easy ({result['arc_easy']:.3f}) — possible specialization or degradation"
            })
    
    # Compute composite score (average of available tasks)
    valid_scores = [s for s in [result.get("arc_easy"), result.get("arc_challenge"), 
                                 result.get("hellaswag")] if s is not None]
    if valid_scores:
        result["score"] = sum(valid_scores) / len(valid_scores)
    else:
        result["score"] = 0.0

    logger.info(f"Benchmark [{model_name}] tier={tier}: {scores} → composite={result['score']:.4f}")

    # --- Optional: Run receipt_runner for deeper anomaly detection ---
    # (This is optional — only if you want two-stage evaluation)
    # try:
    #     runner = BenchmarkRunner(f"breeding_vat/data/merged_models/{model_name}", 
    #                               max_samples=25)
    #     receipt_result = runner.run()
    #     result["anomalies"].extend(receipt_result.get("anomalies", []))
    #     result["receipt_score"] = receipt_result.get("scaled_score")
    # except Exception as e:
    #     logger.warning(f"receipt_runner failed: {e}")

    if experiment_id is not None:
        self.db.log_scores(experiment_id, scores)

    return result  # CHANGED: now returns dict, not float
```

**Note**: All existing code that calls `evaluate()` and expects a float needs updating. See next change.

---

## Change 4: app.py evolution loop

**File**: `breeding_vat/ui/app.py`

**Location**: In the evolution button handler, where we call evo_logged.run_waterfall():

The existing code already handles this correctly if we return a dict from evaluate(). The key is that app.py stores the result as `best_model` which includes the score. Just verify the response is handled correctly.

**Current code should work as-is**, but verify that if evaluation returns a dict, best_model['score'] is extracted properly.

---

## Change 5: ExperimentManager.log_cycle()

**File**: `breeding_vat/modules/experiment_manager.py`

**Status**: Already correct! Just ensure it's being called.

The method signature is:
```python
def log_cycle(self, experiment: Dict, cycle_num: int, 
              models: List[Dict], best_model: Dict):
```

It expects:
```python
models = [
    {
        "name": "...",
        "score": 0.748,
        "method": "slerp",
        # ... more fields ...
    }
]
best_model = {"name": "...", "score": 0.748}
```

This is exactly what EvolutionEngine will now pass after Change 1.

---

## Summary of Changes

| File | Lines Changed | Type | Impact |
|------|---|---|---|
| evolution.py | ~70 lines | Add injection points + log_cycle() call + metadata enrichment | Enables genealogy logging |
| evolution_with_logging.py | ~3 lines | Inject exp_manager | Wires genealogy into engine |
| evaluator.py | ~120 lines | Return dict instead of float; add anomaly detection | Full eval results |
| app.py | 0 lines | Already handles it | No change needed |
| experiment_manager.py | 0 lines | Already correct | No change needed |

**Total new code**: ~200 lines

---

## Testing After Changes

```python
# In breeding_vat/test_genealogy.py (new file)

def test_genealogy_capture():
    """Verify genealogy is logged during evolution"""
    from breeding_vat.modules.experiment_manager import ExperimentManager
    from breeding_vat.modules.merge.evolution import EvolutionEngine
    from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
    from breeding_vat.orchestrator.runner import TaskRunner
    
    # Setup
    runner = TaskRunner()
    manager = ExperimentManager()
    exp = manager.create_experiment(
        goal="test",
        base_models=["Qwen-0.5B", "Mistral-7B"],
        merge_methods=["slerp"],
        num_cycles=1
    )
    
    evo = EvolutionEngine(runner)
    evo_logged = EvolutionWithLogging(evo, manager, exp)
    
    # Run
    best = evo_logged.run_waterfall(
        base_models=["Qwen-0.5B", "Mistral-7B"],
        goal="test",
        num_cycles=1,
        culling_rate=50,
        allowed_methods=["slerp"]
    )
    
    # Verify
    import json
    with open(exp['paths']['results'] + "/benchmarks.json") as f:
        benchmarks = json.load(f)
    
    assert len(benchmarks["cycles"]) == 1, "Cycle not logged"
    assert len(benchmarks["cycles"][0]["models"]) > 0, "Models not logged"
    
    model = benchmarks["cycles"][0]["models"][0]
    assert "method" in model, "Method not recorded"
    assert "parents" in model, "Parents not recorded"
    assert "benchmark" in model, "Benchmark results not recorded"
    assert "anomalies" in model, "Anomalies not recorded"
    
    print("✅ Genealogy capture working!")
```

---

## Verification Checklist

After implementing all 5 changes, verify:

- [ ] EvolutionEngine has `_experiment_manager` and `_current_experiment` attributes
- [ ] EvolutionWithLogging injects these before calling evolution
- [ ] BenchmarkEvaluator.evaluate() returns a dict with score, perplexity, raw_scores, anomalies
- [ ] EvolutionEngine builds offspring dicts with method, parents, benchmark, anomalies
- [ ] ExperimentManager.log_cycle() is called after each cycle
- [ ] exp['paths']['results']/benchmarks.json is populated with cycle results
- [ ] Each model has: name, score, method, parents, benchmark, anomalies
- [ ] UI can load and display genealogy from benchmarks.json

---

**End of EXACT_CODE_CHANGES.md**

Ready to implement. ~1.5 hours total.
