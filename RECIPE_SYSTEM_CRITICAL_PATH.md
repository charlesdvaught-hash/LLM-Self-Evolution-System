# RECIPE_SYSTEM_CRITICAL_PATH.md

**Date**: Current session  
**Status**: Recipe system exists but NOT wired into UI execution  
**Priority**: IMMEDIATE — this is the backbone that enables fabrication

---

## The Gap

**What exists:**
- `RecipeExecutor` (breeding_vat/modules/recipe_executor.py) — validates, builds config
- `RecipeValidator` (breeding_vat/modules/merge/recipe_validator.py) — checks constraints
- `EvolutionEngine` (breeding_vat/modules/merge/evolution.py) — runs breed/cull loop
- `ExperimentManager` (breeding_vat/modules/experiment_manager.py) — tracks genealogy
- UI form in `app.py` — collects user parameters

**What's missing:**
- **Connection**: UI form → recipe JSON → RecipeExecutor.validate() → RecipeExecutor.build_evolution_config() → EvolutionEngine.run_waterfall()

Currently, UI and evolution engine are disconnected. Recipe infrastructure exists but is unused.

---

## The Flow (Target)

```
User fills UI form:
├─ Base models: [Qwen-0.5B, Mistral-7B]
├─ Methods: [SLERP, TIES]
├─ Cycles: 3
├─ Culling rate: 50%
└─ [START FABRICATION]

UI generates recipe JSON:
{
  "metadata": {"name": "test_run", "goal": "reasoning"},
  "evolution": {
    "base_models": ["Qwen/Qwen2.5-0.5B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
    "merge_methods": {
      "slerp": {"enabled": true},
      "ties": {"enabled": true}
    },
    "num_cycles": 3,
    "culling_rate": 50
  },
  "evaluation": {"tier": "standard"},
  "finetuning": {"enabled": false},
  "assay": {"enabled": false},
  "sae": {"enabled": false}
}
  ↓
RecipeExecutor.validate(recipe)
  ├─ RecipeValidator checks: method allowed? params in bounds? no shell injection?
  └─ Returns: valid=True or raises ValidationError
  ↓
RecipeExecutor.build_evolution_config(recipe)
  └─ Converts recipe → {base_models, num_cycles, culling_rate, merge_methods, method_params, eval_tier, ...}
  ↓
EvolutionEngine.run_waterfall(config)
  ├─ Cycle 1: Merge 2 models (random method) → benchmark → cull
  ├─ Cycle 2: Merge winners + new random crossovers → benchmark → cull
  ├─ Cycle 3: Same
  └─ Return best model + genealogy
  ↓
ExperimentManager.log_cycle()
  ├─ Save each model: metadata (parents, method, params, scores, anomalies)
  ├─ Track genealogy: model A parent of model B?
  ├─ Preserve everything (even culled models)
  └─ Update UI live
  ↓
UI displays:
├─ Real-time cycle progress
├─ Population fitness chart
├─ Current best model
├─ Genealogy tree (clickable)
└─ Anomaly alerts (⚠️ score jumped 20%, etc.)
```

---

## Critical Files to Wire

### 1. app.py (breeding_vat/ui/app.py)

