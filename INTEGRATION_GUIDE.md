# UI Revamp: Integration & Quick Start

**Files created**:
- `breeding_vat/ui/ui_v2_sleek.py` — Dark theme + minimal components
- `breeding_vat/modules/evolutionary_pressures.py` — Broad-stroke calibration
- `breeding_vat/modules/benchmark_selector.py` — Quick/Balanced/Thorough presets
- `breeding_vat/modules/ai_advisor_selector.py` — Quick vs Capable advisor
- `breeding_vat/modules/anomaly_detector.py` — Perfect score detection
- `breeding_vat/ui/app_v2_revamped.py` — Revamped main app (5 tabs)

---

## Quick Start

### Option 1: Test Alongside Old App (Recommended)
```bash
# Old app (original)
streamlit run breeding_vat/ui/app.py

# New app (revamped, in separate terminal)
streamlit run breeding_vat/ui/app_v2_revamped.py --logger.level=debug
```

### Option 2: Replace Current App
```bash
# Backup
mv breeding_vat/ui/app.py breeding_vat/ui/app_old.py

# Use new
cp breeding_vat/ui/app_v2_revamped.py breeding_vat/ui/app.py

# Run
streamlit run breeding_vat/ui/app.py
```

---

## What Changed (For Users)

### Before → After

| Aspect | Before | After |
|--------|--------|-------|
| **Theme** | GitHub light + balloons | Dark + minimal + no celebrations |
| **Settings** | Per-cycle tweaking | Broad strokes (set once) |
| **Merge params** | Always visible (cluttered) | Hidden by default (show if needed) |
| **Benchmarks** | Manual task selection | Presets (Quick/Balanced/Thorough) |
| **Advisor** | Fixed choice | Quick (1B) or Capable (4GB) |
| **Anomalies** | Not flagged | Detected & logged (perfect scores) |
| **UI noise** | Balloons, confetti | Subtle pulse animations |
| **Layout** | 6 tabs (some empty) | 5 focused tabs (all functional) |

---

## First-Time User Flow

### Step 1: Mission Control (Sidebar)
```
← Click "New Mission"
← Enter goal: "Reasoning at 3B scale"
← Click "Initialize"
← See: "Mission active: reasoning_3B_2025-01..."
```

### Step 2: Calibration (Set Strategy Once)
```
← Click "Calibration" tab
← Set Evolutionary Pressures:
   - Culling Rate: 50%
   - Evolution Cycles: 3
   - Stopping: "Exhaust all cycles"
   - Post-Cycle: "Analyze" (SAE)
← Set Benchmarks:
   - Intensity: "Balanced"
   - Categories: Check reasoning, knowledge, language
   - (Estimated: 300 questions, ~50 min)
← No need to adjust merge params (hidden by default)
```

### Step 3: Evolution (Just Select & Go)
```
← Click "Evolution" tab
← Base Models: Select Qwen-0.5B + Mistral-7B
← Merge Methods: Select linear + task_arithmetic
← Advisor: Choose "Quick Advisor" (fast) or "Capable" (detailed)
← Click "🚀 START EVOLUTION"
← Watch progress (minimal UI, no balloons)
← After 30-60 min: Done!
```

### Step 4: Results
```
← Click "Lineage" tab
← See genealogy table: All models, scores, methods
← Click "Advanced" tab (if anomaly detected)
   - View anomaly log
   - Check recommendations
```

---

## Key UX Changes

