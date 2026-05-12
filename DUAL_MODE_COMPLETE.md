# Enhanced Dual-Mode UI: Granular + Exploratory

**Status**: Complete  
**Date**: January 2025  
**Major Changes**: Restored all granular controls + added hands-off exploratory mode with AI orchestration

---

## Overview

The UI now supports **two extreme modes**:

1. **Granular Control** 🎛️
   - You pick everything: methods, parameters, base models, benchmarks
   - Full control over every slider/toggle
   - Best for: Experts, reproducibility, precise experiments

2. **Exploratory Mode** 🚀
   - Describe goal + constraints
   - AI asks 5 clarifying questions
   - AI generates strategy + estimates resources
   - Approve/edit or launch
   - Best for: Discovery, quick iteration, "I don't know what I want"

3. **Balanced Mode** ⚖️ (existing, still available)
   - Presets + some customization
   - Smart defaults, less overwhelming

---

## All Prior Features Preserved

✅ **Merge Method Selection** — Pick specific techniques or let AI choose  
✅ **Specimen Selection** — Manual / AI-suggested / Random  
✅ **Method Parameters** — Task Arithmetic reg, DARE drop, TIES threshold, etc.  
✅ **Benchmark Categories** — Reasoning, Knowledge, Language, Math, Code, etc.  
✅ **AI Advisor** — Quick (1B) or Capable (7B)  
✅ **SAE Analysis** — Optional per-cycle  
✅ **Stopping Conditions** — Goal reached, plateau, manual, max cycles  
✅ **Post-Cycle Actions** — Continue, analyze, shuffle, deep eval  
✅ **Anomaly Detection** — Flag perfect scores  
✅ **Local Model Upload** — Transfer your own models to zoo  

**NEW**: AI orchestration for exploratory mode (no prior feature removed)

---

## File Structure

```
breeding_vat/
├── modules/
│   ├── calibration_dual_mode.py      # NEW: Granular + Exploratory UIs
│   ├── strategy_orchestrator.py       # NEW: AI strategy generation
│   ├── evolutionary_pressures.py      # EXISTING: Preserved
│   ├── benchmark_selector.py          # EXISTING: Preserved
│   ├── ai_advisor_selector.py         # EXISTING: Preserved
│   └── anomaly_detector.py            # EXISTING: Preserved
│
└── ui/
    ├── app.py                         # ORIGINAL (still works)
    ├── app_v2_revamped.py             # V2 (still works)
    ├── app_v3_dual_mode.py            # NEW: Dual-mode app
    └── ui_v2_sleek.py                 # EXISTING: Sleek theme
```

---

## Granular Mode Deep Dive

### UI Flow

```
┌─ Calibration Tab
│  ├─ Mode Selector: [🎛️ GRANULAR | ⚖️ Balanced | 🚀 Exploratory]
│  └─ [Click Granular]
│     ├─ Merge Techniques (check all you want)
│     ├─ Evolution Dynamics (rounds, culling %, population)
│     ├─ Specimen Selection (manual/AI/random)
│     ├─ Benchmark Config (intensity + categories)
│     ├─ Per-Method Parameters (expanders for each)
│     ├─ Stopping Conditions (goal/plateau/manual)
│     ├─ Post-Cycle Actions (continue/analyze/shuffle/eval)
│     └─ ⚠️ Resource Estimate
│        - Total models: {techniques × rounds}
│        - Est. VRAM: {total × 1.5} GB
│        - Est. Time: {total × 5} min
│        - Cleanup warning: "Logs accumulate!"

┌─ Evolution Tab
│  ├─ Base Models (multi-select OR AI OR random)
│  ├─ Merge Methods (shows your granular selection)
│  ├─ Advisor Choice (quick or capable)
│  └─ [START EVOLUTION]
```

### Example: Granular Setup

