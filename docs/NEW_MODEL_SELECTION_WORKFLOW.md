# New Model Selection Workflow

**Problem Solved**: Replace clunky sequential model uploads with clean, slot-based selection + AI recipe generation.

---

## Old Workflow (Clunky)

```
1. Upload Model 1 ✅
2. Upload Model 2 ✅
3. Select from zoo
   (no way to add more models in same session)
4. Manually pick merge methods
5. (no AI assistance on strategy)
```

## New Workflow (Clean)

```
1. View all models (local zoo + HuggingFace)
2. Quick add any local model to zoo
3. Select 1-5 models in slots (empty slots for AI)
4. Click "Generate Recipes"
5. AI analyzes goal + models → suggests 3 strategies
6. Pick favorite recipe
7. Click "START EVOLUTION"
```

---

## Components

### 1. Global Model Zoo Manager
**File**: `breeding_vat/modules/model_zoo.py`

```python
from breeding_vat.modules.model_zoo import GlobalModelZoo

zoo = GlobalModelZoo()

# Add local model (persistent)
success, msg = zoo.add_local_model(
    local_path="/path/to/my-model",
    model_name="my-qwen-finetuned",
    model_type="reasoning",
    tags=["3B", "finetuned"]
)

# List all models
models = zoo.list_all_models()

# Search
models = zoo.search_models("qwen")

# Filter by type
reasoning_models = zoo.get_models_by_type("reasoning")
```

**Registry File**: `breeding_vat/data/model_zoo/_registry.json`
- Persistent across sessions
- Tracks: name, type, description, tags, size, source
- Query-able

### 2. Slot-Based Model Selector
**File**: `breeding_vat/modules/recipe_generator.py` (SlotBasedModelSelector class)

```python
from breeding_vat.modules.recipe_generator import SlotBasedModelSelector

selector = SlotBasedModelSelector(model_zoo)

# Fill slots
selector.set_slot(0, "Qwen/Qwen2.5-3B-Instruct")  # Manual
selector.set_slot(1, "my-custom-model")            # Local
# Slots 2, 3, 4 left empty for AI

# Check status
filled = selector.get_filled_models()      # [2 models]
empty_count = selector.get_empty_slots_count()  # 3
```

### 3. AI Recipe Generator
**File**: `breeding_vat/modules/recipe_generator.py` (AIRecipeGenerator class)

```python
from breeding_vat.modules.recipe_generator import AIRecipeGenerator

generator = AIRecipeGenerator(merger, advisor, model_zoo)

recipes = generator.generate_recipes(
    goal="Long-context reasoning at 3B",
    manual_models=["Qwen/Qwen2.5-3B", "my-custom"],
    empty_slots=3,
    available_methods=["task_arithmetic", "moe", "voting"],
    num_recipes=3
)

# Returns:
# [
#   {
#     "name": "🚀 Aggressive Exploration",
#     "strategy": "diverse",
#     "merge_methods": [...],
#     "specialization": "none",
#     "num_cycles": 5,
#     "reasoning": "..."
#   },
#   ...
# ]
```

### 4. Streamlit UI Components
**File**: `breeding_vat/ui/model_selection_ui.py`

```python
from breeding_vat.ui.model_selection_ui import (
    render_model_zoo_uploader,
    render_model_slots,
    render_recipe_generator,
    render_recipe_summary
)

# In app.py Evolution tab:

# 1. Quick zoo upload
render_model_zoo_uploader(model_zoo)

# 2. Slot selection (returns list of 5 models)
selected_slots = render_model_slots(model_zoo)

# 3. Recipe generation
selected_recipe = render_recipe_generator(
    goal=experiment['goal'],
    selected_slots=selected_slots,
    available_methods=merge_methods,
    merger=merger,
    advisor=advisor,
    model_zoo=model_zoo,
    num_recipes=3
)

# 4. Show summary
if selected_recipe:
    render_recipe_summary(selected_recipe)
```

---

## UI Layout (Streamlit)

```
┌─────────────────────────────────────────────────────┐
│  🎯 Model Selection & Recipe Generation             │
└─────────────────────────────────────────────────────┘

┌─ ➕ Add Local Model to Zoo ─────────────────────────┐  ← Collapsible
│  Path: [/path/to/model        ] [📤 Add]            │
│  ✅ Valid model detected                            │
│  Display name: [my-qwen-finetuned]                  │
└─────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────

┌─ 🎯 Model Slots (up to 5) ──────────────────────────┐
│  Select manually OR leave empty for AI              │
│                                                      │
│  Slot 1        Slot 2         Slot 3               │
│  ┌──────────┐  ┌──────────┐   ┌──────────┐         │
│  │ Qwen 3B  │  │ My Model │   │ (empty)  │  ...    │
│  └──────────┘  └──────────┘   └──────────┘         │
│                                                      │
│  ├─ Filled: 2        ├─ Empty: 3        ├─ AI: 3  │
└─────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────

              [🤖 Generate Recipes]

───────────────────────────────────────────────────────

┌─ 📋 Generated Recipes ──────────────────────────────┐  ← After click
│                                                      │
│  ├─ 🚀 Aggressive Exploration                       │
│  │  Try all methods, minimal pre-tuning             │
│  │  Cycles: 5 | Specialization: none                │
│  │  [✅ Use This Recipe]                            │
│  │                                                   │
│  ├─ 🎯 Quality-Focused                              │
│  │  Curated methods + pre-specialization            │
│  │  Cycles: 3 | Specialization: sae_guided          │
│  │  [✅ Use This Recipe]                            │
│  │                                                   │
│  └─ ⚖️ Balanced                                      │
│     Moderate diversity + task specialization        │
│     Cycles: 4 | Specialization: task_lora           │
│     [✅ Use This Recipe]                            │
│                                                      │
└─────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────

┌─ 📊 Recipe Summary ────────────────────────────────┐  ← After select
│  Recipe: Aggressive  | Cycles: 5  | Methods: 7    │
│  "Explore diverse merge techniques quickly"        │
│                                                     │
│  [Full Recipe Details ▼]                           │
└─────────────────────────────────────────────────────┘

              [▶️ START EVOLUTION]
```

