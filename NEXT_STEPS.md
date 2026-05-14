# WHAT TO DO NOW — Next Steps After Implementation

**Current Status**: Phase 1 (Genealogy Wiring) COMPLETE ✅  
**Current Time**: Session end  
**Next Action**: Build Docker + Add UI display + Test

---

## IMMEDIATE NEXT STEPS (In Order)

### Step 1: Build Docker Images (30 minutes)
```bash
setup.bat
```

**What it does**:
- Checks Docker is installed
- Builds 4 images:
  - breeding-vat-ui:latest (Streamlit)
  - breeding-vat-merge:latest (MergeKit + FusionBench)
  - breeding-vat-eval:latest (lm-eval)
  - breeding-vat-sae:latest (SAE analysis)

**How to know it worked**:
```bash
docker images | findstr breeding-vat
# Should see 4 images listed
```

---

### Step 2: Start UI (5 minutes)
```bash
run.bat
```

**What it does**:
- Launches breeding-vat-ui container
- Opens http://localhost:8501 automatically
- Reuses container if healthy

**How to know it worked**:
- Browser opens to Streamlit UI
- See "🧬 The Breeding Vat" title
- Can create new mission

---

### Step 3: Add UI Genealogy Display (60 minutes)

**File to edit**: `breeding_vat/ui/app.py`

**Location**: Tab 2 "Lineage" section (around line 1000+)

**What to add**:
Copy this code into the lineage tab (replace placeholder):

```python
import pandas as pd

with tab2:
    st.markdown("## Model Lineage")
    st.markdown("Genealogy and performance history of evolved models.")
    
    exp = st.session_state.current_experiment
    benchmark_path = exp["paths"]["benchmark_db"]  # or check for benchmarks.json
    
    try:
        # Try multiple possible paths for genealogy data
        genealogy_file = None
        for candidate in [
            benchmark_path,
            os.path.join(exp["paths"]["results"], "benchmarks.json"),
            os.path.join(exp["paths"]["root"], "benchmarks.json")
        ]:
            if os.path.exists(candidate):
                genealogy_file = candidate
                break
        
        if genealogy_file:
            with open(genealogy_file, 'r') as f:
                benchmarks = json.load(f)
            
            if benchmarks.get("cycles"):
                # Collect all models from all cycles
                rows = []
                for cycle_data in benchmarks["cycles"]:
                    for model in cycle_data.get("models", []):
                        anomaly_count = len(model.get("anomalies", []))
                        rows.append({
                            "Cycle": cycle_data["cycle"],
                            "Model": model["name"][-35:],
                            "Score": model.get("score", 0),
                            "Method": model.get("method", "?").upper(),
                            "Parents": " + ".join([p.split("/")[-1][-10:] for p in model.get("parents", [])]),
                            "Anomalies": anomaly_count
                        })
                
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # Display metrics
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
                    
                    # Display genealogy table
                    st.markdown("### Genealogy Table")
                    st.dataframe(
                        df.sort_values("Score", ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Score trajectory
                    st.markdown("### Score Progression")
                    best_per_cycle = df.groupby("Cycle")["Score"].max()
                    st.line_chart(best_per_cycle)
                    
                    # Anomaly summary
                    st.markdown("### Anomalies Detected")
                    anomaly_per_cycle = df.groupby("Cycle")["Anomalies"].sum()
                    st.bar_chart(anomaly_per_cycle)
                else:
                    st.info("Evolution completed but no models kept.")
            else:
                st.info("No cycles completed yet.")
        else:
            st.info("Genealogy data not available yet.")
    except Exception as e:
        st.error(f"Error loading genealogy: {e}")
```

**How to know it worked**:
- Run UI
- Create experiment
- Run evolution (wait ~30 min)
- Go to Tab 2
- See genealogy table with models, parents, methods, scores

---

### Step 4: Create Test Experiment (60 minutes)

**In Streamlit UI**:

1. **Sidebar → New Mission**:
   - Goal: "Test genealogy tracking"
   - Click "🚀 Initialize"

2. **Main Tab (Evolution)**:
   - Base Models: Select Qwen-0.5B + Mistral-7B
   - Methods: Select SLERP + TIES
   - Cycles: Set to 1 (for quick test)
   - Culling: 50%
   - Click "▶️ START EVOLUTION"

3. **Wait**:
   - Cycle 1: ~30 minutes
   - Watch the logs update
   - See merges, evaluations, culling

