## 🚀 Quick Start - Enhanced Breeding Vat UI

### What's New (TL;DR)

**Users can now**:
1. **Be ultra-granular** (pick every setting manually) 🎛️
2. **Be completely hands-off** (describe goal, AI figures it out) 🚀
3. **See resource estimates** (model count, VRAM, time, storage)
4. **Clean up old runs** (prevent storage bloat)

**Nothing removed** - all old features still work.

---

### Test It (30 seconds)

```bash
streamlit run breeding_vat/ui/app_v3_dual_mode.py
```

---

### How It Works

#### Granular Mode (Click "🎛️ Granular")
```
1. Pick merge techniques: linear, task_arithmetic, regmean, etc.
2. Set rounds: 3
3. See estimate: "9 models, 13.5 GB VRAM, 45 min"
4. GO!
```

#### Exploratory Mode (Click "🚀 Exploratory")
```
1. Type goal: "Improve reasoning 15% on 4B model"
2. Set VRAM: 24 GB
3. Set time: 2 hours
4. Click "Ask AI Strategy"
5. Answer 5 questions (yes/no or choose)
6. AI shows: "15 models, 22.5 GB, 1.2 hours"
7. Approve or edit
8. GO!
```

---

### Model Count Examples

```
3 techniques × 2 rounds = 6 models
→ VRAM: 9 GB
→ Time: 30 min
→ Storage: 30 GB (if kept all)

4 techniques × 3 rounds = 12 models
→ VRAM: 18 GB
→ Time: 60 min
→ Storage: 60 GB (if kept all)

5 techniques × 3 rounds = 15 models
→ VRAM: 22.5 GB
→ Time: 75 min
→ Storage: 75 GB (if kept all)
```

---

### VRAM Budget Guide

```
8 GB:   Use 2 techniques, 2 rounds max
12 GB:  Use 3 techniques, 3 rounds OK
24 GB:  Use 4-5 techniques, 3-4 rounds comfortably
48+ GB: Use 6-7 techniques, 4-5 rounds
```

---

### Cleanup (New Feature)

After evolution, go to **Advanced tab**:
- 📁 Delete Old Models (archive cycle 1-2, keep latest)
- 🗑️ Clear Logs (keep only best model)
- 📊 Archive Experiment (compress + move to external)

---

### Preserved Features (All Still Work)

✅ Method selection  
✅ Base model choice  
✅ Method parameters  
✅ Benchmarks  
✅ AI advisor  
✅ SAE analysis  
✅ Anomaly detection  
✅ Local model upload  
✅ Lineage tracking  

---

### Files Added

```
calibration_dual_mode.py     (Granular + Exploratory UIs)
strategy_orchestrator.py     (AI clarification + strategy)
app_v3_dual_mode.py          (Main app with dual modes)
```

---

### Deploy

**Keep both** (v2 + v3):
```bash
streamlit run breeding_vat/ui/app_v2_revamped.py
streamlit run breeding_vat/ui/app_v3_dual_mode.py --server.port 8502
```

**Replace when ready**:
```bash
cp breeding_vat/ui/app_v3_dual_mode.py breeding_vat/ui/app.py
```

---

### Status

✅ Ready to test  
✅ 100% backward compatible  
✅ All old experiments still work  
✅ No breaking changes  

---

**That's it. Test, collect feedback, deploy when ready.**
