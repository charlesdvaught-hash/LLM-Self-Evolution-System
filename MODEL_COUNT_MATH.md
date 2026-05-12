# Model Count & Resource Math

## Quick Reference

### The Basic Math

```
Total Models = Merge Techniques × Evolution Rounds

Examples:
─────────

3 techniques × 3 rounds = 9 models
4 techniques × 5 rounds = 20 models
5 techniques × 4 rounds = 20 models
7 techniques × 3 rounds = 21 models
```

### VRAM Estimates

```
Per Operation:
──────────────
Merge:     1-2 GB (released after)
Eval:      0.5-1 GB (released after)
SAE:       1-2 GB (released after)
Logs/Temp: 0.5 GB (persistent)

Total per model: ~1.5 GB active VRAM

Cumulative:
───────────
N models × 1.5 GB = Total VRAM used over time
(Sequential, but logs accumulate)
```

### Storage Estimates

```
Per Model:
──────────
Weights:       3-5 GB (model size)
Config:        10 MB
Logs:          50 MB
Benchmarks:    5 MB
Total:         ~3.5-5.5 GB per model

Full Experiment (Keep All):
──────────────────────────
20 models × 5 GB = 100 GB storage
Logs:                 1 GB
Configs:              0.2 GB
Total:                ~101 GB

Smart Cleanup (Keep Top 3):
──────────────────────────
3 models × 5 GB = 15 GB
Logs (all):        1 GB
Master log:        0.1 GB
Total:             ~16 GB
```

---

## Scenario Planning

### Scenario A: Fast Discovery (Limited Time)

**Goal**: Test quickly, don't care about perfection  
**Time Budget**: 1 hour  
**VRAM**: 24 GB  

**Granular Settings**:
```
Techniques:    3 (linear, task_arithmetic, ties_linear)
Rounds:        2
Population:    3
Culling:       50%
Benchmark:     Quick (5-10 q/category)
Total models:  3 × 2 = 6
VRAM:          6 × 1.5 = 9 GB active
Time:          6 × 5 = 30 min
Storage:       ~30 GB (if kept all)
```

**Exploratory Settings**:
```
Goal:          "Quick test of 3B reasoning"
Time budget:   1 hour
Risk:          Aggressive
Result:        AI picks 2-3 techniques, 1-2 rounds
               Total: 4-6 models
               Time: 20-30 min
```

**Verdict**: ✅ Comfortable fit

---

### Scenario B: Deep Quality (Unlimited Time & VRAM)

**Goal**: Find the absolute best model, exhaustive search  
**Time Budget**: 4 hours  
**VRAM**: 48 GB  

**Granular Settings**:
```
Techniques:    7 (all available)
Rounds:        4
Population:    5
Culling:       30%
Benchmark:     Thorough (200-500 q/category)
Total models:  7 × 4 = 28
VRAM:          28 × 1.5 = 42 GB active
Time:          28 × 10 = 280 min (4.7 hours)
Storage:       ~150 GB (if kept all)
```

**Cleanup Strategy**:
```
After each round:
- Archive cycle 1-3 models to external drive
- Keep cycle 4 (latest) locally
- Reduces storage to ~30 GB active
```

**Verdict**: ✅ Fits but close to VRAM limit

---

### Scenario C: Constrained (Limited VRAM)

**Goal**: Best quality given tight constraints  
**VRAM**: 8 GB (laptop)  
**Time**: 1 hour  

**Granular Settings**:
```
Techniques:    2 (task_arithmetic, regmean)
Rounds:        2
Benchmark:     Quick (5 q/category)
Total models:  2 × 2 = 4
VRAM:          4 × 1.5 = 6 GB active ✓
Time:          4 × 5 = 20 min ✓
Storage:       ~20 GB
```

**Cleanup Immediately After**:
```
- Delete old models, keep best: 5 GB
- Clear evaluation caches: 2 GB
- Free space for next run: 5 GB available
```

**Verdict**: ✅ Tight but viable with cleanup

---

### Scenario D: Medium Exploration (Typical User)

**Goal**: Balanced exploration with good quality  
**VRAM**: 16 GB  
**Time**: 2 hours  

