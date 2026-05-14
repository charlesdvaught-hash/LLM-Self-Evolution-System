# Design Philosophy, Startup, & User Experience

**The Breeding Vat** is a **LLM Fabricator** — a future-lab for evolving small language models. This document makes that vision explicit.

---

## The Vision: "You Got Access to a Lab from Tomorrow"

You've somehow gained access to an advanced fabrication facility. Inside:

- **Raw materials** (base models) you select
- **Evolutionary pressure** (merge methods, benchmarks, culling)
- **Full transparency** (every crossover logged, every offspring recorded)
- **Full control** (decide every parameter, or let the AI handle it)

You don't understand all the machinery. But you watch it work. Models breed. Failures die. Winners reproduce. Every step recorded. Every mutant preserved.

By the end, you own something that didn't exist before — engineered through directed evolution, not training from scratch.

**This is the feeling the system should evoke.**

---

## Part 1: Build Philosophy

### Core Principle: "Fabrication Laboratory, Not Training Pipeline"

This is NOT another training framework. It's a **fabricator for evolved models**.

**Key difference**:

| Traditional | Breeding Vat |
|-------------|---|
| Start: random weights | Start: proven models |
| Optimize: loss function | Optimize: goal + human judgment |
| End: one model | End: genealogy of exponentially many models |
| Data: loss curves | Data: lineage tree, merge crossovers, benchmark quirks |
| Feel: black box | Feel: transparent lab, every step visible |

**Manifestation**:
- User sets goal + controls
- System fabricates exponential offspring through cycles
- Each offspring benchmarked immediately (simple test, capture quirks)
- Failures culled, winners breed next cycle
- Everything recorded: parents, merge method, benchmark, weird behaviors
- User can export any model or study the genealogy

### Why This Metaphor Matters

A **fabricator** feels like:
- ✅ You're in control (you set parameters OR tell AI to handle it)
- ✅ You're watching something happen (real-time, transparent)
- ✅ You're creating, not training (evolution, not optimization)
- ✅ Science fiction come to life (future lab aesthetic)
- ✅ Data everywhere (every crossover recorded, every quirk noted)

Not a black box. Not a service. A **tool you operate**.

### Design Consequence: Exponential Population Growth

Each cycle, population **doubles** (or user-configured factor):

```
Cycle 0: [Base Model A, Base Model B]  (2 models)
  ↓ (every model breeds with random partner)
Cycle 1: [offspring_1, offspring_2, offspring_3, offspring_4]  (4 models)
  ↓
Cycle 2: [8 models]
  ↓
Cycle 3: [16 models]
  ↓
Cycle 4: [32 models]
  ↓
Cull bottom 50% each cycle → keep winners
  ↓ (winners breed next cycle)
Cycle 5: [winners from cycle 4, new offspring]
```

**Result**: By cycle 5 with 50% culling, you have ~32 models in genealogy, but 2-4 survivors chosen by evolution.

**User feels**: "Wow, the system tried that many models? And kept only the good ones?"

### Design Consequence: Every Merge is Recorded

Every single crossover **saved with full metadata**:

```json
{
  "model_id": "mutant_c2_p1_regmean",
  "cycle": 2,
  "parents": ["mutant_c1_p0_slerp", "mutant_c1_p2_dare"],
  "method": "regmean",
  "method_params": {"reg_coef": 1e-6},
  "timestamp": "2025-01-15T14:23:45",
  "benchmark": {
    "perplexity": 8.234,
    "arc_challenge": 0.751,
    "hellaswag": 0.740,
    "anomalies": [
      "⚠️ arc_challenge much better than hellaswag (specialization?)",
      "✓ perplexity stable (no collapse)",
      "⚠️ reasoning_depth lower than parent (drift?)"
    ]
  },
  "culled": false,
  "reason_kept": "Best combined score this cycle"
}
```

**User feels**: "I can see exactly why each model was kept or culled. I can study the data later."

### Design Consequence: Simple General Benchmark on Every Model

Every model gets a **quick, standardized test** immediately after merge:

```
Benchmark Suite (runs in ~2-3 minutes):
├─ Perplexity check (15s) — "did the merge break it?"
├─ Arc Easy (30s) — "can it answer simple questions?"
├─ Arc Challenge (30s) — "can it reason under constraints?"
├─ HellaSwag (1min) — "does it understand narrative?"
└─ Quirk Detection (30s) — "is there anything weird?"
```

**Quirk Detection** is key — flags anomalies for later analysis:
- Score jumped 20% vs parent (specialization? or overfitting?)
- Perplexity spiked (structural damage?)
- One task >> other tasks (capability loss in some areas?)
- Performance matches parent exactly (merge did nothing?)

**User feels**: "The system is watching for weird behaviors. I can study those later."

### Design Consequence: Full Control OR Let AI Handle It

**Two modes of operation**:

#### Mode 1: "I'm in Control" (Expert)