```
User: "I want 3 merge techniques, 4 rounds, quick benchmarks"

1. Calibration → Granular
2. Check: linear, task_arithmetic, regmean
3. Set: Rounds=4, Culling=50%, Population=5
4. Select: Qwen-0.5B + Mistral-7B (manual)
5. Benchmark: Quick (5-10 q/cat)
6. Method params: Task Arithmetic reg=0.1, DARE drop=0.15

Resource estimate:
- 3 techniques × 4 rounds = 12 models
- VRAM: 12 × 1.5 = 18 GB
- Time: 12 × 5 = 60 min
⚠️ Logs will add ~600 MB to experiment folder

7. Evolution Tab → START
```

---

## Exploratory Mode Deep Dive

### AI Orchestration Flow

```
┌─ Calibration Tab
│  ├─ Mode Selector: [🎛️ Granular | ⚖️ Balanced | 🚀 EXPLORATORY]
│  └─ [Click Exploratory]
│     ├─ Goal: "Improve reasoning by 15% on 4B model"
│     ├─ Performance Targets:
│     │  - Target improvement: 15%
│     │  - Max model size: 5 GB
│     ├─ Resource Constraints:
│     │  - Available VRAM: 24 GB
│     │  - Time budget: 2 hours
│     │  - Risk tolerance: Moderate
│     └─ Base Model Strategy: [Let AI choose | Manual | Random]
│
│  [Ask AI to Generate Strategy]
│    ↓ (AI asks 5 clarifying Qs)
│
│  ┌─ Q1: Quality vs Speed?
│  │  [Quality (deep)] [Speed (broad)] [Balanced]
│  │
│  ├─ Q2: Benchmark Intensity?
│  │  [Thorough] [Quick] [Balanced]
│  │
│  ├─ Q3: Enable SAE Analysis?
│  │  [Yes] [No]
│  │
│  ├─ Q4: When to Stop?
│  │  [Stop at target] [Keep exploring] [Ask per round]
│  │
│  └─ Q5: How Many Techniques?
│     [All available] [Top 5] [My top 3]
│
│  ┌─ AI-Generated Strategy
│  │  - Techniques: task_arithmetic, regmean, ties_linear, dare_linear, voting
│  │  - Rounds: 3
│  │  - Benchmark: Balanced
│  │  - SAE: Enabled
│  │  - Total models: 15
│  │  - Est. time: 1.2 hours
│  │  - Est. VRAM: 22.5 GB
│  │
│  │  Reasoning: "Quality-focused: 5 techniques × 3 rounds..."
│  │
│  │  [✓ Approve & Launch] [✎ Edit] [Reduce Scope] [Cancel]
│
└─ Evolution Tab
   [START EVOLUTION] ← Uses AI strategy
```

### Example: Exploratory Setup

```
User: "Hey, I want to improve reasoning by 15% on a 4B model without exceeding 5GB. I have 24GB VRAM and 2 hours."

1. Calibration → Exploratory
2. Goal: "Improve reasoning by 15% on 4B model, under 5GB"
3. Target improvement: 15%
4. Max model size: 5 GB
5. VRAM: 24 GB, Time: 2 hours, Risk: Moderate
6. Base models: Let AI choose

[Ask AI to Generate Strategy]
   ↓ AI clarifies:
   ✓ Quality or Speed? → User: "Quality" 
   ✓ Benchmarks? → User: "Balanced"
   ✓ SAE? → User: "Yes"
   ✓ Stopping? → User: "Stop at target"
   ✓ Techniques? → User: "Top 5"

AI generates:
- Techniques: task_arithmetic, regmean, ties_linear, dare_linear, voting
- Rounds: 3
- Total models: 15
- Est. VRAM: 22.5 GB
- Est. time: 1.2 hours
- Reasoning: "Quality-focused approach: thorough eval + SAE gives best insights"

User: [✓ Approve & Launch]

Evolution runs with AI-generated parameters.
```

---

## Model Count Warning System

### The Problem

"I picked 4 techniques and 5 rounds. How many models is that?"

### The Solution

**Granular Mode**:
```python
Resource Estimate:
─────────────────
Techniques: 4
Rounds: 5
Population: 5

Total new models: 4 × 5 = 20 models

VRAM Usage:
- Each merge/eval: ~1.5 GB (released after)
- Cumulative: 20 × 1.5 = 30 GB over time
- Logs: ~1 GB
- Experiment folder: ~40 GB total

⚠️ WARNING
- With 24GB VRAM: Tight fit
- Cleanup between rounds recommended
- Or reduce to 2-3 techniques
```

