# GET THE PIPELINE WORKING — Complete Implementation Guide

**Goal**: Go from current state → fully functional LLM evolution system  
**Time**: 2-3 hours of implementation + 1-2 hours of local testing  
**Result**: Reproducible model breeding with genealogy tracking and anomaly detection

---

## WHAT WE HAVE ✅

1. **UI Complete** (Streamlit app.py) — 600+ lines, 7 tabs, all controls present
2. **Recipe System** (wired) — UI → JSON → validated → evolution
3. **Evolution Engine** — Merges, benchmarks, culls, but genealogy broken
4. **Docker Orchestration** (scripts/manager.py) — Image building, container reuse
5. **Experiment Manager** — Folder creation, logging structure ready
6. **Benchmark Evaluator** — Perplexity + lm-eval integrated

## WHAT'S MISSING ❌

1. **Genealogy Logging** — EvolutionEngine never calls log_cycle()
2. **Anomaly Detection** — Benchmarks return only float, not full dict
3. **Model Metadata** — Missing method, parents, cycle, timestamp
4. **UI Genealogy Display** — Tab 2 has placeholder but no data source
5. **Import Issues** — Some modules may not be importable
6. **Docker Images** — Need to be built (setup.bat does this)

---

## STEP-BY-STEP IMPLEMENTATION

### PHASE 0: Pre-Flight Check (15 minutes)

**0.1: Verify Python environment**

```bash
python --version  # Should be 3.9+
pip list | findstr streamlit torch transformers  # Verify key packages
```

**0.2: Verify Docker**

```bash
docker --version
docker ps  # Should not error
```

**0.3: Check file structure**

```bash
ls breeding_vat/ui/app.py         # UI exists
ls breeding_vat/modules/           # All modules present
ls scripts/manager.py              # Container manager exists
```

**If any file missing**: 
- Check Map.json for file inventory
- Project structure may have issues; cannot proceed

---

### PHASE 1: Fix Genealogy Wiring (90 minutes)

This is the CRITICAL path. Without this, genealogy is broken.

**1.1: Update BenchmarkEvaluator.evaluate()** (~30 min)

**File**: `breeding_vat/modules/benchmark/evaluator.py`

**Change**: Return dict instead of float

```python
# OLD:
def evaluate(self, model_name: str, experiment_id: Optional[int] = None,
             tier: str = "standard", skip_perplexity: bool = False) -> float:
    # ... returns avg score as float (e.g., 0.748)

# NEW:
def evaluate(self, model_name: str, experiment_id: Optional[int] = None,
             tier: str = "standard", skip_perplexity: bool = False) -> Dict:
    """
    Returns: {
        "score": 0.748,
        "perplexity": 8.234,
        "arc_easy": 0.612,
        "arc_challenge": 0.751,
        "hellaswag": 0.740,
        "raw_scores": {...},
        "anomalies": [...],
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
    
    # Tier 0: Perplexity
    if not skip_perplexity:
        passed, ppl, reason = self.run_perplexity(model_name)
        result["perplexity"] = ppl
        logger.info(f"Perplexity [{model_name}]: {ppl:.1f}")
        if not passed:
            result["anomalies"].append({
                "type": "perplexity_fail",
                "detail": f"Perplexity {ppl} exceeds {PERPLEXITY_FAIL_THRESHOLD}"
            })
            return result
    
    # Tier 1-3: lm-eval
    scores = self.run_lm_eval(model_name, tier=tier)
    result["raw_scores"] = scores
    
    if not scores:
        result["anomalies"].append({"type": "eval_failure", "detail": "lm-eval returned no results"})
        return result
    
    # Extract per-task scores
    result["arc_easy"] = scores.get("arc_easy")
    result["arc_challenge"] = scores.get("arc_challenge")
    result["hellaswag"] = scores.get("hellaswag")
    
    # Anomaly detection: task disparity
    if result.get("arc_challenge") and result.get("arc_easy"):
        diff = result["arc_challenge"] - result["arc_easy"]
        if diff > 0.2:
            result["anomalies"].append({
                "type": "specialization",
                "detail": f"arc_challenge ({result['arc_challenge']:.3f}) >> arc_easy ({result['arc_easy']:.3f})"
            })
    
    # Composite score
    valid_scores = [s for s in [result.get("arc_easy"), result.get("arc_challenge"), 
                                 result.get("hellaswag")] if s is not None]
    result["score"] = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    
    return result  # CHANGED: now returns dict
```