```
Set every parameter by hand:
├─ Base models: [Qwen-0.5B, Mistral-7B, my-finetuned]
├─ Merge methods: [SLERP (t=0.5), DARE (drop=0.1), Task Arithmetic (w=0.7)]
├─ Cycles: 5
├─ Population size per cycle: 4
├─ Culling rate: 50%
├─ Benchmark tier: full (all 4 tasks)
└─ [START FABRICATION]
```

User specifies **exactly what happens**. System executes faithfully.

#### Mode 2: "You Handle It" (Novice)

```
Set high-level goal:
├─ Goal: "3B reasoning specialist"
├─ Compute budget: "1 hour"
├─ Explore: "All methods"
└─ [START FABRICATION]

System decides:
├─ Which merge methods to try
├─ How many cycles to fit in 1 hour
├─ Population size (adjusted for time)
├─ When to cull vs explore
└─ Which benchmark tier to use
```

AI advisor watches, adapts, stays within compute budget.

**Both feel like control** because both are transparent: user sees what happens real-time.

### Design Consequence: Invisible Infrastructure

Containers, GPU allocation, YAML configs, database queries — all invisible.

User never types:
- ❌ Docker commands
- ❌ Merge configs
- ❌ SQL queries
- ❌ CUDA settings
- ❌ Python code

User sees:
- ✅ Clean UI (Streamlit)
- ✅ Evolution progress (real-time chart)
- ✅ Model genealogy (clickable tree)
- ✅ Benchmark results (table)
- ✅ Quirk alerts (flagged anomalies)

All infrastructure handled. User operates the **lab**, not the machinery.

---

## Part 2: Startup Process

### Philosophy: "One Click, Everything Works"

A future lab wouldn't make you debug. You'd walk in and it's operational.

### Flow: `setup.bat` (First Time Only)

```
User double-clicks setup.bat
  ↓
💬 "Welcome to the Breeding Vat. Setting up your fabrication lab..."
  ↓
[✓] Checking Docker installation
    ├─ If missing: "Install Docker Desktop: docker.com"
    └─ If found: Continue
  ↓
[✓] Building fabrication chambers (Docker images)
    ├─ breeding-vat-ui (control interface)
    ├─ breeding-vat-merge (crossover engine)
    ├─ breeding-vat-eval (benchmark harness)
    ├─ breeding-vat-sae (introspection tool)
    └─ breeding-vat-fusionbench (advanced merging)
    
    [████████████████░░░░░] 70% — Building merge chamber...
    (Estimated 8 minutes remaining)
  ↓
[✓] Initializing data vault
    ├─ experiments/ (genealogy records)
    ├─ merged_models/ (fabricated specimens)
    ├─ eval_results/ (benchmark data)
    └─ model_zoo/ (base materials)
  ↓
[✓] Downloading base models (~30GB, first time only)
    ├─ Qwen-0.5B-Instruct
    ├─ Qwen-1.5B-Instruct
    ├─ Mistral-7B-Instruct
    
    [████████░░░░░░░░░░░░░] 35% — Downloading base models...
    (Estimated 12 minutes remaining)
  ↓
[✓] Initializing genealogy database
    └─ Ready to track lineage, merges, benchmarks
  ↓
✨ SUCCESS
💬 "Lab operational. All systems ready."
💬 "Run: run.bat"
💬 "Time to fabricate something extraordinary."
Exit setup.bat
```

**Total time**: 20-35 minutes first run (depends on internet, disk)
**Subsequent runs**: < 1 second (everything cached)

### Flow: `run.bat` (Every Time)

```
User double-clicks run.bat
  ↓
💬 "Initializing control interface..."
  ↓
[✓] Docker running
[✓] Chambers operational
[✓] Database responding
  ↓
🚀 Opening lab interface...
  
(Browser opens to http://localhost:8501)
  ↓
Streamlit UI appears with:
├─ 📊 Recent experiments list (clickable)
├─ 🧬 Create new fabrication run
├─ 📈 Live evolution monitor
├─ 🔬 Benchmark & quirks explorer
├─ 📜 Lineage visualizer
└─ 💾 Export & archive tools
```

**Total time**: 3-5 seconds (UI loads instantly)

### Error Handling: "Helpful, Not Scary"

If something breaks:

```
❌ ERROR: Base model download failed (no internet?)

🔧 Solutions:
  1. Check internet connection
  2. Free up 50GB disk space
  3. Run setup.bat again (resumes download)

📖 Need help? See docs/STARTUP_TROUBLESHOOTING.md
```

Never shows stack traces. Always actionable.

---

## Part 3: User Experience Intent — The Feeling

### Aesthetic: "You're Operating a Fabricator"

The lab aesthetic should permeate everything:

**During Setup**:
- ✓ Progress bars with chamber names ("Building merge chamber...")
- ✓ Estimated time remaining
- ✓ Sense of anticipation ("Lab starting up...")

**At Idle** (waiting for evolution to start):
- ✓ Nice visuals of the system standing by
- ✓ Maybe a quiet hum of "chambers ready"
- ✓ Button says "🚀 START FABRICATION" not "Run Experiment"

