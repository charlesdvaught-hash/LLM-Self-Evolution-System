# READY TO RUN — What's Complete vs What's Next

---

## ✅ IMPLEMENTED (3 files modified, 100+ lines of code)

### 1. breeding_vat/modules/benchmark/evaluator.py
**What changed**: evaluate() method
- ❌ Was: Returns `float` (score only)
- ✅ Now: Returns `Dict` with full evaluation results
- ✅ Added: Anomaly detection (5 types)
- ✅ Added: Per-task scores (arc_easy, arc_challenge, hellaswag)
- ✅ Added: Timestamp for each evaluation

**Test it**: 
```python
result = evaluator.evaluate(model_name)
assert isinstance(result, dict)
assert "score" in result
assert "anomalies" in result
assert "perplexity" in result
```

### 2. breeding_vat/modules/merge/evolution.py
**What changed**: EvolutionEngine class
- ✅ Added: `_experiment_manager` injection point
- ✅ Added: `_current_experiment` injection point
- ✅ Changed: evaluate() call to handle dict return
- ✅ Enhanced: Offspring metadata (added parents, method, benchmark, anomalies)
- ✅ Added: log_cycle() call after culling
- ✅ Added: datetime import for timestamps

**Test it**:
```python
engine = EvolutionEngine(runner)
assert engine._experiment_manager is None  # Before injection
engine._experiment_manager = manager       # After injection
assert engine._experiment_manager is not None
```

### 3. breeding_vat/modules/evolution/evolution_with_logging.py
**What changed**: run_waterfall() method
- ✅ Added: Manager and experiment injection (3 lines)
- ✅ Now: Evolution engine has genealogy capability

**Test it**:
```python
evo_logged = EvolutionWithLogging(engine, manager, exp)
# Manager is automatically injected before evolution runs
```

---

## ⏳ NEXT PHASE (NOT STARTED YET)

### Phase 2: UI Genealogy Display (60 minutes)
**File**: breeding_vat/ui/app.py, Tab 2 (Lineage)

What to add:
```python
# In Tab 2, after line with "Genealogy and performance history":

import pandas as pd

exp = st.session_state.current_experiment
benchmark_path = exp["paths"]["benchmark_db"]  # or results/benchmarks.json

if os.path.exists(benchmark_path):
    with open(benchmark_path) as f:
        benchmarks = json.load(f)
    
    # Create table from cycles
    rows = []
    for cycle in benchmarks.get("cycles", []):
        for model in cycle.get("models", []):
            rows.append({
                "Cycle": cycle["cycle"],
                "Model": model["name"][-30:],
                "Score": model.get("score", 0),
                "Method": model.get("method", "?").upper(),
                "Parents": ", ".join([p[-15:] for p in model.get("parents", [])]),
                "Anomalies": len(model.get("anomalies", []))
            })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df.sort_values("Score", ascending=False))
        st.line_chart(df.groupby("Cycle")["Score"].max())
```

### Phase 3: Docker Images (30 minutes)
```bash
setup.bat
# Builds:
# - breeding-vat-ui:latest
# - breeding-vat-merge:latest  
# - breeding-vat-eval:latest
# - breeding-vat-sae:latest
```

### Phase 4: End-to-End Test (60 minutes)
```bash
run.bat
# Then in UI:
# 1. New Mission
# 2. Select 2 base models (Qwen-0.5B, Mistral-7B)
# 3. Select 2 methods (SLERP, TIES)
# 4. Set cycles: 1
# 5. Click START EVOLUTION
# 6. Wait ~30 minutes
# 7. Check Tab 2 for genealogy table
```

---

## Current System State

### What Works Now
✅ Recipe system wired (UI → JSON → validated)
✅ Genealogy logging wired (model → benchmark → log_cycle → benchmarks.json)
✅ Anomaly detection active (5+ types detected)
✅ Model metadata enriched (parents, method, scores, anomalies)
✅ ExperimentManager ready to log
✅ All code compiles
✅ All imports work

### What Needs To Happen
❌ Build Docker images (setup.bat not run yet)
❌ Display genealogy in UI (Tab 2 still empty)
❌ Test end-to-end (haven't run actual evolution yet)

---

## To Get A Working System (Next 2.5 hours)

### Step 1: Build Docker Images (30 min)
```bash
setup.bat
```

### Step 2: Start UI (5 min)
```bash
run.bat
# Opens http://localhost:8501
```

### Step 3: Add UI Genealogy Display (60 min)
Copy the code from Phase 2 above into app.py Tab 2

### Step 4: Test (60 min)
- Create 1-cycle test
- Verify genealogy.json created
- Verify anomalies detected
- Verify UI shows results

---

## Files You Can Check Right Now

1. **breeding_vat/modules/benchmark/evaluator.py**
   - Search for: "def evaluate("
   - Should see: returns Dict, not float

2. **breeding_vat/modules/merge/evolution.py**
   - Search for: "_experiment_manager"
   - Should see: injection points and log_cycle() call

3. **breeding_vat/modules/evolution/evolution_with_logging.py**
   - Search for: "NEW: Inject"
   - Should see: manager injection code

---

## Verification Commands

```bash
# Check code compiles
python -m py_compile breeding_vat/modules/benchmark/evaluator.py
python -m py_compile breeding_vat/modules/merge/evolution.py
python -m py_compile breeding_vat/modules/evolution/evolution_with_logging.py

# Check imports work
python -c "
import sys
sys.path.insert(0, '.')
from breeding_vat.modules.benchmark.evaluator import BenchmarkEvaluator
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
print('All imports OK!')
"

# Should output: All imports OK!
```

---

## What Each Change Enables

### BenchmarkEvaluator returning dict
- ✅ Enables anomaly detection (perplexity spike, specialization, etc.)
- ✅ Enables per-task score tracking
- ✅ Enables genealogy UI to show why models were culled

### EvolutionEngine genealogy wiring
- ✅ Enables log_cycle() to be called (genealogy saved)
- ✅ Enables parent tracking
- ✅ Enables method tracking
- ✅ Enables genealogy tree visualization

### EvolutionWithLogging manager injection
- ✅ Wires everything together
- ✅ Makes genealogy logging automatic
- ✅ User doesn't have to do anything special

---

## The Genealogy Data Saved

After 1 cycle with 2 models, you'll have benchmarks.json:

```json
{
  "cycles": [
    {
      "cycle": 1,
      "models": [
        {
          "name": "mutant_c1_p0_slerp",
          "score": 0.748,
          "parents": ["Qwen-0.5B", "Mistral-7B"],
          "method": "slerp",
          "method_params": {},
          "benchmark": {
            "score": 0.748,
            "perplexity": 8.234,
            "arc_easy": 0.612,
            "arc_challenge": 0.751,
            "hellaswag": 0.740
          },
          "anomalies": [
            {
              "type": "specialization",
              "detail": "arc_challenge (0.751) >> arc_easy (0.612)"
            }
          ],
          "timestamp": "2025-01-15T14:23:45.123456",
          "culled": false
        }
      ]
    }
  ]
}
```

This data can then be displayed in UI Tab 2 with a table, chart, anomaly list.

---

## Summary

**What's Done**: Genealogy wiring is complete. Evolution can now track full lineage.

**What's Working**: All code compiles, imports work, system ready for testing.

**What's Next**: 
1. Build Docker images (setup.bat)
2. Add UI display (60 min coding)
3. Run test (60 min wait + verify)

**Time to Full System**: 2.5-3 hours more work

---

**Status**: IMPLEMENTATION COMPLETE, READY FOR TESTING PHASE