**Current state:**
- Has UI form for goal, base_models, methods, cycles
- Calls MergeAdvisor.generate_recipe() (but doesn't use result to drive execution)
- Calls ExperimentManager but doesn't validate recipe first

**Changes needed:**
```python
# In evolution tab, START FABRICATION button:

recipe = {
    "metadata": {
        "name": st.session_state.exp_name,
        "goal": current_goal,
        "timestamp": datetime.now().isoformat()
    },
    "evolution": {
        "base_models": selected_base_models,
        "merge_methods": {m: {"enabled": True} for m in selected_methods},
        "num_cycles": num_cycles,
        "culling_rate": culling_rate
    },
    "evaluation": {"tier": benchmark_tier},
    "finetuning": {"enabled": False},
    "assay": {"enabled": False},
    "sae": {"enabled": False}
}

# NEW: Validate recipe before execution
executor = RecipeExecutor()
validation = executor.validate(recipe)

if not validation.valid:
    st.error(f"Recipe invalid: {validation.errors}")
else:
    # NEW: Build evolution config from validated recipe
    evo_config = executor.build_evolution_config(recipe)
    
    # EXISTING: Run evolution (but now with validated config)
    best_model = evo_logged.run_waterfall(
        base_models=evo_config["base_models"],
        num_cycles=evo_config["num_cycles"],
        culling_rate=evo_config["culling_rate"],
        allowed_methods=evo_config["merge_methods"],
        # ... other params from evo_config
    )
```

### 2. RecipeExecutor (breeding_vat/modules/recipe_executor.py)

**Current state:**
- Exists and is functional
- Methods: validate(), build_evolution_config(), build_finetuning_config(), build_assay_config()

**Already ready** — no changes needed. Just needs to be imported and called from app.py.

### 3. RecipeValidator (breeding_vat/modules/merge/recipe_validator.py)

**Current state:**
- Validates method, parameters, shell injection, required fields
- Called by RecipeExecutor.validate()

**Already ready** — just needs to be in the chain.

### 4. EvolutionEngine (breeding_vat/modules/merge/evolution.py)

**Current state:**
- Has run_waterfall() method that takes base_models, num_cycles, culling_rate, allowed_methods, etc.

**Changes needed:**
- Ensure it accepts config dict OR individual params (check signature)
- Ensure it calls ExperimentManager.log_cycle() after each cycle (genealogy tracking)
- Ensure benchmark results are captured with anomalies (quirk detection)

### 5. ExperimentManager (breeding_vat/modules/experiment_manager.py)

**Current state:**
- Tracks experiments, cycles, models
- Has save_model() and log_cycle() methods

**Verify:**
- Does log_cycle() save full model metadata (parents, method, params, scores, anomalies)?
- Does it track genealogy (which model is parent of which)?
- Does it preserve culled models (not delete them)?

---

## Test Case (Verification)

**Setup:** 2 base models, SLERP+TIES, 3 cycles

**Expected genealogy:**
```
Cycle 0: [Qwen-0.5B, Mistral-7B] (2 models)
  ↓
Cycle 1: Merge parents with random method
  → mutant_c1_p0_slerp (score: X)
  → mutant_c1_p1_ties (score: Y)
  Culling: keep top 1 (or both if scores close)
  ↓
Cycle 2: Winners breed again + new random crossovers
  → mutant_c2_p0_* (score: Z)
  → mutant_c2_p1_*
  → mutant_c2_p2_* (if population grows)
  Culling: keep top ~2
  ↓
Cycle 3: Same
  Final population: 2-4 survivors
  Total genealogy: ~16 models (exponential growth with culling)
```

**Verification checklist:**
- [ ] UI generates valid recipe JSON
- [ ] RecipeExecutor.validate() passes
- [ ] RecipeExecutor.build_evolution_config() creates correct EvolutionEngine config
- [ ] EvolutionEngine runs 3 cycles
- [ ] Each cycle produces new models (branching)
- [ ] Culling removes bottom 50%
- [ ] All models saved (even culled ones)
- [ ] Genealogy tracks parents for each model
- [ ] Benchmark captures anomalies (score jumps, perplexity changes, etc.)
- [ ] UI updates live (cycle counter, best model, population size)

---

## Benchmark (Per-Model, ~2-3 min)

Each merged model gets:

```python
# In BenchmarkEvaluator or similar
def quick_benchmark(model_path):
    results = {}
    anomalies = []
    
    # Perplexity check (15s) — catches broken merges
    ppl = compute_perplexity(model_path)
    results["perplexity"] = ppl
    if ppl > threshold:
        anomalies.append("⚠️ Perplexity spiked (structural damage?)")
    
    # Arc Easy (30s)
    ae = eval_on_task(model_path, "arc_easy")
    results["arc_easy"] = ae["accuracy"]
    
    # Arc Challenge (30s)
    ac = eval_on_task(model_path, "arc_challenge")
    results["arc_challenge"] = ac["accuracy"]
    if ac["accuracy"] >> ae["accuracy"]:
        anomalies.append("⚠️ arc_challenge >> arc_easy (specialization?)")
    
    # HellaSwag (1min)
    hs = eval_on_task(model_path, "hellaswag")
    results["hellaswag"] = hs["accuracy"]
    
    # Quirk detection
    if score_jumped_20_percent_from_parent:
        anomalies.append("⚠️ Score jumped 20% vs parent")
    
    return {
        "scores": results,
        "anomalies": anomalies,
        "timestamp": datetime.now().isoformat()
    }
```

---

## Genealogy Tracking (Existing)

ExperimentManager already tracks:
- model_id, parents, method, parameters, scores, cycle_number, status (kept/culled)

**Ensure it saves:**
```json
{
  "model_id": "mutant_c2_p1_slerp",
  "cycle": 2,
  "parents": ["mutant_c1_p0_ties", "Mistral-7B"],
  "method": "slerp",
  "method_params": {"alpha": 0.5},
  "benchmark": {
    "perplexity": 8.234,
    "arc_easy": 0.612,
    "arc_challenge": 0.751,
    "hellaswag": 0.740
  },
  "anomalies": [
    "⚠️ arc_challenge much higher than arc_easy",
    "✓ perplexity stable"
  ],
  "culled": false,
  "reason_kept": "Best score this cycle (0.748)",
  "timestamp": "2025-01-15T14:23:45"
}
```

---

## Import Chain (Next Session)

In app.py, add:
```python
from breeding_vat.modules.recipe_executor import RecipeExecutor
from breeding_vat.modules.merge.recipe_validator import RecipeValidator
```

Then use:
```python
executor = RecipeExecutor()
validation = executor.validate(recipe)
if validation.valid:
    config = executor.build_evolution_config(recipe)
    # Pass config to EvolutionEngine
```

---

## Next Steps (Ordered)

1. **Wire RecipeExecutor into app.py** (see section "Critical Files to Wire" → app.py)
2. **Test validation** — try invalid recipe, ensure error is caught
3. **Test config building** — ensure recipe → evo_config conversion is correct
4. **Run local test** — 2 models, SLERP+TIES, 3 cycles
5. **Verify genealogy** — check database/logs for full lineage
6. **Verify benchmarks** — ensure anomalies are captured
7. **Verify UI updates** — live progress, final tree

**Time estimate**: 2-3 hours to wire + test locally

---

## Known Working Components

- ✅ RecipeExecutor (validate, build config)
- ✅ RecipeValidator (check constraints)
- ✅ EvolutionEngine (breed/cull loop)
- ✅ ExperimentManager (genealogy)
- ✅ TaskRunner (Docker orchestration)
- ✅ BenchmarkEvaluator (scoring)
- ✅ UI form (collect params)

**Just needs**: UI → recipe → validator → execution connection

---

## Design Principle

Recipe system enables:
- **Reproducibility** — save recipe, run again with identical results
- **Auditability** — every decision (merge method, params) recorded
- **Experimentation** — swap methods/params in recipe, re-run
- **Branching evolution** — recipe drives exponential population growth with culling

This is THE backbone of the fabricator.
