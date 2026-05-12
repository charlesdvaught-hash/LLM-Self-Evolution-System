# Complete Model Selection Flow - Visual

## End-to-End Streamlit UI Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                Evolution Tab - Model Selection                 │
└─────────────────────────────────────────────────────────────────┘

STEP 1: ADD LOCAL MODEL (Optional, Collapsible)
┌─ ➕ Add Local Model to Zoo ────────────────────────────────────┐
│                                                                 │
│  Model directory path: [/home/user/models/my-model/  ]        │
│  Display name:         [my-qwen-reasoning         ]            │
│                                                                 │
│  ✅ Valid model detected (found config.json)                   │
│                                                                 │
│                    [📤 Add to Zoo]                             │
│                                                                 │
│  (User clicks "📤 Add")                                         │
│  → Validates path                                              │
│  → Copies to breeding_vat/data/model_zoo/                      │
│  → Updates _registry.json                                      │
│  → Shows: ✅ Added 'my-qwen-reasoning' (5.6 GB)               │
│  → Clears form                                                 │
│  → UI reruns (dropdowns update with new model)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

─────────────────────────────────────────────────────────────────────

STEP 2: SELECT MODELS IN SLOTS
┌─ 🎯 Model Slots (Select 1-5) ─────────────────────────────────┐
│  Pick models for evolution. Leave empty for AI to suggest.    │
│                                                                 │
│  Slot 1           Slot 2            Slot 3                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ [HF] Qwen 3B │ │ [Local] My    │ │ (empty - AI) │  ...     │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│  Filled: 2 models | Empty: 3 slots | AI Will Fill: 3         │
│                                                                 │
│  (Dropdowns always show updated list from zoo registry)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

─────────────────────────────────────────────────────────────────────

STEP 3: GENERATE RECIPES
                                                                  │
                        [🤖 Generate Recipes]  ←── Click         │
                                                                  │
         ↓ (Analyzes goal + models + methods)                   │
         
┌─ 📋 Generated Recipes ────────────────────────────────────────┐
│                                                                 │
│  ├─ 🚀 Aggressive Exploration                                  │
│  │  Try all merge methods, minimal pre-tuning                 │
│  │                                                              │
│  │  Strategy: diverse  | Cycles: 5 | Culling: 50%            │
│  │  Pre-spec: none     | Methods: 7 selected                  │
│  │  Why: Explore diverse merge techniques quickly             │
│  │                                                              │
│  │  [✅ Use 'Aggressive Exploration']                         │
│  │                                                              │
│  ├─ 🎯 Quality-Focused  ←── Pre-selected (expanded)           │
│  │  Curated methods + SAE pre-specialization                  │
│  │                                                              │
│  │  Strategy: quality  | Cycles: 3 | Culling: 30%            │
│  │  Pre-spec: sae_guided | Methods: 4 selected               │
│  │  Why: Focus on best-quality merges with layer analysis    │
│  │                                                              │
│  │  [✅ Use 'Quality-Focused']  ←── User clicks               │
│  │                                                              │
│  └─ ⚖️ Balanced                                                 │
│     Moderate diversity + task specialization                   │
│                                                                 │
│     Strategy: balanced | Cycles: 4 | Culling: 40%            │
│     Pre-spec: task_lora | Methods: 5 selected                │
│     Why: Balance quality and exploration                       │
│                                                                 │
│     [✅ Use 'Balanced']                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

─────────────────────────────────────────────────────────────────────

STEP 4: RECIPE SUMMARY (After selection)
┌─ 📊 Recipe Summary ───────────────────────────────────────────┐
│                                                                 │
│  Strategy: Quality  | Cycles: 3 | Methods: 4                 │
│                                                                 │
│  Approach: Focus on best-quality merges with layer analysis  │
│                                                                 │
│  [📋 Full Recipe Details ▼]                                   │
│     Strategy Type: quality                                    │
│     Total Cycles: 3                                           │
│     Culling Rate: 30%                                         │
│     Pre-specialization: sae_guided                            │
│     Merge Methods: task_arithmetic, regmean, frankenmerge    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

─────────────────────────────────────────────────────────────────────

STEP 5: LAUNCH EVOLUTION
                                                                  │
                      [▶️ START EVOLUTION]  ←── Click            │
                                                                  │
         ↓ (Applies recipe parameters, starts evolution)        │
         
