# MERGEBENCH / Existing Tools Analysis

**Question**: Would it be easier to use bits of MergeBench instead of building our own genealogy + anomaly tracking?

**Answer**: YES, partially. We already HAVE most of what we need. Analysis below.

---

## What We Already Have

### 1. **receipt_runner.py** ✅ EXCELLENT

This module ALREADY implements:
- ✅ Two-stage evaluation (Stage 1: 25 qs, Stage 2: 50 qs)
- ✅ Anomaly detection (below_chance, early_failure, strong_ceiling)
- ✅ Chance-corrected scoring: `max(0, (accuracy - 0.25) / 0.75) × 100`
- ✅ Topic-level breakdown
- ✅ Both lighteval integration AND fallback direct scoring

**Status**: Ready to use immediately.

**Example output**:
```json
{
  "questions_attempted": 50,
  "questions_correct": 37,
  "raw_accuracy": 0.74,
  "scaled_score": 65.33,
  "topics_attempted": {"reasoning": 25, "knowledge": 25},
  "anomalies": [
    {"type": "below_chance", "detail": "..."},
    {"type": "strong_ceiling", "detail": "..."}
  ]
}
```

### 2. **fusion_bench_wrapper.py** ✅ PROVIDES STRUCTURE

Advantages:
- ✅ Shows how to create YAML configs for algorithms
- ✅ Abstracts Docker execution
- ✅ Handles multiple merge algorithms + eval in one pipeline

Disadvantage:
- ❌ Heavy: FusionBench is for running merge + eval together
- ❌ Overkill for just tracking genealogy
- ❌ Doesn't integrate with ExperimentManager

### 3. **BenchmarkEvaluator** ⚠️ PARTIAL

Current implementation:
- ✅ Perplexity check (15s, good for fast gate)
- ✅ lm-eval integration (hellaswag, arc_challenge, arc_easy)
- ✅ Docker execution

Problems:
- ❌ Returns single score (float), not dict with per-task scores
- ❌ No anomaly detection
- ❌ No quirk flagging (score jumps, specialization, etc.)

---

## The Real Problem

We DON'T have genealogy tracking anywhere. The issue is **not anomaly detection** (receipt_runner already does it), but:

1. **Genealogy logging missing** — ExperimentManager.log_cycle() never called
2. **Model metadata incomplete** — No parents, method, method_params, timestamp, cycle info
3. **Integration broken** — EvolutionEngine doesn't call log_cycle()
4. **UI disconnected** — No way to display genealogy

---

## Smart Solution: Hybrid Approach

Instead of building everything from scratch, **reuse what's ready, wire what's broken**:

### Use receipt_runner.py for anomaly detection

**Change BenchmarkEvaluator.evaluate()**:

```python
def evaluate(self, model_name: str, tier: str = "standard", skip_perplexity: bool = False) -> Dict:
    """
    Returns dict instead of float:
    {
        "score": 0.748,           # composite
        "perplexity": 8.234,      # tier 0
        "arc_easy": 0.612,        # tier 1
        "arc_challenge": 0.751,   # tier 2
        "hellaswag": 0.740,       # tier 2
        "anomalies": [...]        # quirk detection
    }
    """
    
    # Tier 0: Perplexity
    if not skip_perplexity:
        passed, ppl, reason = self.run_perplexity(model_name)
        if not passed:
            return {
                "score": 0.0,
                "perplexity": ppl,
                "anomalies": [{"type": "perplexity_fail", "detail": reason}]
            }
    
    # Tier 1-3: lm-eval
    scores = self.run_lm_eval(model_name, tier=tier)
    
    # Run receipt_runner for anomaly detection
    runner = BenchmarkRunner(model_path, max_samples=25)
    receipt_result = runner.run()  # Returns {score, anomalies}
    
    # Merge results
    return {
        "score": receipt_result["scaled_score"] / 100,  # normalize to 0-1
        "perplexity": ppl if not skip_perplexity else None,
        "arc_easy": scores.get("arc_easy"),
        "arc_challenge": scores.get("arc_challenge"),
        "hellaswag": scores.get("hellaswag"),
        "raw_scores": scores,
        "anomalies": receipt_result["anomalies"],  # from receipt_runner
        "timestamp": datetime.now().isoformat()
    }
```

### Wire ExperimentManager.log_cycle() into EvolutionEngine

**In EvolutionWithLogging.run_waterfall()**:

```python
# Inject experiment manager reference
self.evolution._experiment_manager = self.exp_manager
self.evolution._current_experiment = self.experiment
```

**In EvolutionEngine.run_waterfall()**:

```python
for cycle in range(cycles):
    # ... merge, evaluate, sort ...
    
    # Log cycle results using the injected manager
    if hasattr(self, '_experiment_manager'):
        models_data = [
            {
                "name": m['name'],
                "score": m['score'],
                "method": m.get('method'),
                "method_params": m.get('method_params'),
                "parents": m.get('parents'),
                "benchmark": m.get('benchmark'),  # Full dict from evaluate()
                "anomalies": m.get('anomalies'),
                "cycle": cycle + 1,
                "timestamp": datetime.now().isoformat()
            }
            for m in population
        ]
        self._experiment_manager.log_cycle(
            self._current_experiment,
            cycle_num=cycle + 1,
            models=models_data,
            best_model=population[0]
        )
```

---

## Files to Touch (Minimal Changes)