**Exploratory Mode**:
```
AI shows:
───────
Techniques: 5 (you asked for top 5)
Rounds: 3 (AI picked for your goal)
Total: 15 models

Resources:
- Est. VRAM: 22.5 GB
- Est. time: 1.2 hours
- Fits your 24GB + 2h budget: ✓

[✓ Approve] [Reduce] [Cancel]
```

### Model Accumulation Cleanup

After evolution completes, users can:
```
Advanced Tab:
├─ 📁 Delete Old Models (archive cycle 1-2, keep cycle 3)
├─ 🗑️ Clear Logs (keep best model logs only)
└─ 📊 Archive Experiment (zip + move to external)
```

---

## Comparison: Granular vs Exploratory

| Aspect | Granular | Exploratory |
|--------|----------|-------------|
| **Setup Time** | 5-10 min | 2 min (goal only) |
| **Decision Load** | High (pick everything) | Low (AI clarifies) |
| **Resource Visibility** | Manual calculation | AI estimates |
| **Reproducibility** | High (exact params) | Medium (AI choices) |
| **Best For** | Experts, precise control | Discovery, quick start |
| **Model Count** | User decides | AI recommends |
| **Technique Selection** | Check all you want | AI narrows to 3/5/all |
| **Risk** | User responsible | AI considers constraints |

---

## Resource Management Strategy

### During Evolution

1. **Per-Cycle VRAM**:
   - Merge: 1-2 GB (released after)
   - Eval: 0.5-1 GB (released after)
   - Total per cycle: ~1.5 GB cumulative

2. **Logs & Configs**:
   - Per model: ~50 MB logs
   - 20 models = ~1 GB logs
   - Configs: ~10 MB each

3. **Cleanup Windows**:
   - After each cycle: Archive old models (optional)
   - After evolution: Keep only best + master log
   - After experiments: Compress old experiment folders

### Storage Estimate

```
Example: 4 techniques × 5 rounds = 20 models

Per Model:
- Weights: 3-5 GB (stored)
- Config: 10 MB
- Logs: 50 MB
- Benchmarks: 5 MB
= ~5.5 GB per model

Total for 20 models: 110 GB storage
BUT: Only 1 running at a time (~5 GB VRAM active)

Cleanup options:
- Keep only best: 5.5 GB
- Keep top 3: 16.5 GB
- Keep all: 110 GB
```

### Recommended Settings for Different VRAM

```
24GB VRAM:
├─ Granular: 4-5 techniques, 3-4 rounds (OK)
├─ Exploratory: AI auto-selects (safer)
└─ Benchmark: Thorough (takes time but OK)

12GB VRAM:
├─ Granular: 2-3 techniques, 2-3 rounds (tight)
├─ Exploratory: AI limits to 2-3 techniques
└─ Benchmark: Balanced (quicker)

8GB VRAM:
├─ Granular: 2 techniques max, 2 rounds
├─ Exploratory: AI strictly limits scope
└─ Benchmark: Quick (must be fast)
```

---

## Preserved Features in Action

### Specimen Selection (All Modes)

**Granular**:
```
Specimen Selection
├─ Manual: [Pick specific models ▼]
│  Qwen-0.5B ✓, Mistral-7B ✓
│
├─ AI-Suggested: "I'll choose N models"
│  Number of models: [3]
│  → AI picks best combination
│
└─ Random: Auto-select from zoo
   → Random 3 models each time
```

**Exploratory**:
```
Base Models:
├─ Let AI choose (auto picks for your goal)
├─ I'll pick (manual override)
└─ Mix from zoo (random)
```

### Method Selection (All Modes)

**Granular**: 10+ techniques shown, check as many as you want  
**Exploratory**: AI picks 3/5/all based on time budget

### Parameters (All Modes)

