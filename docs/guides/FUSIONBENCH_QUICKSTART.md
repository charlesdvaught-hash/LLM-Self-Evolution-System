# FusionBench Integration: Quick Start

## What Changed?

**You now have 20+ ways to merge models** instead of 6.

- ✅ Same setup process (`setup.bat`)
- ✅ Same launch process (`run.bat`)
- ✅ Same basic workflow
- ✅ **NEW:** 6 powerful new merging methods in sidebar
- ✅ **NEW:** Per-method parameter tuning (optional)

---

## Step 1: Run Setup (First Time Only)

```batch
setup.bat
```

What this does:
- Rebuilds Docker images (includes FusionBench now)
- Creates local directories
- Takes ~10-20 minutes
- **Does NOT load any models to VRAM** (as always)

---

## Step 2: Launch UI

```batch
run.bat
```

Opens: `http://localhost:8501`

---

## Step 3: Create Experiment

**Sidebar → New Mission**

```
Define your goal: "Reasoning at 3B scale"
Optional: Name it something catchy
Click: 🚀 Initialize
```

---

## Step 4: Select Merge Methods (NEW!)

**Sidebar → ⚙️ Merge Methods**

You'll see:

```
🔧 MergeKit (7 methods)
├─ ✓ SLERP (classic, fast)
├─ ✓ TIES (interference-aware)
├─ ✓ DARE (sparse merging)
├─ ☐ MOE (expert routing)
├─ ☐ RMM (majority voting)
├─ ☐ NegMerge (subtract unwanted)
└─ ☐ Task Arithmetic (vector math)

🧠 FusionBench (13+ methods) ← NEW!
├─ ✓ Task Arithmetic (regression)
├─ ✓ RegMean (optimized mean)
├─ ☐ Voting (democratic merge)
├─ ☐ Magnitude Prune (sparse)
├─ ☐ Frankenmerge (layer-wise)
├─ ☐ Git Rebasin (aligned)
└─ ☐ ... (7+ more)
```

**Default:** SLERP, TIES, Task Arithmetic, RegMean (checked)

**To add/remove:** Just click checkboxes

---

## Step 5: Customize Method Parameters (Optional)

**Sidebar → ⚙️ Method Parameters** (new section)

Expand any section to tweak:

```
📌 Task Arithmetic
   Regularization: ━━━━━●━ 0.3

📌 DARE
   Drop Rate: ━━●━━━━ 0.15

📌 TIES
   Threshold: ━━━━━━●━ 0.9
```

**If you don't touch these:** Defaults are used (they work well)

---

## Step 6: Select Base Models

**🧪 Evolution tab → Base Models**

```
Multi-select: 
  ✓ Qwen/Qwen2.5-0.5B-Instruct
  ✓ Qwen/Qwen2.5-1.5B-Instruct
  ✓ mistralai/Mistral-7B
```

Pick 2+ models you want to merge together.

---

## Step 7: Start Evolution

**Click: ▶️ START EVOLUTION**

What happens:
1. Each cycle, a random merge method is selected
2. Your selected base models are merged using that method
3. Result is evaluated (benchmarked)
4. If it's good, it becomes a parent for the next cycle
5. If it's bad, it's removed

**Progress bar updates in real-time** with scores and timestamps.

---

## New Methods Explained (Simple Version)

### 6 New Methods You Got

**RegMean**
- Like averaging, but smarter
- Solves an optimization problem
- Good all-rounder

**Voting**
- Ask each model "what should this weight be?"
- Take majority vote
- Democratic merging

**Magnitude Prune**
- Keep only the important weights
- Drop small/noisy ones
- Efficient merging

**Frankenmerge**
- Take layers from different models
- E.g., layers 1-5 from model A, 6-12 from model B
- Novel combinations

**Git Rebasin**
- Align models geometrically first
- Then merge aligned versions
- High quality but slower

**Task Arithmetic**
- Math: base + (model_A - base) + (model_B - base)
- Works in vector space
- Principled approach

---

## Understanding Parameters (Optional Learning)

### Regularization (Task Arithmetic, RegMean)

- **0.0** = Pure merge (no constraint)
- **0.5** = Medium constraint
- **1.0** = Maximum constraint (stays close to base)

→ **Leave at 0.0 for first runs**

### Drop Rate (DARE)

- **0.1** = Drop 10% of weights (sparse)
- **0.3** = Drop 30% (very sparse, risky)
- **0.0** = Keep everything (dense)

→ **0.1 is safe, try 0.2 if feeling brave**

### Threshold (TIES)

- **0.9** = Strict (only high-confidence weights)
- **0.7** = Moderate
- **0.5** = Loose (merge more aggressively)