**1.2: Update EvolutionEngine** (~40 min)

**File**: `breeding_vat/modules/merge/evolution.py`

**Change 1**: Add injection points (line ~20):

```python
class EvolutionEngine:
    def __init__(self, runner: TaskRunner):
        self.runner = runner
        # ... existing code ...
        
        # NEW: Injection points for genealogy tracking
        self._experiment_manager = None
        self._current_experiment = None
```

**Change 2**: Update evaluate() call to handle dict (line ~55):

```python
# OLD:
score = self.evaluate(child_name)
logger.info(f"  Score: {score:.4f}")

# NEW:
eval_result = self.evaluate(child_name)
score = eval_result.get("score", 0.0)  # Extract score from dict
logger.info(f"  Score: {score:.4f}")
```

**Change 3**: Enrich offspring metadata (line ~60):

```python
# OLD:
offspring.append({"name": child_name, "score": score, "parent": parent_model})

# NEW:
offspring.append({
    "name": child_name,
    "score": score,
    "parent": parent_model,
    "parents": [parent_model, sibling_model],  # NEW: both parents
    "method": method,  # NEW
    "method_params": {},  # NEW
    "benchmark": eval_result,  # NEW: full eval results
    "anomalies": eval_result.get("anomalies", [])  # NEW
})
```

**Change 4**: Add log_cycle() call (after culling, line ~75):

```python
# After: num_to_keep = max(1, int(len(offspring) * (1 - culling_rate / 100)))
#        population = offspring[:num_to_keep]
# ADD:

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
```

**1.3: Wire EvolutionWithLogging** (~20 min)

**File**: `breeding_vat/modules/evolution/evolution_with_logging.py`

**Change**: Inject manager before evolution (line ~75):

```python
# Before: best_model = self.evolution.run_waterfall(...)
# ADD:

# NEW: Inject experiment manager for genealogy tracking
self.evolution._experiment_manager = self.exp_manager
self.evolution._current_experiment = self.experiment
```

---

### PHASE 2: Add Genealogy Display to UI (60 minutes)

**File**: `breeding_vat/ui/app.py`

**Location**: Tab 2 (Lineage), after existing code

The UI already has placeholder code. Just need to populate it with genealogy data:

```python
# In tab2 (Lineage tab), replace placeholder with:

import pandas as pd

exp = st.session_state.current_experiment
benchmark_db_path = exp["paths"]["benchmark_db"]

try:
    if os.path.exists(benchmark_db_path):
        with open(benchmark_db_path, 'r') as f:
            benchmarks = json.load(f)
        
        if benchmarks.get("cycles"):
            # Collect all models from all cycles
            rows = []
            for cycle_data in benchmarks["cycles"]:
                for model in cycle_data.get("models", []):
                    rows.append({
                        "Cycle": cycle_data["cycle"],
                        "Model": model["name"][-30:],
                        "Score": model.get("score", 0),
                        "Method": model.get("method", "?").upper(),
                        "Parents": ", ".join([p[-15:] for p in model.get("parents", [])]),
                        "Anomalies": len(model.get("anomalies", []))
                    })
            
            if rows:
                df = pd.DataFrame(rows)
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Models", len(rows))
                with col2:
                    st.metric("Best Score", f"{df['Score'].max():.4f}")
                with col3:
                    st.metric("Avg Score", f"{df['Score'].mean():.4f}")
                with col4:
                    st.metric("Cycles", len(benchmarks["cycles"]))
                
                st.markdown("---")
                
                # Lineage table
                st.markdown("### Genealogy Table")
                st.dataframe(
                    df.sort_values("Score", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Score trajectory chart
                st.markdown("### Score Over Time")
                best_per_cycle = df.groupby("Cycle")["Score"].max()
                st.line_chart(best_per_cycle)
                
                # Anomalies breakdown
                st.markdown("### Anomalies by Cycle")
                anomaly_df = df.groupby("Cycle")["Anomalies"].sum()
                st.bar_chart(anomaly_df)
            else:
                st.info("Evolution has completed but no models were kept.")
        else:
            st.info("No cycles completed yet. Run evolution to populate genealogy.")
    else:
        st.info("Genealogy database not created yet. Run evolution first.")
except Exception as e:
    st.error(f"Error loading genealogy: {e}")
```