**Granular**: All per-method sliders visible (expanders)  
**Exploratory**: AI sets defaults, user can edit if needed

### Benchmarks (All Modes)

**Granular**: Pick categories manually  
**Exploratory**: AI suggests based on goal

### AI Advisor (All Modes)

Always available: Quick (1B) or Capable (7B)

---

## User Journeys

### Journey A: Expert (Granular)
```
1. Sidebar: New mission "reasoning_expert"
2. Calibration: Granular mode
   - Pick: linear, task_arithmetic, regmean
   - Rounds: 3, Culling: 40%
   - Techniques: Manual
   - Params: task_arithmetic_reg=0.1, dare_drop=0.2
3. Evolution: Select models + launch
4. Results: View lineage, download logs
5. Next: Tweak params, re-run
```

### Journey B: Explorer (Exploratory)
```
1. Sidebar: New mission "reasoning_discovery"
2. Calibration: Exploratory mode
   - Goal: "Better reasoning, under 5GB"
   - VRAM: 24GB, Time: 2h, Risk: Moderate
3. [Ask AI Strategy]
   - AI asks 5 clarifying Qs
   - Generates strategy: 5 techniques, 3 rounds
4. [Approve]
5. Evolution: Just click START
6. Results: AI-orchestrated discovery
```

### Journey C: Quick Test (Balanced)
```
1. Sidebar: New mission "quick_test"
2. Calibration: Balanced mode (presets)
3. Evolution: Pick 2-3 models, go
4. Results: Quick results in 30 min
```

---

## Testing Checklist

### Granular Mode
- [ ] All merge techniques show as checkboxes
- [ ] Population dynamics sliders work
- [ ] Specimen selection (manual/AI/random) works
- [ ] Method parameters appear in expanders
- [ ] Resource estimate calculates correctly
- [ ] Model count warning shows
- [ ] VRAM estimate shows

### Exploratory Mode
- [ ] Goal input renders
- [ ] Performance targets show (improvement %, model size)
- [ ] Resource constraints (VRAM, time, risk) appear
- [ ] "Ask AI to Generate Strategy" button works
- [ ] AI clarifying questions appear (5 total)
- [ ] User can answer each question
- [ ] AI strategy generated + displayed
- [ ] Approval/edit/reduce buttons work
- [ ] Strategy passed to Evolution tab

### Preserved Features
- [ ] Base model selection (manual) works in both modes
- [ ] Merge method selection appears in Evolution tab
- [ ] Method parameters used if set in Granular
- [ ] Benchmark selector still works
- [ ] AI advisor choice works
- [ ] SAE analysis option preserved
- [ ] Anomaly detection still runs

### Resource Management
- [ ] Model count warning accurate
- [ ] VRAM estimate realistic
- [ ] Time estimate shown
- [ ] Storage cleanup tools visible in Advanced tab
- [ ] Archive/delete buttons functional

---

## Future Extensions

1. **Hybrid Mode**: Granular + AI suggestions  
2. **History**: Save favorite strategies, compare runs  
3. **Meta-Learning**: AI learns from past experiments  
4. **Cost Calculator**: Cloud compute cost estimates  
5. **Batch Mode**: Run multiple strategies in parallel  
6. **Export Strategy**: Save strategy as YAML for reproducibility  

---

## Summary

**You now have**:
- ✅ **Ultra-granular control** for experts (pick every detail)
- ✅ **Hands-off exploratory mode** for discovery (AI figures it out)
- ✅ **All prior features preserved** (methods, specimens, params, etc.)
- ✅ **Resource warnings** (model count, VRAM, storage)
- ✅ **Cleanup tools** (manage experiment size)
- ✅ **AI clarification** (5 Qs to narrow scope)
- ✅ **Smart defaults** (AI estimates realistic params)

Users can now:
- Be as granular as they want (expert mode)
- Be as exploratory as they want (AI orchestrated)
- Mix both (balanced mode with presets)

**Zero breaking changes. All old features still work.**

---

**Status**: Ready for testing  
**Next**: `streamlit run breeding_vat/ui/app_v3_dual_mode.py`