4. **Verify Genealogy**:
   - Check Tab 2 (Lineage)
   - Should see genealogy table
   - Should show parents, methods, scores
   - Should show anomalies

5. **Check Files**:
   ```bash
   # In breeding_vat/data/experiments/<mission_name>/results/
   # Should have:
   # - benchmarks.json (genealogy data)
   # - master.log (timeline)
   ```

---

## EXPECTED RESULTS

### After Evolution Completes

**Genealogy Data** (benchmarks.json):
```json
{
  "cycles": [{
    "cycle": 1,
    "best_model": "mutant_c1_p0_slerp",
    "models": [
      {
        "name": "mutant_c1_p0_slerp",
        "score": 0.748,
        "parents": ["Qwen-0.5B", "Mistral-7B"],
        "method": "slerp",
        "benchmark": {
          "perplexity": 8.234,
          "arc_easy": 0.612,
          "arc_challenge": 0.751,
          "hellaswag": 0.740
        },
        "anomalies": [
          {"type": "specialization", "detail": "..."}
        ]
      }
    ]
  }]
}
```

**UI Display** (Tab 2):
- Genealogy table with 2-4 models
- Score progression chart
- Anomaly count
- Parent relationships visible

**Master Log** (master.log):
```
EVOLUTION RUN STARTED
Total cycles: 1
Base models: Qwen-0.5B, Mistral-7B
Merge methods: slerp, ties
Culling rate: 50%

Cycle 1: merging...
Cycle 1: evaluating...
Cycle 1: culling...
Best score: 0.748
Evolution complete!
```

---

## SUCCESS CRITERIA

✅ Docker images built successfully
✅ UI starts without errors
✅ Can create new experiment
✅ Evolution runs and completes
✅ Tab 2 shows genealogy table
✅ Each model has: name, parents, method, score
✅ Anomalies detected and displayed
✅ benchmarks.json created with full genealogy

---

## TROUBLESHOOTING

### Docker fails to build
```bash
# Check Docker Desktop is running
docker ps  # Should not error

# If images fail, try manual build
docker build -t breeding-vat-ui:latest -f docker/Dockerfile.ui .
docker build -t breeding-vat-merge:latest -f docker/Dockerfile.merge .
docker build -t breeding-vat-eval:latest -f docker/Dockerfile.eval .
docker build -t breeding-vat-sae:latest -f docker/Dockerfile.sae .
```

### UI doesn't start
```bash
# Check port 8501 isn't in use
netstat -ano | findstr :8501  # If shows something, port in use

# Kill old container
docker ps -a | findstr breeding-vat-ui
docker rm -f <container_id>

# Try run.bat again
run.bat
```

### Evolution takes forever
- Normal: 30 min per cycle for 2 models
- Each model: 15s perplexity + 2min lm-eval
- Set cycles to 1 for first test
- Can skip perplexity if in hurry (checkbox in sidebar)

### Tab 2 genealogy empty
- Check evolution actually completed (check Tab 1 logs)
- Check benchmarks.json exists (look in file system)
- Check file path in code matches actual path
- Refresh browser (F5)

---

## Timeline to Working System

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | Build Docker images | 30 min | ⏳ Next |
| 2 | Start UI | 5 min | ⏳ After step 1 |
| 3 | Add genealogy UI code | 60 min | ⏳ After step 2 |
| 4 | Test with 1 cycle | 60 min | ⏳ After step 3 |
| — | **Total** | **155 min** | — |

**To fully working system: ~2.5 hours**

---

## Optional Enhancements (Later)

After basic system works, can add:

1. **Method parameters** (sidebar controls for DARE drop_rate, TIES threshold, etc.)
2. **Fine-tuning** (per-cycle LoRA adaptation)
3. **ASSAY** (3-axis measurement tool)
4. **SAE analysis** (layer introspection)
5. **Receipt generation** (detailed benchmark reports)

But core genealogy will be working first.

---

## Summary

### What's Done ✅
- Genealogy wiring complete
- Code compiles and imports work
- Recipe system ready

### What's Next ⏳
1. setup.bat (build Docker)
2. Add UI genealogy display code
3. run.bat + test

### Result After 2.5 Hours
Fully working LLM fabricator with complete genealogy tracking

---

**You're ready to go. Start with `setup.bat` → `run.bat` → test.**

Good luck! 🧬