**Granular Settings**:
```
Techniques:    4 (linear, task_arithmetic, regmean, ties_linear)
Rounds:        3
Benchmark:     Balanced (50-100 q/category)
Total models:  4 × 3 = 12
VRAM:          12 × 1.5 = 18 GB... wait, over budget!
```

**Adjustment**:
```
Revised:
Techniques:    3 (linear, task_arithmetic, regmean)
Rounds:        3
Total models:  3 × 3 = 9
VRAM:          9 × 1.5 = 13.5 GB ✓
Time:          9 × 5 = 45 min ✓
```

**Verdict**: ✅ Reduced to fit, still good exploration

---

## Decision Tree: How to Choose Settings

```
START
│
├─ "How much VRAM?"
│  ├─ 8 GB ──→ 2 techniques, 2 rounds max
│  ├─ 16 GB ──→ 3 techniques, 3 rounds max
│  ├─ 24 GB ──→ 4-5 techniques, 3-4 rounds
│  └─ 48+ GB ──→ 6+ techniques, 4-5 rounds
│
├─ "How much time?"
│  ├─ 30 min ──→ Quick benchmark
│  ├─ 1 hour ──→ Balanced benchmark
│  ├─ 2 hours ──→ Balanced + SAE
│  └─ 4+ hours ──→ Thorough benchmark
│
├─ "How many techniques?"
│  ├─ "I know exactly" ──→ Granular (pick specific)
│  ├─ "I'm exploring" ──→ Exploratory (AI picks)
│  └─ "No idea" ──→ Balanced (3-4 presets)
│
├─ "Keep old models?"
│  ├─ Yes ──→ Need extra storage
│  ├─ No ──→ Archive/delete after each cycle
│  └─ Top 3 only ──→ ~16 GB per 12 models
│
└─ END: Settings locked in
```

---

## Common Mistakes & Fixes

### Mistake 1: Too Many Techniques + Rounds

**User**: "Let me try 8 techniques for 5 rounds!"  
**Math**: 8 × 5 = 40 models, 60 GB VRAM  
**Fix**: AI says "That's 40 models, 60 GB VRAM, 4 hours. Do you have that?" → User: "No" → Adjust to 3 × 3 = 9

### Mistake 2: Forgetting Logs Accumulate

**User**: "I'll generate 10 models, clean up after"  
**Reality**: Logs alone = 500 MB, configs = 100 MB  
**Fix**: Warning shows "~10 GB total storage per 10 models", user understands scope

### Mistake 3: Underestimating SAE Overhead

**User**: "SAE shouldn't add much time"  
**Reality**: SAE = 5-10 min per model  
**Fix**: Calculation: "3 rounds with SAE = 45 min base + 15 min SAE = 60 min total"

### Mistake 4: Running Out of VRAM Mid-Evolution

**User**: "I have 8 GB VRAM, let me try 5 techniques × 3 rounds"  
**Reality**: Mid-eval, OOM error  
**Fix**: Granular mode shows warning BEFORE starting: "This will use ~22.5 GB, you have 8 GB. Won't fit!"

---

## Model Count Explanations for Users

### Simple Case

```
User: "I want to try 3 techniques over 2 rounds"

Explanation:
────────────
Round 1:
- Start with base models (Qwen-0.5B, Mistral-7B)
- Try: linear, task_arithmetic, regmean
- Generate: 3 new models
- Evaluate: all 3
- Cull: keep best 1-2

Round 2:
- Start with survivors from round 1
- Try: linear, task_arithmetic, regmean on winners
- Generate: 3 new models
- Total new so far: 6 models

Total: 6 new models from 2 techniques × 2 rounds
```

### Complex Case with Population

```
User: "4 techniques, 3 rounds, population 5, 50% cull"

Explanation:
────────────
Population size: 5 models per round
Per round, you try 4 techniques on different parent pairs:
- Technique 1: Parents A+B → Model 1
- Technique 2: Parents A+B → Model 2
- Technique 3: Parents C+D → Model 3
- Technique 4: Parents C+D → Model 4
+ 1 from previous generation = 5 total

Cull 50%: Keep best 2-3

Round 2: Start with 2-3 winners, repeat
Round 3: Start with 2-3 winners, repeat

Total new models: ~12-16 (depending on culling)
```

