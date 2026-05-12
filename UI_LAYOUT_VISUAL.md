# UI Layout & Visual Guide

## Overall Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🧬 BREEDING VAT                                                      │
│ Autonomous LLM Evolution Engine • Experimental Pipeline             │
└─────────────────────────────────────────────────────────────────────┘

┌─ SIDEBAR ──────────────────┐  ┌─ MAIN AREA ────────────────────────────┐
│ Mission Control            │  │                                        │
│                            │  │ [Evolution] [Calibration] [Lineage]   │
│ ┌─ New │ Resume ────────┐  │  │ [Advanced] [Logs]                     │
│ │ Goal:                 │  │  │                                        │
│ │ [Reasoning at 3B...] │  │  │ ┌────────────────────────────────────┐ │
│ │                      │  │  │ │ EVOLUTION TAB                      │ │
│ │ [Initialize]         │  │  │ │                                    │ │
│ └────────────────────┘  │  │  │ Base Models    Merge Methods  Advisor│
│                         │  │  │ ┌──────────┐   ┌──────────┐  ┌────┐  │
│ Current Mission         │  │  │ │Qwen-0.5B │   │[x] linear │  │Q1B │  │
│ ▯ Cycles: 0/3           │  │  │ │Mistral-7B│   │[x] task_a │  │Q7B │  │
│ ▯ Best: 0.0000          │  │  │ └──────────┘   │[x] regmean│  └────┘  │
│ ▯ Status: Active        │  │  │                │[x] ties   │          │
│                         │  │  │                └──────────┘          │
│ ┌─ Open │ Logs ──────┐  │  │  │                                    │
│ │ (explorer/console)   │  │  │ [📤 Upload] [Get Recipe]           │
│ └────────────────────┘  │  │  │                                    │
│                         │  │  │ ─────────────────────────────────  │
│                         │  │  │ [🚀 START EVOLUTION]              │
│                         │  │  │ [Get Recipe]                       │
│                         │  │  └────────────────────────────────────┘
└─────────────────────────┘  └────────────────────────────────────────┘
```

---

## EVOLUTION TAB (Main Interface)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Evolution Pipeline                                                  │
│ Select models and launch evolutionary synthesis.                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ Base Models ──────────┐  ┌─ Merge Methods ─┐  ┌─ Advisor ──┐   │
│ │                        │  │                 │  │            │   │
│ │ [Qwen 0.5B        ▼]   │  │ [x] linear      │  │ ⚡ Quick   │   │
│ │ [Mistral-7B       ▼]   │  │ [x] task_arith  │  │    Fast    │   │
│ │ [My Qwen          ▼]   │  │ [x] regmean     │  │    1GB     │   │
│ │ [              ▼]       │  │ [x] ties_linear │  │ 500ms      │   │
│ │                        │  │ [x] dare_linear │  │            │   │
│ │ ┌──────────────────┐   │  │                 │  │ 🧠 Capable │   │
│ │ │📤 Upload Local   │   │  │ [Show all (7+)] │  │    Detailed│   │
│ │ │Model             │   │  │                 │  │    7GB     │   │
│ │ │ ────────────────│   │  │                 │  │ 3000ms     │   │
│ │ │ /path/to/model/ │   │  │                 │  │            │   │
│ │ │ [Transfer]      │   │  │                 │  │            │   │
│ │ └──────────────────┘   │  │                 │  │            │   │
│ └────────────────────────┘  └─────────────────┘  └────────────┘   │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ [🚀 START EVOLUTION]        [Get Recipe]                      │ │
│ └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

[When running...]

┌─────────────────────────────────────────────────────────────────────┐
│ Evolution in Progress                                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  1/3 cycles           │
│ **▶️ Cycle 1: Evaluating**                                          │
│                                                                     │
│ [15:24:12] • Starting evolution                                    │
│ [15:24:15] ✓ Merge method: linear                                 │
│ [15:24:45] ✓ Merge complete: mutant_c1_p0_ln                     │
│ [15:25:00] ✓ Score: 0.6890                                        │
│                                                                     │
│ Progress: 33%      Current Score: 0.6890      Best: 0.6890        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## CALIBRATION TAB (Broad-Stroke Settings)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Strategy Calibration                                                │
│ Set broad-stroke parameters once. Evolution runs autonomously.     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ Evolutionary Pressures ─────────┐  ┌─ Benchmarking Strategy ──┐ │
│ │                                   │  │                          │ │
│ │ Population Dynamics               │  │ Evaluation Intensity     │ │
│ │ ┌─────────────────────────────┐   │  │ ◉ Quick & Dirty          │ │
│ │ │Culling Rate: [50]           │   │  │ ○ Balanced               │ │
│ │ │  Min 10%    Max 90%         │   │  │ ○ Thorough               │ │
│ │ │Evolution Cycles: [3]        │   │  │                          │ │
│ │ │  Min 1     Max 50           │   │  │ Category Selection       │ │
│ │ └─────────────────────────────┘   │  │ ☑ Reasoning (10 q)       │ │
│ │                                   │  │ ☑ Knowledge (20 q)       │ │
│ │ Stopping Strategy                 │  │ ☑ Language (10 q)        │ │
│ │ ┌─────────────────────────────┐   │  │ ☑ Math (5 q)             │ │
│ │ │When to Stop: [Exhaust  ▼]   │   │  │ ☑ Coding (3 q)           │ │
│ │ │ • Exhaust all cycles        │   │  │ ☑ Common Sense (10 q)    │ │
│ │ │ • Hit goal score            │   │  │ ☑ QA (5 q)               │ │
│ │ │ • Plateau detected          │   │  │ ☑ Safety (10 q)          │ │
│ │ │ • Manual intervention       │   │  │ ☑ General (25 q always) │ │
│ │ └─────────────────────────────┘   │  │                          │ │
│ │                                   │  │ Summary:                 │ │
│ │ Post-Cycle Actions                │  │ Categories: 7            │ │
│ │ ┌─────────────────────────────┐   │  │ Questions: 98            │ │
│ │ │After Each Cycle: [Analyze ▼]│  │  │ Est. Time: 15m           │ │
│ │ │ • Analyze (SAE)             │   │  │                          │ │
│ │ │ • Shuffle winners           │   │  │                          │ │
│ │ │ • Continue normally         │   │  │                          │ │
│ │ │ • Deep eval                 │   │  │                          │ │
│ │ └─────────────────────────────┘   │  │                          │ │
│ │                                   │  │                          │ │
│ │ ☑ Flag Perfect Runs               │  │                          │ │
│ │ (Catch anomalies)                 │  │                          │ │
│ └───────────────────────────────────┘  └──────────────────────────┘ │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ ┌─ ⚙️ Show Advanced Merge Settings                 [expanded]       │ │
│ │ (Hidden by default)                                             │ │
│ │                                                                 │ │
│ │ Task Arithmetic Regularization:    [0.0]                       │ │
│ │ DARE Drop Rate:                    [0.1]                       │ │
│ │ RegMean Regularization:            [0.0]                       │ │
│ │ TIES Threshold:                    [0.9]                       │ │
│ │ Voting Threshold:                  [0.5]                       │ │
│ │ Frankenmerge Rank:                 [8]                         │ │
│ │                                                                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LINEAGE TAB (Results & History)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Model Genealogy                                                     │
│ Performance history and model breeding records.                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Models Tested: 8     │     Best Score: 0.7346     │     Avg: 0.6892│
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ Performance History:                                                │
│                                                                     │
│ Cycle │ Model                      │ Score   │ Method                 │
│ ─────┼────────────────────────────┼─────────┼──────────────────     │
│   2   │ mutant_c2_p0_rm            │ 0.7346  │ regmean                │
│   2   │ mutant_c2_p1_ta            │ 0.7234  │ task_arithmetic        │
│   1   │ mutant_c1_p1_ti            │ 0.7102  │ ties_linear            │
│   1   │ mutant_c1_p0_ln            │ 0.6890  │ linear                 │
│   0   │ Qwen/Qwen2.5-0.5B          │ 0.6432  │ base                   │
│   0   │ mistralai/Mistral-7B       │ 0.6124  │ base                   │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ Score Trajectory:                                                   │
│                                                                     │
│   0.74 │                                                             │
│   0.72 │                                    ╱─╮                      │
│   0.70 │                ╱─────╮             ╱   │                    │
│   0.68 │            ╱─╮╱         │        ╱     │                    │
│   0.66 │         ╱─╮               │    ╱       │                    │
│   0.64 │     ╱─╮                   │╱           │                    │
│   0.62 │ ╱─╮                       ╱            │                    │
│        └─────────────────────────────────────────────               │
│        Cycle 0   Cycle 1   Cycle 2   Cycle 3   Cycle 4              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ADVANCED TAB (Analysis & Debugging)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Advanced Analysis                                                   │
│ Sparse Autoencoder introspection and anomaly investigation.        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ SAE Analysis ──────────────────┐  ┌─ Anomaly Log ──────────────┐ │
│ │                                 │  │                            │ │
│ │ VRAM Available: [12GB ▼]        │  │ Detected Anomalies: 0      │ │
│ │                                 │  │                            │ │
│ │ Samples: ▬▬▬▬▬▬▬░░░ 30          │  │ (No anomalies detected)    │ │
│ │                                 │  │                            │ │
│ │ Layers: [8]                     │  │ ──────────────────────────┘ │
│ │                                 │  │                            │
│ │ [🔬 Analyze]                    │  │ [If anomaly detected]      │
│ │                                 │  │                            │
│ │ └─────────────────────────────┘ │  │ ┌──────────────────────┐   │
│ │                                 │  │ │🚨 mutant_c1_p0_ta    │   │
│ │                                 │  │ │2025-01-15            │   │
│ │                                 │  │ │                      │   │
│ │                                 │  │ │Anomaly: Score 100%   │   │
│ │                                 │  │ │on general benchmark. │   │
│ │                                 │  │ │                      │   │
│ │                                 │  │ │Likely causes:        │   │
│ │                                 │  │ │• Weight corruption   │   │
│ │                                 │  │ │• Setup error         │   │
│ │                                 │  │ │• Data leak           │   │
│ │                                 │  │ │                      │   │
│ │                                 │  │ │Recommend: Check      │   │
│ │                                 │  │ │model README, re-eval │   │
│ │                                 │  │ │with clean setup      │   │
│ │                                 │  │ └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LOGS TAB (Data Export)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Master Log                                                          │
│ Complete experiment timeline and decisions.                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [📥 Download Log]                                                   │
│                                                                     │
│ [15:24:00] • Experiment created                                    │
│ [15:24:01] ✓ Goal: Reasoning at 3B scale                           │
│ [15:24:02] ✓ Base models: Qwen-0.5B, Mistral-7B                   │
│ [15:24:03] ✓ Merge methods: linear, task_arithmetic               │
│ [15:24:04] ✓ Evolutionary pressures: cull=50%, cycles=3           │
│ [15:24:05] ✓ Benchmarks: balanced (98 q), + general (25 q)        │
│ [15:24:12] • Cycle 1 started                                       │
│ [15:24:15] • Merge method selected: linear                         │
│ [15:24:30] ✓ Merge complete: mutant_c1_p0_ln                      │
│ [15:24:45] • Evaluation started (98 q + 25 q)                      │
│ [15:25:00] ✓ Benchmark complete: score=0.6890                     │
│ [15:25:01] ✓ No anomalies detected (0.6890 < 0.99)                │
│ [15:25:02] • Culling: keeping top 50% (1/2 models)                 │
│ [15:25:03] • Post-cycle action: analyzing best model (SAE)        │
│ [15:25:15] ✓ SAE analysis complete: 4 specialized layers          │
│ [15:25:16] • Cycle 2 started                                       │
│ ...                                                                  │
│ [15:45:00] ✓ Cycle 3 complete                                      │
│ [15:45:01] ✓ Stopping condition met: exhausted 3 cycles            │
│ [15:45:02] ✓ Evolution complete: best_model=mutant_c2_p0_rm       │
│ [15:45:03] ✓ Best score: 0.7346                                    │
│ [15:45:04] ✓ Improvement: +12.3% from baseline                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Color Palette

```
Background Primary:     #0a0e27  (Very Dark Blue)
Background Secondary:   #12172a  (Slightly Lighter)
Accent Primary:         #00d9ff  (Cyan)
Accent Success:         #10b981  (Green)
Accent Warning:         #f59e0b  (Amber)
Accent Danger:          #ef4444  (Red)
Text Primary:           #e5e7eb  (Light Gray)
Text Secondary:         #9ca3af  (Medium Gray)
Border:                 #1f2937  (Dark Gray)
```

---

## Animations & Interactions

### Progress Bar
- Smooth linear gradient (cyan to blue)
- Updates every cycle
- No celebrations

### Buttons
- Hover: 0.2s ease transition
- Primary (cyan): Linear gradient
- Secondary: Border highlight
- No "happy" animations

### Log Entries
- Append inline (no popups)
- Max 8 recent shown
- Scroll if more
- Codes blocks for clean display

### Metrics
- Compact layout (no big numbers)
- Subtle color coding
- Scan-friendly format

---

## Responsive Design

| Screen | Layout |
|--------|--------|
| **Desktop (1200+px)** | 3-col sidebar + wide main |
| **Laptop (1000px)** | 2-col (sidebar narrower) |
| **Tablet (768px)** | Sidebar collapses, tabs stack |
| **Mobile (480px)** | Single column, full-width tabs |

---

**Status**: Ready for implementation