**During Evolution**:
- ✓ Real-time chart of population fitness over cycles
- ✓ Current cycle (e.g., "Cycle 3/5")
- ✓ Method being tried right now (e.g., "Testing DARE merge...")
- ✓ Model count ("7 models in population")
- ✓ Culling event: "🔪 Culled 2 models, 5 remain"
- ✓ New survivor: "✨ New best model: mutant_c3_p2_ta (score 0.764)"

**After Evolution**:
- ✓ "Fabrication complete"
- ✓ Best model highlighted
- ✓ Genealogy tree (clickable, shows every crossover)
- ✓ Export buttons: "💾 Save Best Model", "📋 Export Genealogy"

### Transparency: "You Can See Everything"

User never feels blind:

**Live Progress**:
- What cycle is running?
- What method is being tried?
- Current benchmark scores (partial results)?
- Current population count?
- Time remaining?

**Queryable History**:
- Click any model → see parents, merge method, parameters
- Click any benchmark → see which models got that score, any quirks?
- Search genealogy → "show me all SLERP merges", "show models with high HellaSwag scores"

### Control: "Dial It Up Or Let AI Tune It"

Two clear pathways:

**Pathway A: Expert Control**
```
I know exactly what I want:
├─ These 3 base models
├─ These 4 merge methods with specific parameters
├─ Run for exactly 7 cycles
├─ Use this benchmark tier
└─ [START]

System: executes exactly as specified
```

**Pathway B: Guided Evolution**
```
I have a goal but not the parameters:
├─ Goal: "3B reasoning specialist"
├─ Budget: "30 minutes of compute"
├─ Risk: "low (conservative) / medium / high (exploratory)"
└─ [START]

System: picks methods, adapts cycles, watches the clock, reports why it chose winners
```

Both give **control**. Different flavors.

### Data Obsession: "Every Merge is Evidence"

The system treats every fabrication as a **data point**:

```
Model: mutant_c2_p1_regmean

Metadata:
✓ Parents: [mutant_c1_p0_slerp, mutant_c1_p2_dare]
✓ Method: RegMean with reg_coef=1e-6
✓ Timestamp: precise
✓ Benchmark: [perplexity, arc_easy, arc_challenge, hellaswag]
✓ Quirks detected: 
   - ⚠️ arc_challenge >> arc_easy (specialization?)
   - ⚠️ perplexity vs parents (structural impact?)
✓ Culling decision: kept (best this cycle) / culled (didn't improve)
✓ Why kept/culled: exact reason
```

**User feels**: "This is scientific. Every decision is recorded. I can study this later."

### Speed of Feedback: "You See Results in Hours, Not Weeks"

A cycle should finish in **10-30 minutes**, depending on model size + benchmark tier.

Default: 3 cycles in 1 hour.

Why?
- ✅ User sees something happening (not watching paint dry)
- ✅ Can iterate fast (try idea 1, see results, try idea 2)
- ✅ Research loop stays tight (curiosity not killed by waiting)

Benchmark is **intentionally light** (not comprehensive) to keep cycles fast. User can run comprehensive eval later on best model.

### Curation, Not Search

The system is **curating a bloodline**, not searching a space.

```
NOT: "Trying 1000 random hyperparameters, picking the best"
YES: "Breeding models with direction, culling the weak, keeping winners"
```

**Difference in feeling**:
- Random search = lottery
- Evolution = cultivation

User feels like a **breeder selecting for traits**, not an optimizer tuning knobs.

### Preservation: "Everything is Saved"

User never loses data:

```
Every model saved with:
├─ Full weights & config
├─ Parent lineage
├─ Merge parameters used
├─ Benchmark scores
├─ Quirks detected
├─ Timestamp
└─ "Culled/Kept" status with reason
```

User can:
- Export any model (even the "failed" ones)
- Study genealogy (why was this model culled?)
- Analyze quirks later (what was weird about this merge?)
- Resume experiment (continue from cycle 3)

**User feels**: "My data is safe. I own the entire genealogy."

### Future Lab Aesthetic

Make it feel like you're in a **facility from 2035** where:
- Models breed automatically
- Results appear in real-time
- Genealogy is visualized beautifully
- Data is abundant
- You make decisions with perfect information
- Failures are recorded and studied, not hidden

**Dark mode UI** (optional but fitting). **Real-time animations**. **Sound effects** (subtle, optional). **Tree visualizations** of genealogy. **Heatmaps** of benchmark quirks.

The system should be **beautiful to watch**.

---

## Summary: The Breeding Vat is a Fabricator

| Dimension | Experience |
|-----------|-----------|
| **Feeling** | You have access to a future lab. Models breed before your eyes. |
| **Control** | Full control (specify everything) OR guided control (let AI handle it). Both transparent. |
| **Data** | Every merge recorded. Every quirk flagged. Full genealogy available. |
| **Speed** | Fast cycles (10-30 min). See results quickly. Iterate. |
| **Curation** | You're breeding for a goal, not optimizing randomly. |
| **Preservation** | Every model saved. No data loss. Own the entire genealogy. |

**User walks away thinking**: "I didn't train a model. I *fabricated* one through evolution. And I watched every step."

That's the magic.