### 1. Sleek Dark Theme
- Professional dark background (#0a0e27)
- Cyan accents (#00d9ff)
- Minimal borders, rounded corners
- **Result**: Less eye strain, feels premium

### 2. No Celebrations
- Before: `st.balloons()` after every evolution
- After: `NoiseLevel.suppress_celebrations()` + subtle UI
- **Result**: More focused, addictive feel

### 3. Broad-Stroke Calibration
- Before: Set method params every cycle
- After: Set evolutionary pressures once, run autonomously
- **Result**: Less decision fatigue, faster iteration

### 4. Hidden Merge Settings
- Before: 7 expanders cluttering sidebar
- After: 1 collapsible "Show Advanced" in Calibration tab
- **Result**: Cleaner UI, merge experts can still tweak

### 5. Benchmark Presets
- Before: Manual task list selection
- After: Quick/Balanced/Thorough + category checkboxes
- **Result**: Less decision paralysis, smart defaults

### 6. AI Advisor Choice
- Before: Fixed model
- After: Quick (1B, instant) or Capable (7B, detailed)
- **Result**: Flexibility for different use cases

### 7. Anomaly Detection
- Before: Perfect scores not flagged
- After: ≥99% on general benchmark → Alert + record
- **Result**: Catch setup errors early

---

## Component Details

### ProgressTracker (Replaces Old Alerts)
```python
tracker = ProgressTracker(total=3, label="Evolution")

tracker.log("Starting evolution", "success")
tracker.update(1, "Cycle 1: Merging", {"Method": "linear"})
tracker.log("Merge complete", "info")
tracker.update(2, "Cycle 2: Evaluating", {"Score": "0.732"})
tracker.complete("Evolution finished")
```

**Features**:
- Progress bar at top
- Inline status updates (no popups)
- Log entries (max 8 recent)
- Metrics display
- Complete message at end

### StatusIndicator (Replaces Old st.error/st.success)
```python
StatusIndicator.success("Mission active")
StatusIndicator.info("Setting calibration")
StatusIndicator.warning("Configure pressures first")
StatusIndicator.error("Failed: model not found")
```

**Result**: Subtle, professional tone

### CompactMetrics (Replaces st.metric)
```python
CompactMetrics.render_trio(
    "Cycles", "3/3",
    "Best", "0.745",
    "Status", "Complete"
)
```

**Result**: Compact, scannable metrics

---

## Testing Checklist

### UI Rendering
- [ ] Dark theme loads (no light background)
- [ ] Cyan accents visible on buttons/links
- [ ] No balloons or confetti after simulation
- [ ] Minimal borders and rounded corners

### Calibration
- [ ] Evolutionary Pressures UI renders
  - [ ] Culling slider works
  - [ ] Cycles input works
  - [ ] Stopping condition dropdown works
  - [ ] Post-cycle actions show correctly
- [ ] Benchmark Selector UI renders
  - [ ] Quick/Balanced/Thorough toggle works
  - [ ] Category checkboxes appear
  - [ ] Question counts update
  - [ ] Total + estimated time shown

### Evolution
- [ ] Model selection works (multi-select)
- [ ] Method selection works
- [ ] Advisor choice toggles correctly
- [ ] START button present and clickable
- [ ] Requires Calibration tab config before starting

### Progress
- [ ] ProgressTracker displays correctly
- [ ] Progress bar updates
- [ ] Log entries appear (8 most recent)
- [ ] Metrics update in real-time
- [ ] No balloons at completion

### Anomaly Detection
- [ ] General benchmark always runs
- [ ] Perfect score (≥99%) → Alert
- [ ] Alert message explains causes
- [ ] Record saved to anomalies.json

---

## Troubleshooting

### "Dark theme not applied"
→ Check `SleekUITheme.apply()` called at module import
→ Run: `streamlit cache clear && streamlit run app.py`

### "Balloons still appearing"
→ Check `NoiseLevel.suppress_celebrations()` in __init__
→ May need to clear Streamlit's internal cache

### "Calibration settings not saved"
→ Check `st.session_state` is being used
→ Verify settings passed to evolution loop

### "Anomaly detection not working"
→ Ensure `AnomalyDetector` initialized with exp['paths']['root']
→ Check general benchmark score is being captured
→ Verify anomalies.json path correct

---

## Advanced Customization

### Adjust Dark Theme Colors
Edit `breeding_vat/ui/ui_v2_sleek.py`:
```python
# Change cyan to purple
--accent-primary: #a78bfa;  # Purple instead
--accent-primary: #f472b6;  # Pink instead
```

### Add More Benchmark Categories
Edit `breeding_vat/modules/benchmark_selector.py`:
```python
BENCHMARK_CATEGORIES["music"] = {
    "name": "Music Understanding",
    "tasks": ["music_qa", "lyrics_understanding"],
    "quick": 10,
    "balanced": 50,
    "thorough": 200
}
```

### Adjust Anomaly Threshold
Edit `breeding_vat/modules/anomaly_detector.py`:
```python
PERFECT_THRESHOLD = 0.99  # Change to 0.95 or 0.98
```

### Add Post-Cycle Actions
Edit `breeding_vat/modules/evolutionary_pressures.py`:
```python
class PostCycleAction(Enum):
    CUSTOM = "custom"  # Your action here
    # Add handler in apply_evolutionary_pressures()
```

---

## Performance Notes

### Dark Theme
- CSS-only, negligible overhead
- Applies once on page load
- No runtime computation

### ProgressTracker
- Efficient container updates
- Logs capped at 8 recent entries
- Metrics container reused

### Benchmark Selector
- Category selection cached in session_state
- Question count calculation O(n) where n=categories (~10)
- Negligible impact

### Anomaly Detector
- JSON write per anomaly (blocking but rare)
- File I/O only if anomaly detected
- No continuous monitoring

---

## Migration from Old App

### Breaking Changes
None! Both apps can coexist.

### Recommended Migration Path
1. **Week 1**: Run v2 side-by-side, A/B test
2. **Week 2**: Gather feedback, iterate UI
3. **Week 3**: Replace if stable, keep v1 backup

### Data Compatibility
- Experiment folders: **Compatible** (v1 can resume v2 experiments and vice versa)
- Database schema: **Compatible** (no changes to underlying structure)
- Merge configs: **Compatible** (YAML format unchanged)
- Logs: **Compatible** (text-based, no format change)

---

## Support & Feedback

### If UI feels too dark
→ Edit CSS in `ui_v2_sleek.py` background colors

### If animations too subtle
→ Adjust pulse @keyframes speed

### If missing old features
→ Most are in "Advanced" tab or hidden by default

### If benchmarks take too long
→ Switch to "Quick & Dirty" intensity

---

**Ready to launch!** 🚀
