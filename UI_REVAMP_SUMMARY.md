# UI Revamp: Sleek, Experimental Pipeline, Broad-Stroke Calibration

**Status**: Complete  
**Changes**: Replaced granular-per-cycle settings with broad-stroke calibration, sleek dark theme, hidden merge params, no celebration balloons.

---

## Overview of Changes

### 1. **New Sleek Dark Theme** (`ui_v2_sleek.py`)

**Before**: GitHub-style light theme with emoji balloons  
**After**: Dark, minimal, professional theme with subtle animations

- CSS-based dark mode (cyan accents `#00d9ff`)
- Minimal borders, rounded corners
- Suppressed all balloons/confetti (NoiseLevel class)
- Compact metric displays (no celebrations after success)
- Subtle pulse animations instead of loud feedback

```python
# Apply theme
SleekUITheme.apply()
NoiseLevel.suppress_celebrations()
```

**UI Components**:
- `SleekUITheme.apply()` — Dark CSS injection
- `CompactMetrics` — Minimal stat displays
- `StatusIndicator` — Subtle success/warning/error messages
- `ProgressTracker` — Progress bar + logging + metrics
- `NoiseLevel.suppress_celebrations()` — Kill balloons

### 2. **Evolutionary Pressures** (`evolutionary_pressures.py`)

**Before**: Individual sliders for each method per cycle  
**After**: Broad-stroke strategy calibration set once

**Settings**:
- **Population Dynamics**: Culling rate (10-90%), evolution cycles (1-50)
- **Stopping Strategy**: Exhaust cycles / Hit goal / Plateau detected / Manual
- **Post-Cycle Actions**: Analyze (SAE) / Shuffle winners / Continue / Deep eval
- **Anomaly Detection**: Flag perfect general benchmark scores

**Example**:
```python
pressures = EvolutionaryPressures()
settings = pressures.render_ui()
# Returns:
# {
#   "culling_rate": 50,
#   "num_cycles": 3,
#   "stopping_condition": "max_cycles",
#   "post_cycle_action": "analyze",
#   "enable_anomaly_detection": True
# }
```

### 3. **Benchmark Selector** (`benchmark_selector.py`)

**Before**: Manual selection of individual tasks  
**After**: Quick/Balanced/Thorough presets with category selection

**8-10 Core Categories**:
- Logical Reasoning (arc_challenge, hellaswag)
- General Knowledge (mmlu, wikiqa)
- Language Understanding (winogrande, boolq)
- Mathematical Problem Solving (gsm8k)
- Code Generation (humaneval, mbpp)
- Common Sense Reasoning (commonsense_qa)
- Question Answering (squad)
- Safety & Toxicity (toxiqa)

**Intensity Levels**:
- **Quick & Dirty**: 5-20 questions per category
- **Balanced**: 50-100 questions per category
- **Thorough**: 200-500 questions per category

**Always Included**:
- General Benchmark: 25 moderate questions (detects anomalies)

**Example**:
```python
selector = BenchmarkSelector()
settings = selector.render_ui()
# Returns:
# {
#   "intensity": "balanced",
#   "categories": [
#     {"key": "reasoning", "name": "Logical Reasoning", "question_count": 100}
#   ],
#   "total_questions": 300,
#   "enable_general": True
# }
```

### 4. **AI Advisor Selector** (`ai_advisor_selector.py`)

**Before**: Fixed model selection  
**After**: Quick (1B) vs Capable (4GB) choice

**Quick Advisor** (⚡):
- Model: Qwen/Qwen2.5-0.8B-Instruct
- Size: 1GB
- Latency: 500ms
- Use Case: Fast iteration, immediate feedback

**Capable Advisor** (🧠):
- Model: Qwen/Qwen2.5-7B-Instruct
- Size: 4GB
- Latency: 3000ms
- Use Case: Detailed orchestration, complex analysis

### 5. **Anomaly Detector** (`anomaly_detector.py`)

**Purpose**: Flag suspicious perfect scores on general benchmark

**Detects**:
- Score ≥ 99% on general benchmark (likely errors)
- Possible causes: Weight corruption, benchmark data corruption, data leak
- Records merge data for debugging

**Example**:
```python
detector = AnomalyDetector(exp_dir)
anomaly = detector.check_general_benchmark_anomaly(
    model_name="mutant_c1_p0",
    general_benchmark_score=1.0,
    full_results={...}
)
# If detected:
# {
#   "is_anomaly": True,
#   "message": "🚨 Anomaly: ...",
#   "merge_data": {...},
#   "timestamp": "..."
# }
```