---

## VRAM Breakdown During Execution

```
Timeline for 1 Model (typical 3B merge):
─────────────────────────────────────────

T+0:    Start merge                      1 GB used
T+2:    Peak VRAM during merge          2.5 GB used
T+5:    Merge done, save weights        2 GB (disk)
        + Load for eval
        
T+6:    Eval benchmark starts          2 GB VRAM
T+15:   Peak during eval               2.5 GB VRAM
T+20:   Eval done, save results         0.5 GB (disk)
        
T+21:   All released                    0 GB VRAM

Total time: ~20 min
Peak VRAM: 2.5 GB (transient)
Permanent storage: 5 GB weights + 0.05 GB logs

For 12 models sequentially:
────────────────────────────
Total time: 12 × 20 = 240 min (4 hours)
Max VRAM ever: 2.5 GB
Total storage: 12 × 5 = 60 GB
```

---

## Storage Cleanup Options

### Option 1: Aggressive (Keep Only Best)
```
After experiment:
- Delete all models except best
- Keep master log only
- Result: 5.5 GB per 12 models → 1 GB kept
- Trade-off: Can't revisit old models
```

### Option 2: Conservative (Keep Top 3)
```
After experiment:
- Keep top 3 models by score
- Keep all logs
- Result: 16.5 GB per 12 models
- Trade-off: Uses more storage, preserves options
```

### Option 3: Archive (Move Old to External)
```
After each round:
- Archive round 1-2 models to USB/S3
- Keep round 3 (latest) local
- Result: 15 GB local, unlimited external
- Trade-off: Slower to revisit old
```

### Option 4: Checkpoint (Save Strategy, Delete Weights)
```
After experiment:
- Save best model ID + merge config
- Delete weights (can regenerate)
- Keep logs + configs
- Result: 0.5 GB per 12 models
- Trade-off: Can't run best model, only recipe
```

---

## Formulas for Estimation

```
Total New Models
════════════════
Formula: N = T × R
Where:
  T = Merge techniques selected
  R = Evolution rounds
  
Example: 5 techniques × 3 rounds = 15 models


VRAM Usage (Sequential)
══════════════════════
Formula: V_active = 2.5 GB (peak per operation)
         V_cumulative = N × 1.5 GB (over time)
         
Where N = total models

Example: 15 models = 2.5 GB peak, 22.5 GB cumulative


Time Estimate
═════════════
Formula: T_total = (N × B) + (R × S)
Where:
  N = total models
  B = benchmark time per model (5-30 min)
  R = rounds
  S = SAE overhead per round (5-10 min)
  
Example: 15 models, balanced bench (10 min/model), 3 rounds, SAE:
         T = (15 × 10) + (3 × 7) = 150 + 21 = 171 min (2.9 hours)


Storage (Keep All)
══════════════════
Formula: S = N × 5 + L
Where:
  N = total models
  5 = GB per model (weights + config)
  L = logs (~1 GB total)
  
Example: 15 models = (15 × 5) + 1 = 76 GB
```

---

## Quick Lookup Table

```
Tech  Rounds  Models  VRAM_Est  Time_Est  Storage
────  ──────  ──────  ────────  ────────  ─────────
2     2       4       6 GB      30 min    20 GB
2     3       6       9 GB      45 min    30 GB
3     2       6       9 GB      45 min    30 GB
3     3       9       13.5 GB   1.2 h     45 GB
3     4       12      18 GB     1.6 h     60 GB
4     2       8       12 GB     1 h       40 GB
4     3       12      18 GB     1.6 h     60 GB
4     4       16      24 GB     2.1 h     80 GB
5     3       15      22.5 GB   2 h       75 GB
5     4       20      30 GB     2.7 h     100 GB
```

**Note**: Time estimates assume balanced benchmarks (10 min/model). Quick=5 min, Thorough=20 min.

---

**Users now understand exactly how many models they'll generate and what resources are needed.**