---

### PHASE 3: Fix Import Issues (30 minutes)

**3.1: Check all imports in app.py**

```python
# Run this to verify all imports work:
python -c "
from breeding_vat.modules.merge.advisor import MergeAdvisor
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.benchmark.evaluator import BenchmarkEvaluator
print('All imports OK')
"
```

**If any import fails**:

```bash
# Install missing package
pip install <package-name>

# Or check __init__.py files exist:
ls breeding_vat/modules/__init__.py
ls breeding_vat/modules/merge/__init__.py
ls breeding_vat/modules/benchmark/__init__.py
ls breeding_vat/modules/evolution/__init__.py
```

**3.2: Create missing __init__.py files if needed**

```python
# Touch breeding_vat/modules/__init__.py
# Touch breeding_vat/modules/merge/__init__.py
# Touch breeding_vat/modules/benchmark/__init__.py
# Touch breeding_vat/modules/evolution/__init__.py
```

---

### PHASE 4: Build Docker Images (30 minutes)

**4.1: Run setup.bat**

```bash
setup.bat
```

This will:
- Check Docker is installed
- Build 4 Docker images:
  - breeding-vat-ui
  - breeding-vat-merge
  - breeding-vat-eval
  - breeding-vat-sae
- Output success or errors

**4.2: Verify images were built**

```bash
docker images | findstr breeding-vat
```

Should see 4 images. If any missing, check output from setup.bat.

---

## FINAL VERIFICATION (1 hour)

### Part A: Syntax & Import Check (5 min)

```bash
python -m py_compile breeding_vat/modules/merge/evolution.py
python -m py_compile breeding_vat/modules/evolution/evolution_with_logging.py
python -m py_compile breeding_vat/modules/benchmark/evaluator.py
python -c "from breeding_vat.ui.app import *; print('✓ UI imports OK')"
```

### Part B: Start UI (2 min)

```bash
run.bat
```

This will:
- Check Docker is running
- Launch container on http://localhost:8501
- Open browser automatically

### Part C: Create Test Experiment (10 min)

In UI:

1. **Sidebar → New Mission**:
   - Goal: "Test genealogy tracking"
   - Click "🚀 Initialize"
   - See: "✅ Mission active: test_genealogy_..."

2. **Main tab → Evolution**:
   - Base Models: Select 2 (Qwen-0.5B, Mistral-7B)
   - Methods: Select 2 (SLERP, TIES)
   - Cycles: 1 (for testing)
   - Culling: 50%
   - Click "▶️ START EVOLUTION"

### Part D: Monitor Evolution (30 min)

Watch the logs:
- `ℹ️ Starting evolution: 1 cycles`
- `📊 Benchmark tier: standard | perplexity gate: on`
- `[cycle 1]` → merging → evaluating → culling

Expected output (1 cycle with 2 methods):
- ~5-10 merges attempted
- ~2-4 successful
- ~2-4 evaluated
- 1-2 kept (50% culling)

### Part E: Check Genealogy File (5 min)