---

## New App Structure (`app_v2_revamped.py`)

### Tab Layout

| Tab | Purpose | Settings? |
|-----|---------|-----------|
| **Evolution** | Model selection, advisor choice, START button | No |
| **Calibration** | Evolutionary pressures, benchmarks, (hidden merge params) | Yes |
| **Lineage** | Genealogy table, performance history | No |
| **Advanced** | SAE analysis, anomaly investigation | Maybe |
| **Logs** | Master log download | No |

### Key Workflows

#### **Workflow 1: Simple Evolution**
```
1. Evolution Tab → Select 2+ models, select methods
2. Calibration Tab → Set evolutionary pressures (broad strokes), choose benchmark intensity
3. Evolution Tab → Click START EVOLUTION
4. Watch progress with minimal UI noise
5. Check Lineage when done
```

#### **Workflow 2: Anomaly Investigation**
```
1. Run evolution
2. If general benchmark score = 100% → Anomaly detected & logged
3. Advanced Tab → View anomaly log
4. Check merge data + readme
5. Re-evaluate with clean setup
```

#### **Workflow 3: Deep Analysis**
```
1. Run evolution with "Analyze" post-cycle action
2. After each cycle → SAE introspection runs automatically
3. Advanced Tab → View layer specialization
4. Use insights to guide next cycles
```

---

## Feature Breakdown

### ✅ Hidden Merge Settings
- **Visible by default**: Method selection only (checkbox list)
- **Hidden by default**: Per-method parameters (sliders, thresholds)
- **Show when relevant**: Expander "⚙️ Show Advanced Merge Settings"

### ✅ Broad-Stroke Calibration
- **Not per-cycle**: Set once at start
- **Evolutionary Pressures**: Culling, cycles, stopping conditions, post-cycle actions
- **Benchmarks**: Choose intensity (quick/balanced/thorough) + categories
- **AI Advisor**: Fast or detailed (not per-query)

### ✅ Sleek Dark UI
- Dark background (`#0a0e27`)
- Cyan accents (`#00d9ff`)
- Minimal borders and rounded corners
- No balloons, confetti, or loud celebrations
- Subtle pulse animations
- Compact metric displays

### ✅ Experimental Pipeline
- **Evolution Tab**: Models → Methods → Go
- **Calibration Tab**: Set strategy once
- **Automated loop**: Merge → Eval → Check stopping → Post-cycle action
- **Resumable**: Pause and resume across sessions

### ✅ Anomaly Detection
- General benchmark (25 questions, always run)
- Flag perfect scores (≥99%)
- Record merge data for debugging
- Alert user with detailed message

---

## Files Created

| File | Purpose |
|------|---------|
| `breeding_vat/ui/ui_v2_sleek.py` | Dark theme, minimal components, celebrations suppressed |
| `breeding_vat/modules/evolutionary_pressures.py` | Broad-stroke calibration UI (culling, cycles, stopping, post-cycle) |
| `breeding_vat/modules/benchmark_selector.py` | Quick/Balanced/Thorough presets + 8-10 categories |
| `breeding_vat/modules/ai_advisor_selector.py` | Quick (1B) vs Capable (4GB) advisor choice |
| `breeding_vat/modules/anomaly_detector.py` | Flag perfect general benchmark scores |
| `breeding_vat/ui/app_v2_revamped.py` | Revamped main app (5-tab layout, sleek, minimal) |

---

## Integration Steps

### Option A: Replace Existing App
```bash
# Backup old app
mv breeding_vat/ui/app.py breeding_vat/ui/app_old.py

# Use new app
cp breeding_vat/ui/app_v2_revamped.py breeding_vat/ui/app.py
```

### Option B: Run Side-by-Side (Testing)
```bash
streamlit run breeding_vat/ui/app_v2_revamped.py
```

---

## UI Flow Diagrams