┌─ 🚀 Evolution in Progress ────────────────────────────────────┐
│                                                                 │
│  [█████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 1/3 cycles │
│  ▶️ Cycle 1: Merging with task_arithmetic...                 │
│                                                                 │
│  [15:24:12] Evolution started                                 │
│  [15:24:15] Merge method: task_arithmetic                    │
│  [15:24:45] Merge complete: mutant_c1_p0_ta                 │
│  [15:25:00] Evaluation complete: score=0.723                │
│                                                                 │
│  Progress: 33% | Current Score: 0.723 | Best: 0.723         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: UI → Zoo → Registry → Slots → Recipes → Evolution

```
┌──────────────────┐
│  User Input      │
│  (Streamlit UI)  │
└────────┬─────────┘
         │
         ├─ Path + Name ──→ render_model_zoo_uploader()
         │                    ├─ Validate path
         │                    ├─ Copy to zoo
         │                    └─ model_zoo.add_local_model()
         │                         │
         │                         ├─ Copy dir to breeding_vat/data/model_zoo/{name}/
         │                         ├─ Create .model_metadata.json
         │                         └─ Update _registry.json
         │
         ├─ Slot selections ──→ render_model_slots()
         │                        ├─ Read _registry.json
         │                        ├─ Build dropdown options
         │                        └─ Return selected_slots list
         │
         ├─ Generate button ──→ render_recipe_generator()
         │                        ├─ Get manual_models from slots
         │                        ├─ Count empty_slots
         │                        ├─ Call AIRecipeGenerator
         │                        │   └─ Generate 3 recipes
         │                        └─ Display recipes + buttons
         │
         ├─ Select recipe ──→ Stored in st.session_state
         │                     └─ render_recipe_summary()
         │
         └─ START button ──→ Evolution starts
                              ├─ RecipeExecutor.apply_recipe()
                              ├─ Get base_models from slots
                              └─ Run evolution loop (existing code)
```

---

## Registry File (_registry.json)

```json
{
  "version": "1.0",
  "created_at": "2025-01-15T10:30:00",
  "models": {
    "my-qwen-reasoning": {
      "name": "my-qwen-reasoning",
      "display_name": "My Qwen Reasoning",
      "type": "reasoning",
      "description": "Local upload",
      "tags": [],
      "size_gb": 5.6,
      "path": "breeding_vat/data/model_zoo/my-qwen-reasoning",
      "added_at": "2025-01-15T10:30:00",
      "source": "local_upload"
    },
    "my-retrieval": {
      "name": "my-retrieval",
      "display_name": "My Retrieval Model",
      "type": "retrieval",
      "description": "Local upload",
      "tags": [],
      "size_gb": 7.2,
      "path": "breeding_vat/data/model_zoo/my-retrieval",
      "added_at": "2025-01-15T10:35:00",
      "source": "local_upload"
    }
  }
}
```

When UI refreshes, dropdowns automatically include these models.

---

## Complete Operations

### Operation 1: Add Model to Zoo

```python
# UI Call:
success, msg = model_zoo.add_local_model(
    local_path="/home/user/models/my-qwen/",
    model_name="my-qwen-reasoning",
    model_type="reasoning"
)

# What happens:
1. Validates /home/user/models/my-qwen/ has config.json ✓
2. Copies entire directory to:
   breeding_vat/data/model_zoo/my-qwen-reasoning/
3. Creates .model_metadata.json in destination
4. Updates _registry.json with entry
5. Returns: (True, "Added 'my-qwen-reasoning' (5.6 GB)")

# Result:
- Model permanently in zoo
- Available in slot dropdowns next reload/rerun
- Can be reused in future experiments
```

### Operation 2: List Models in Dropdowns

```python
# UI Call:
all_models = model_zoo.list_all_models()

# Returns:
[
  {
    "name": "my-qwen-reasoning",
    "display_name": "My Qwen Reasoning",
    "source_type": "local",
    "type": "reasoning",
    "size_gb": 5.6,
    ...
  },
  {
    "name": "Qwen/Qwen2.5-3B-Instruct",
    "display_name": "Qwen 3B",
    "source_type": "huggingface",
    ...
  },
  ...
]

# UI builds dropdown:
"[Local] My Qwen Reasoning" → "my-qwen-reasoning"
"[HF] Qwen 3B" → "Qwen/Qwen2.5-3B-Instruct"
"(empty - let AI choose)" → None
```

### Operation 3: Generate Recipes

```python
# UI Call:
selected_slots = [
  "my-qwen-reasoning",      # Manual
  None,                      # Empty
  "Qwen/Qwen2.5-3B-Instruct", # Manual
  None,
  None
]

recipes = AIRecipeGenerator(...).generate_recipes(
    goal="Multi-task reasoning",
    manual_models=["my-qwen-reasoning", "Qwen/Qwen2.5-3B-Instruct"],
    empty_slots=3,
    available_methods=["linear", "task_arithmetic", "moe"],
    num_recipes=3
)

# Returns 3 recipes with different strategies
```

### Operation 4: Execute Evolution

```python
# User selects recipe and clicks START EVOLUTION

selected_recipe = {
    "name": "🎯 Quality-Focused",
    "strategy": "quality",
    "merge_methods": ["task_arithmetic", "regmean"],
    "specialization": "sae_guided",
    "num_cycles": 3,
    "culling_rate": 30
}

# Apply recipe
exp = RecipeExecutor.apply_recipe(exp, selected_recipe)

# Get base models from slots
base_models = ["my-qwen-reasoning", "Qwen/Qwen2.5-3B-Instruct"]

# Run evolution (standard loop)
best_model = evo.run_waterfall(
    base_models=base_models,
    goal=exp['goal'],
    num_cycles=3,  # From recipe
    merge_methods=["task_arithmetic", "regmean"],  # From recipe
    ...
)
```

---

## YES - Everything Works Via Streamlit UI

✅ **Add Models**: Form input → model_zoo.add_local_model()  
✅ **Save Models**: Copies to breeding_vat/data/model_zoo/  
✅ **Move Models**: Automatically in registry, available in slots  
✅ **Persistent**: _registry.json survives across sessions  
✅ **No Manual File Ops**: All done through Streamlit forms  
✅ **One-Click Launch**: Recipe → START EVOLUTION  

**No command line needed. Everything in the UI.** ✓