---

## Step-by-Step Usage

### Step 1: Add Models to Zoo (Optional)

```
Sidebar → ➕ Add Local Model to Zoo
  Path: /home/user/models/my-qwen-3b/
  [📤 Add]
  
  Display name: my-qwen-reasoning
  [Submit]
  
✅ Added 'my-qwen-reasoning' (5.6 GB)
```

Model now in zoo permanently. Reusable in future experiments.

### Step 2: Select Models in Slots

```
Evolution Tab → 🎯 Model Slots

Slot 1: [Qwen 3B ▼]
Slot 2: [My Qwen Reasoning ▼]
Slot 3: [(empty - let AI choose) ▼]
Slot 4: [(empty - let AI choose) ▼]
Slot 5: [(empty - let AI choose) ▼]

Filled: 2 | Empty: 3 | AI will choose: 3
```

### Step 3: Generate Recipes

```
[🤖 Generate Recipes]

(analyzing goal + models + methods...)

📋 Generated Recipes

🚀 Aggressive Exploration
  All methods, minimal pre-tuning
  Cycles: 5, Specialization: none
  [✅ Use This Recipe]

🎯 Quality-Focused
  Curated + SAE pre-specialization
  Cycles: 3, Specialization: sae_guided
  [✅ Use This Recipe]  ← User clicks here

⚖️ Balanced
  Moderate diversity + task specialization
  Cycles: 4, Specialization: task_lora
  [✅ Use This Recipe]
```

### Step 4: Review & Launch

```
📊 Recipe Summary
Recipe: Quality-Focused | Cycles: 3 | Methods: 4
"Focus on best-quality merges with layer analysis"

[Full Recipe Details ▼]

[▶️ START EVOLUTION]
```

Evolution runs with recipe params.

---

## What Recipes Do

Each recipe is a **merge strategy** + **parameter set**:

| Recipe | Strategy | Methods | Cycles | Specialization | Best For |
|--------|----------|---------|--------|----------------|----------|
| 🚀 Aggressive | Diverse | All 7 | 5 | None | Explore fast |
| 🎯 Quality | Curated | Top 4 | 3 | SAE-guided | Best results |
| ⚖️ Balanced | Mixed | 4-5 | 4 | Task-LoRA | Balanced |

Users can also **create custom recipes** (future UI feature).

---

## Benefits vs Old Workflow

| Aspect | Old | New |
|--------|-----|-----|
| **Add model** | Sequential upload | Quick form (stay on page) |
| **Reuse models** | Not tracked | Persistent zoo registry |
| **Select models** | Dropdown only | 5 slots + AI fill |
| **Strategy choice** | Manual method picks | AI suggests 3 recipes |
| **One-click launch** | No | Yes ✅ |
| **Multiple experiments** | Start over each time | Zoo persistent |

---

## Code Integration Example

Replace the old model selection section in `app.py`:

```python
# OLD (REMOVE):
with st.expander("📤 Upload Local Model", expanded=False):
    uploaded_path = st.text_input("Local model path", ...)
    # ... clunky sequential UI ...

# NEW (ADD):
from breeding_vat.ui.model_selection_ui import (
    render_model_zoo_uploader,
    render_model_slots,
    render_recipe_generator,
    render_recipe_summary
)

# Quick upload (optional, collapsible)
with st.expander("➕ Add Local Model to Zoo", expanded=False):
    render_model_zoo_uploader(st.session_state.model_zoo)

# Slot selection
selected_slots = render_model_slots(st.session_state.model_zoo)

# Recipe generation
selected_recipe = render_recipe_generator(
    goal=exp['goal'],
    selected_slots=selected_slots,
    available_methods=merge_methods,
    merger=st.session_state.merger,
    advisor=st.session_state.advisor,
    model_zoo=st.session_state.model_zoo
)

# Recipe summary + launch
if selected_recipe:
    render_recipe_summary(selected_recipe)
    if st.button("▶️ START EVOLUTION", type="primary"):
        # ... execute ...
```

---

## API Quick Reference

### Model Zoo
```python
zoo = GlobalModelZoo()
zoo.add_local_model(local_path, "name")
zoo.list_all_models()
zoo.search_models("query")
zoo.get_models_by_type("reasoning")
```

### Slot Selector
```python
selector = SlotBasedModelSelector(zoo)
selector.set_slot(0, "model_id")
selector.get_filled_models()
selector.get_empty_slots_count()
```

### Recipe Generator
```python
gen = AIRecipeGenerator(merger, advisor, zoo)
recipes = gen.generate_recipes(goal, manual_models, empty_slots, methods)
```

### UI Components
```python
render_model_zoo_uploader(zoo)
render_model_slots(zoo)  # → List[Optional[str]]
render_recipe_generator(...)  # → Dict (recipe)
render_recipe_summary(recipe)
```

---

## Future Enhancements

- [ ] Custom recipe builder (users create own strategies)
- [ ] Recipe history (save favorite recipes)
- [ ] Model details sidebar (size, type, tags)
- [ ] Batch upload (multiple models at once)
- [ ] Recipe preview (what methods will run)
- [ ] AI empty slot filling (recommend specific models)