### Main Evolution Flow
```
┌─ Mission Control (Sidebar)
│  ├─ New Mission or Resume
│  └─ Current mission stats
│
├─ Evolution Tab
│  ├─ Select base models (multi)
│  ├─ Select merge methods (multi)
│  ├─ Choose advisor (quick/capable)
│  └─ [START EVOLUTION]
│     ↓
│     ┌─ Check Calibration Tab (pressures + benchmarks set?)
│     ├─ Run evolution loop (autonomous)
│     │  ├─ Merge
│     │  ├─ Evaluate (benchmarks)
│     │  ├─ Check anomalies
│     │  ├─ Cull (evolutionary pressure)
│     │  ├─ Apply post-cycle action
│     │  └─ Check stopping condition
│     └─ Progress tracker (minimal, no balloons)
│
├─ Calibration Tab (Set Once)
│  ├─ Evolutionary Pressures (culling, cycles, stopping, post-cycle)
│  ├─ Benchmark Strategy (intensity, categories)
│  └─ Advanced Merge Settings (hidden by default)
│
├─ Lineage Tab
│  ├─ Performance history table
│  ├─ Score trajectory chart
│  └─ Genealogy tree
│
├─ Advanced Tab
│  ├─ SAE analysis (if enabled)
│  └─ Anomaly investigation
│
└─ Logs Tab
   └─ Master log download
```

### Anomaly Flow
```
Evolution runs
    ↓
General benchmark scored
    ↓
Score ≥ 99%?
    ├─ Yes: Anomaly detected → Record to anomalies.json
    │   ├─ Message: "🚨 Anomaly: Check setup/data/weights"
    │   ├─ Save: Model name, merge data, timestamp
    │   └─ Alert user in UI
    │
    └─ No: Continue normally
```

### Benchmark Intensity Flow
```
User selects: Balanced
    ↓
Auto-preselects categories (reasoning, knowledge, language, etc)
    ↓
Calculates questions per category (50-100)
    ↓
Adds general benchmark (25 questions)
    ↓
Shows total questions + estimated time
    ↓
User clicks START → Runs lm-eval with selected tasks
```

---

## Example Session

### Session A: Quick Experiment
```
1. Sidebar: Create "reasoning_quick"
2. Evolution: Select Qwen-0.5B + Mistral-7B
3. Evolution: Select linear + task_arithmetic
4. Calibration: Set culling=50%, cycles=3
5. Calibration: Quick intensity (5-20 q/category)
6. Evolution: Click START
7. [Progress bar, no noise, minimal UI]
8. After 5 min: Evolution complete
9. Lineage: View genealogy table
```

### Session B: Investigation of Anomaly
```
1. Evolution runs normally
2. General benchmark: 100% score detected!
3. Anomaly alert: "🚨 Check setup/weights"
4. Advanced Tab: View anomalies.json
5. Record shows: mutant_c1_p0_ta, all tasks perfect
6. User checks: Model readme, benchmark data, weights
7. Finds: Model corrupted during save (weights file truncated)
8. Fixes: Re-merge with corrected process
9. Re-run evolution
```

### Session C: Deep Analysis
```
1. Calibration: Set post-cycle action = "Analyze"
2. Evolution: Start
3. After cycle 1:
   - Best model evaluated
   - SAE analysis runs
   - Layer specialization recorded
4. After cycle 2:
   - Next best model analyzed
   - Compare layer patterns
   - Insights feed into next cycle
5. Lineage: View both standard scores + layer analysis
6. Advanced: Review SAE discoveries
```

---

## Styling Notes

### Colors
- **Background**: `#0a0e27` (very dark blue)
- **Secondary**: `#12172a` (slightly lighter)
- **Accent**: `#00d9ff` (cyan)
- **Success**: `#10b981` (green)
- **Warning**: `#f59e0b` (amber)
- **Danger**: `#ef4444` (red)
- **Text**: `#e5e7eb` (light gray)

### No Celebrations
- Balloons: Disabled
- Confetti: Disabled
- Exclamation marks: Minimal
- Emojis: Only where necessary (advisor icon, status symbols)

### Animations
- **Pulse**: Subtle 2s loop on running items
- **Transitions**: 0.2s ease on buttons/hovers
- **Progress**: Smooth linear gradient

---

## Future Extensions

### Post-Cycle Actions
- `analyze` → SAE layer analysis (implemented concept)
- `shuffle` → Recombine top performers automatically
- `evaluate` → Deep benchmark eval of best model
- `optimize` → Fine-tune hyperparams on best

### Anomaly Handling
- Auto-retry with different settings
- Compare against known good checkpoints
- Validate model weights checksum

### Advanced Stopping
- Genetic diversity metric (cull clones)
- Fitness plateau detection (moving avg)
- Goal-aware stopping (custom metrics)

---

**Status**: Ready for integration and testing.  
**Next Step**: Replace old app or run v2 side-by-side to compare.