After evolution completes:

```bash
# Navigate to experiment folder
cd breeding_vat/data/experiments/<name>/results/

# Check genealogy
cat benchmarks.json

# Should see:
# {
#   "cycles": [
#     {
#       "cycle": 1,
#       "models": [
#         {
#           "name": "mutant_c1_p0_slerp",
#           "score": 0.748,
#           "method": "slerp",
#           "parents": [...],
#           "anomalies": [...],
#           ...
#         }
#       ]
#     }
#   ]
# }
```

### Part F: Verify UI Tab 2 (5 min)

Back in UI:

1. Click Tab 2 (🌳 Lineage)
2. Should see:
   - **Total Models**: 2-4
   - **Best Score**: 0.xxx
   - **Genealogy Table**: List of all models with parents
   - **Score Over Time**: Chart showing progression
   - **Anomalies**: Flags for each cycle

If you see data → ✅ GENEALOGY WORKING

If blank → Check breeding_vat/data/experiments/<name>/results/benchmarks.json exists

---

## TROUBLESHOOTING

### Issue: "RecipeExecutor not found"

```bash
# Missing import or file
pip install -e .  # or python setup.py develop
```

### Issue: "Docker: not running"

```bash
# Start Docker Desktop manually
# Wait 30 seconds for daemon to start
# Then run.bat again
```

### Issue: "Port 8501 already in use"

```bash
# Kill existing container
docker ps  # Find breeding-vat-ui
docker stop <container_id>
docker rm <container_id>
# Then run.bat
```

### Issue: "CUDA out of memory"

```bash
# Set model eval tier to "fast" (fewer tasks, less VRAM)
# Or reduce batch size
# Or skip perplexity check (checkbox in sidebar)
```

### Issue: "No models in genealogy table"

```bash
# Check evolution completed without error
docker logs breeding-vat-ui  # Look for errors

# Check genealogy file exists
ls breeding_vat/data/experiments/*/results/benchmarks.json

# If file exists but empty, ExperimentManager.log_cycle() not being called
# Re-check PHASE 1 changes were applied correctly
```

---

## SUCCESS CRITERIA

✅ **You have a working pipeline when:**

1. `run.bat` starts without errors
2. UI loads at http://localhost:8501
3. Can create new experiment
4. Can select models and methods
5. "START EVOLUTION" button runs without crashing
6. Evolution completes in ~10-30 min (1 cycle, 2-4 models)
7. Tab 2 (Lineage) shows table with models + scores
8. benchmarks.json file created with full genealogy
9. Each model has: name, score, method, parents, anomalies
10. Can repeat evolution and see different merges

---

## EXPECTED TIMING

| Phase | Task | Time | Total |
|-------|------|------|-------|
| 0 | Pre-flight checks | 15 min | 15 min |
| 1 | Fix genealogy wiring (code) | 90 min | 105 min |
| 2 | Add genealogy UI display | 60 min | 165 min |
| 3 | Fix imports | 30 min | 195 min |
| 4 | Build Docker images | 30 min | 225 min |
| — | **Subtotal: Implementation** | **225 min** | — |
| 5 | Verify & test (1 cycle) | 60 min | 285 min |
| — | **Total: Ready to Use** | **~4.5 hours** | — |

---

## NEXT: ADVANCED FEATURES (Optional)

After getting genealogy working, you can add:

1. **Fine-tuning per cycle** (optional checkbox) → breeding_vat/modules/train/
2. **ASSAY integration** (3-axis measurement) → already in UI, just need integration
3. **SAE layer analysis** → already partially wired
4. **Method-specific parameters** → Recipe system handles this
5. **Resumable experiments** → ExperimentManager supports this

---

**You are now ready to BUILD. Start with PHASE 0 (pre-flight checks) and work sequentially.**

Any issues, refer back to MISSING_INTEGRATIONS.md and EXACT_CODE_CHANGES.md for reference code.