| File | What | Why | Effort |
|------|------|-----|--------|
| `BenchmarkEvaluator.evaluate()` | Return dict instead of float; use receipt_runner | Anomaly detection + full scores | 30 min |
| `EvolutionEngine` | Add injection points for exp manager | Genealogy logging | 20 min |
| `EvolutionWithLogging` | Inject experiment manager into engine | Wire genealogy | 10 min |
| `EvolutionEngine.run_waterfall()` | Add log_cycle() call + model metadata | Actually track genealogy | 20 min |
| `app.py` | (Already done in previous session) | Recipe → validation → evolution | 0 min |

**Total: ~80 minutes (~1.5 hours)**

---

## What NOT to Build

❌ **DO NOT build:**
- Custom anomaly detection (receipt_runner already does it)
- Custom benchmarking harness (lm-eval already integrated)
- Custom logging system (ExperimentManager already exists)

✅ **DO build:**
- Integration layer (wire receipt_runner into BenchmarkEvaluator)
- Genealogy injection (wire ExperimentManager into EvolutionEngine)
- Model metadata enrichment (add method, params, cycle, timestamp)

---

## Expected Result After Wiring

**Evolution cycle with full genealogy:**

```
Cycle 1, Parent 0 (Qwen-0.5B × Mistral-7B) → SLERP merge
  ↓
Model: mutant_c1_p0_slerp
  ├─ Evaluate via BenchmarkEvaluator.evaluate()
  │  ├─ Perplexity: 8.234 ✓
  │  ├─ receipt_runner: 65.33 scaled_score
  │  ├─ Anomalies: [{"type": "below_chance", ...}]
  │  └─ Per-task: {arc_easy: 0.612, arc_challenge: 0.751, hellaswag: 0.740}
  │
  └─ Store metadata:
     {
       "name": "mutant_c1_p0_slerp",
       "cycle": 1,
       "parents": ["Qwen-0.5B", "Mistral-7B"],
       "method": "slerp",
       "method_params": {"alpha": 0.5},
       "score": 0.748,
       "benchmark": {
         "perplexity": 8.234,
         "arc_easy": 0.612,
         "arc_challenge": 0.751,
         "hellaswag": 0.740,
         "anomalies": [...]
       },
       "timestamp": "2025-01-15T14:23:45",
       "culled": false,
       "reason_kept": "Best this cycle"
     }
  ↓
ExperimentManager.log_cycle() saves to:
  exp['paths']['results']/benchmarks.json
  + exp['paths']['merged_models']/mutant_c1_p0_slerp/model_metadata.json
  ↓
UI displays genealogy tree with anomalies
```

---

## MergeBench vs. Our Hybrid Approach

| Aspect | MergeBench | Our Hybrid |
|--------|-----------|-----------|
| Merge algorithms | ✅ 20+ built-in | ✅ Same (via FusionBench + MergeKit) |
| Evaluation | ✅ Integrated | ✅ receipt_runner + lm-eval |
| Anomaly detection | ✅ Some built-in | ✅ receipt_runner (better) |
| Genealogy tracking | ❌ NOT built-in | ✅ Via ExperimentManager |
| Experiment management | ❌ NOT designed for evolution loops | ✅ ExperimentManager ready |
| UI integration | ❌ Heavy | ✅ Lightweight, Streamlit-native |
| Code size | 1000+ lines | ~200 lines new code |
| Dependency weight | Heavy | Light (we already use all libs) |

**Verdict**: MergeBench is a complete research suite. We need a **simple evolution harness**. Hybrid approach is better.

---

## Why NOT Just Use MergeBench Wholesale

1. **Over-engineered**: MergeBench is designed for research experiments, not real-time UI evolution loops
2. **Learning curve**: MergeBench config system is complex
3. **Inflexible genealogy**: MergeBench doesn't track parent chains the way we need
4. **No experiment folders**: MergeBench doesn't create the `breeding_vat/data/experiments/{name}/` structure we need
5. **UI disconnect**: MergeBench results don't naturally fit Streamlit

Our ExperimentManager is already optimized for:
- ✅ Experiment folder creation
- ✅ Master log streaming
- ✅ Dated folders
- ✅ Resumable state
- ✅ Genealogy tracking

We just need to **wire it to the evolution loop**, not replace it.

---

## Action Plan

**Phase 1 (Next 1.5 hours): Wire Everything**

1. **Enhance BenchmarkEvaluator.evaluate()** to use receipt_runner for anomalies
2. **Add injection points to EvolutionEngine** for experiment manager reference
3. **Wire log_cycle() calls** after each cycle
4. **Enrich model metadata** with method, params, cycle info
5. **Test end-to-end** with 2 models, 3 cycles

**Result**: Full genealogy tracking + anomaly detection, zero external dependencies beyond what we already use.

---

## TL;DR

| Question | Answer |
|----------|--------|
| Use MergeBench for genealogy? | ❌ NO — too heavy, designed for research |
| Use MergeBench for anomalies? | ✅ Kind of — but receipt_runner.py is already better |
| Use MergeBench for merging? | ✅ YES — we already do (FusionBench integration) |
| Easiest path forward? | ✅ Hybrid: reuse receipt_runner, wire ExperimentManager, minimal new code |
| Time to completion? | ~1.5 hours for full genealogy + anomaly detection |

---

**End of Analysis**

Recommendation: **Do NOT detour to MergeBench. Wire ExperimentManager instead. ~90 min finish.**
