# MISSING INTEGRATIONS — Critical Gaps Found

**Date**: Current session (continuation)  
**Status**: ❌ Critical gaps identified that prevent genealogy tracking and anomaly capture

---

## Gap 1: EvolutionEngine Does NOT Call ExperimentManager.log_cycle()

**Current state**:
- EvolutionEngine.run_waterfall() runs cycles
- Each model evaluated, but results NOT logged to ExperimentManager
- ExperimentManager.log_cycle() exists but is NEVER called
- This means: **genealogy is not captured in experiment folders**

**Evidence**:
- Line 55 in evolution.py: `self.runner.log_model()` logs to a database, not ExperimentManager
- ExperimentManager.log_cycle() in experiment_manager.py is defined but unreachable from evolution loop
- No reference to ExperimentManager in evolution.py

**Impact**:
- ❌ benchmarks.json never populated
- ❌ master.log never updated with cycle results
- ❌ model_id, parents, method, scores never saved to experiment folder
- ❌ Genealogy tree cannot be visualized
- ❌ Test case checklist items 1.3, 1.4 will fail

**Fix needed**:
```python
# In EvolutionEngine.run_waterfall(), after each cycle:
# (between culling and next cycle)

for cycle in range(cycles):
    # ... merge, evaluate, sort ...
    
    # MISSING: Log cycle to ExperimentManager
    if hasattr(self, '_experiment_manager') and self._experiment_manager:
        models_data = [
            {
                "name": m['name'],
                "score": m['score'],
                "method": m.get('method', 'unknown'),
                "parents": m.get('parents', [])
            }
            for m in population
        ]
        best = population[0]
        self._experiment_manager.log_cycle(
            self._current_experiment,
            cycle_num=cycle + 1,
            models=models_data,
            best_model=best
        )
```

---

## Gap 2: Benchmark Results Do NOT Capture Anomalies

**Current state**:
- BenchmarkEvaluator returns a score (float)
- Anomalies are not captured (score jumps, perplexity spikes, specialization)
- No structure for storing: perplexity, arc_easy, arc_challenge, hellaswag separately
- No structure for: anomalies list, quirk detection

**Evidence**:
- Line 32 in evolution.py: `score = self.evaluate(child_name)` — only returns float
- BenchmarkEvaluator.evaluate() interface not checked, but likely returns only a single score
- No anomaly detection in the benchmark loop

**Impact**:
- ❌ Benchmark quirks never detected
- ❌ benchmarks.json has no per-task scores (perplexity, arc_easy, etc.)
- ❌ Cannot flag "arc_challenge >> arc_easy" specialization
- ❌ Cannot flag "perplexity spiked vs parent"
- ❌ Cannot flag "score jumped 20%"
- ❌ Test case checklist items 1.2, 1.3 will fail

**Fix needed**:
```python
# BenchmarkEvaluator.evaluate() should return dict instead of float:
{
    "score": 0.748,  # composite score
    "perplexity": 8.234,
    "arc_easy": 0.612,
    "arc_challenge": 0.751,
    "hellaswag": 0.740,
    "anomalies": [
        "⚠️ arc_challenge much higher than arc_easy (specialization?)",
        "✓ perplexity stable"
    ]
}
```

Then in evolution.py, store full results in model metadata.

---

## Gap 3: Model Genealogy Metadata Incomplete