→ **0.9 is conservative, try 0.8 for more blending**

### Voting Type

- **majority** = Most common vote wins
- **unanimous** = Only use weights all models agree on
- **weighted** = Weight by confidence

→ **majority is safe**

### Prune Ratio (Magnitude Prune)

- **0.1** = Remove 10% of weights
- **0.3** = Remove 30%
- **0.5** = Remove 50% (aggressive)

→ **0.1 is safe**

### Rank (Frankenmerge)

- **4** = Low rank (speed over quality)
- **8** = Medium (balance)
- **16** = High rank (quality over speed)

→ **8 is default, use 16 for final runs**

---

## Tips for Best Results

### First Time?
- Use default methods (SLERP, TIES, Task Arithmetic, RegMean)
- Don't touch parameters
- Run 3-5 cycles

### Want Faster?
- Remove MOE, Expert Selection, Variance Reduction
- Keep SLERP, TIES, DARE
- These run in seconds

### Want Better Quality?
- Add Frankenmerge, Git Rebasin
- Increase num_cycles to 5-10
- Takes longer but finds better models

### Curious About Everything?
- Select ALL methods
- Evolution will randomly try each
- Best methods win over time

---

## What Happens During Evolution

**Cycle 1:**
- Randomly pick merge method → SLERP
- Merge your base models
- Get score: 0.7102
- Save this model

**Cycle 2:**
- Randomly pick merge method → Task Arithmetic  
- Merge best model from Cycle 1 with a base model
- Get score: 0.7234 (better!)
- ✨ This becomes new best

**Cycle 3:**
- Randomly pick merge method → RegMean
- Merge best model from Cycle 2 with base model
- Get score: 0.6890 (worse)
- 📉 Discard this one

**After all cycles:**
- Keep the best model (0.7234)
- Download from results folder
- Use it!

---

## Check That It Works

### Do this after setup.bat completes:

```batch
run.bat
```

**In sidebar, look for:**
- ✅ "🔧 MergeKit methods" section
- ✅ "🧠 FusionBench methods" section (NEW)
- ✅ "⚙️ Method Parameters" (NEW)

**In main tabs, look for:**
- ✅ "🔬 Methods" tab showing all 20+ methods (NEW)

If you see these → integration successful!

---

## Common Questions

**Q: Do I need to understand all 20 methods?**

A: No. Evolution does. Just select a mix and let it find winners.

**Q: What if I break parameters?**

A: Worst case: merge quality drops. Defaults will always work.

**Q: Do models still NOT load during setup?**

A: Correct! `setup.bat` still doesn't load anything. Models download when you first run evolution (5-10 min).

**Q: Can I use these methods with my own models?**

A: Yes. In Evolution tab, checkbox "Custom model" and paste HuggingFace ID.

**Q: Which method is best?**

A: It depends! That's why evolution tries many. Let it discover.

**Q: Can I resume old experiments?**

A: Yes. Sidebar → Resume Mission. Everything backwards compatible.

---

## Examples

### Example 1: Conservative User

```
Sidebar:
  MergeKit: ✓ SLERP ✓ TIES (no FusionBench)
  Parameters: Leave at defaults
  Cycles: 3

Result: Reliable, boring, good baseline
```

### Example 2: Adventurous User

```
Sidebar:
  MergeKit: ✓ All
  FusionBench: ✓ All
  Parameters: Explore different values
  Cycles: 10

Result: Likely to find novel combinations
```

### Example 3: Balanced User

```
Sidebar:
  MergeKit: ✓ SLERP ✓ TIES ✓ DARE
  FusionBench: ✓ Task Arithmetic ✓ RegMean ✓ Frankenmerge
  Parameters: Leave at defaults
  Cycles: 5

Result: Good mix of exploration and reliability
```

---

## Troubleshooting

**"I don't see FusionBench methods"**
- Run `setup.bat` again (may need to rebuild)
- Restart Streamlit (`run.bat`)

**"Merge failed"**
- Check sidebar logs for error
- Most common: Model downloading (takes 5-10 min first time)
- If stuck, check Docker is running

**"Parameters don't seem to work"**
- Changes take effect next cycle
- Restart UI (`run.bat`) if still stuck

**"All methods give same result"**
- Normal for small models
- Try different base models
- Increase cycles to see divergence

---

## Next Steps

1. **Run:** `setup.bat` (first time only)
2. **Launch:** `run.bat`
3. **Create:** New Mission with your goal
4. **Select:** Mix of MergeKit + FusionBench methods
5. **Run:** Evolution
6. **Enjoy:** Results in real-time UI

---

**That's it! 20+ merging methods, same simple interface.**