**Current state**:
- Each offspring stored as: `{"name": ..., "score": ..., "parent": ...}`
- Missing: method used, method parameters, timestamp, cycle number, anomalies
- Missing: grandparent chain (who was parent's parent?)

**Impact**:
- ❌ Cannot reconstruct full genealogy tree (only knows immediate parent, not chain)
- ❌ Method information lost
- ❌ Cannot query "all SLERP merges" later
- ❌ Cannot track method effectiveness

**Fix needed**:
```python
# Each offspring should include:
{
    "name": "mutant_c2_p1_regmean",
    "score": 0.751,
    "parent": "mutant_c1_p0_ties",
    "method": "regmean",  # MISSING
    "method_params": {"reg": 1e-6},  # MISSING
    "cycle": 2,  # MISSING
    "timestamp": "2025-01-15T14:23:45",  # MISSING
    "parents": ["mutant_c1_p0_ties", "mutant_c1_p2_slerp"],  # MISSING (both parents)
    "benchmark": { /* full results with anomalies */ },  # MISSING
    "anomalies": [...]  # MISSING
}
```

---

## Gap 4: EvolutionWithLogging Does NOT Integrate Genealogy

**Current state**:
- EvolutionWithLogging wraps EvolutionEngine
- Sets up experiment folder, master log
- Calls EvolutionEngine.run_waterfall()
- **But does not wire genealogy tracking into the engine**

**Evidence**:
- run_waterfall() calls evolution.run_waterfall() but doesn't pass experiment_manager
- No mechanism to signal to EvolutionEngine: "Hey, log each cycle to this experiment folder"
- EvolutionEngine has no reference to ExperimentManager

**Impact**:
- ❌ Even though ExperimentManager exists, evolution never uses it
- ❌ Genealogy data flows to database (`self.runner.log_model()`), not experiment folder
- ❌ Cannot access genealogy from Streamlit UI (wrong storage location)

**Fix needed**:
```python
# In EvolutionWithLogging.run_waterfall(), BEFORE calling evolution:

# Inject experiment manager reference
self.evolution._experiment_manager = self.exp_manager
self.evolution._current_experiment = self.experiment

# Then in EvolutionEngine, after each cycle:
if hasattr(self, '_experiment_manager'):
    self._experiment_manager.log_cycle(...)
```

---

## Gap 5: UI Does NOT Display Genealogy or Anomalies

**Current state**:
- Streamlit UI has placeholder for genealogy tree (tab 2)
- No data source connected
- Anomalies never displayed

**Impact**:
- ❌ User cannot see the model lineage
- ❌ User cannot see "why was this model culled?"
- ❌ User cannot study quirks and failures
- ❌ Fabrication lab aesthetic broken (transparent genealogy was core promise)

**Fix needed**:
- Connect UI to ExperimentManager
- Load genealogy.json / benchmarks.json from experiment folder
- Display genealogy tree (visualization)
- Display anomalies per model

---

## Wiring Checklist — What We DID vs. What We MISSED

| Task | Done? | Status |
|------|-------|--------|
| Recipe JSON generation (UI → recipe) | ✅ YES | COMPLETE (this session) |
| Recipe validation | ✅ YES | COMPLETE (this session) |
| Recipe → evolution config | ✅ YES | COMPLETE (this session) |
| EvolutionEngine receives recipe config | ✅ YES | READY (via app.py) |
| EvolutionEngine calls log_cycle() | ❌ NO | **MISSING** |
| Benchmark returns full results (not just score) | ❌ NO | **MISSING** |
| Anomaly detection in benchmark | ❌ NO | **MISSING** |
| Model metadata includes method, params, timestamp | ❌ NO | **MISSING** |
| EvolutionWithLogging injects experiment manager | ❌ NO | **MISSING** |
| ExperimentManager.log_cycle() called each cycle | ❌ NO | **MISSING** |
| Genealogy saved to experiment folder | ❌ NO | **MISSING** |
| UI displays genealogy tree | ❌ NO | **MISSING** |
| UI displays anomalies | ❌ NO | **MISSING** |

---

## Prioritized Fixes (ordered by criticality)

### CRITICAL (blocks genealogy tracking)

1. **Wire ExperimentManager into EvolutionEngine**
   - Add `_experiment_manager` and `_current_experiment` instance variables to EvolutionEngine
   - EvolutionWithLogging injects these before calling run_waterfall()
   - File: breeding_vat/modules/merge/evolution.py

2. **Add log_cycle() call to EvolutionEngine.run_waterfall()**
   - After culling, before next cycle
   - Log cycle results to experiment folder
   - File: breeding_vat/modules/merge/evolution.py

3. **Verify BenchmarkEvaluator returns full results, not just score**
   - Should return dict with: score, perplexity, arc_easy, arc_challenge, hellaswag, anomalies
   - File: breeding_vat/modules/benchmark/evaluator.py

4. **Update model metadata collection**
   - Include: method, method_params, timestamp, cycle, both parents, benchmark dict, anomalies
   - File: breeding_vat/modules/merge/evolution.py

### HIGH (blocks UI display of genealogy)

5. **Connect Streamlit UI to genealogy data**
   - Load from exp['paths']['results']/benchmarks.json
   - Display genealogy tree with parent/child relationships
   - Show anomalies per model
   - File: breeding_vat/ui/app.py (tab 2 - Lineage)

### MEDIUM (test verification)

6. **Test end-to-end**
   - Run: 2 base models, SLERP+TIES, 3 cycles
   - Verify: genealogy.json in experiment folder
   - Verify: ~16 models in genealogy, 2-4 survivors
   - Verify: all anomalies captured

---

## Code Locations for Fixes

**File 1: breeding_vat/modules/merge/evolution.py**
- Add instance variables: `_experiment_manager`, `_current_experiment`
- Add log_cycle() call after culling (line ~70)
- Enhance model metadata with method, params, timestamp, cycle
- Include benchmark results + anomalies in model dict

**File 2: breeding_vat/modules/benchmark/evaluator.py**
- Verify evaluate() returns dict, not float
- Include: perplexity, arc_easy, arc_challenge, hellaswag, anomalies
- Implement anomaly detection (score jumps, specialization, structural damage)

**File 3: breeding_vat/modules/evolution/evolution_with_logging.py**
- Inject experiment_manager: `self.evolution._experiment_manager = self.exp_manager`
- Inject current_experiment: `self.evolution._current_experiment = self.experiment`

**File 4: breeding_vat/ui/app.py**
- Tab 2 (Lineage): Load genealogy from benchmarks.json
- Display tree visualization of parent/child relationships
- Display anomalies per model with severity flags

---

## Example: Fixed Flow

```
User clicks "START EVOLUTION"
  ↓
build_recipe_from_ui() + validate() ✅ (DONE)
  ↓
EvolutionEngine receives recipe config ✅ (READY)
  ↓
EvolutionWithLogging injects experiment_manager ❌ (NEED FIX)
  ↓
For each cycle:
  ├─ Merge models (random method)
  ├─ Evaluate: BenchmarkEvaluator.evaluate() returns:
  │  {
  │    "score": 0.751,
  │    "perplexity": 8.234,
  │    "arc_easy": 0.612,
  │    "arc_challenge": 0.751,
  │    "hellaswag": 0.740,
  │    "anomalies": ["⚠️ arc_challenge >> arc_easy", "✓ perplexity stable"]
  │  } ❌ (NEED FIX)
  ├─ Store model metadata:
  │  {
  │    "name": "mutant_c1_p0_slerp",
  │    "score": 0.751,
  │    "method": "slerp",
  │    "parents": ["Qwen-0.5B", "base_model_2"],
  │    "cycle": 1,
  │    "timestamp": "...",
  │    "benchmark": {...full results...},
  │    "anomalies": [...]
  │  } ❌ (NEED FIX)
  ├─ Cull bottom 50%
  ├─ log_cycle() to ExperimentManager ❌ (NEED FIX)
  │  └─ Saves to exp['paths']/benchmarks.json
  └─ Update UI with progress
  ↓
UI displays genealogy tree ❌ (NEED FIX)
  ├─ Shows all models with parent/child links
  ├─ Highlights survivors vs. culled
  └─ Shows anomalies per model
```

---

## Impact Assessment

**If these gaps are NOT fixed**:
- ❌ Genealogy never captured (core feature missing)
- ❌ No anomaly detection (transparency promise broken)
- ❌ UI cannot display lineage tree (fabrication lab aesthetic broken)
- ❌ User has no insight into evolution decisions (why culled? why kept?)
- ❌ No reproducibility (no way to study past experiments)
- ❌ System appears broken (data lost at end of evolution)

**If these gaps ARE fixed**:
- ✅ Full genealogy tree captured and displayed
- ✅ Anomalies flagged and studied
- ✅ User understands evolution decisions
- ✅ Fabrication lab aesthetic intact
- ✅ Reproducible, auditable experiments
- ✅ System feels complete and professional

---

## Time Estimate for Fixes

- EvolutionEngine integration: 30 min
- BenchmarkEvaluator verification: 20 min
- Model metadata enhancement: 20 min
- UI genealogy display: 1 hour
- End-to-end testing: 1 hour

**Total: ~3 hours to complete Phase 1**

---

**End of MISSING_INTEGRATIONS.md**

This document captures the critical gaps discovered while cross-checking against CLAUDE.md and RECIPE_SYSTEM_CRITICAL_PATH.md.
