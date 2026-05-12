# Local Model Upload Integration

## Overview

The Breeding Vat now supports uploading and using local models directly in evolution experiments. Local models are:
- **Transferred** to a central model zoo (`breeding_vat/data/model_zoo/`)
- **Preserved** as originals (never modified)
- **Available** alongside HuggingFace models in the UI
- **Tracked** with metadata (source, description, transfer date)

## Architecture

```
User's Local Drive
└── /path/to/my-model/
    ├── config.json
    ├── model.safetensors
    └── tokenizer.json

                ↓ (transfer via Streamlit UI)

Model Zoo (Preserved Originals)
└── breeding_vat/data/model_zoo/
    └── my-qwen-finetuned/
        ├── config.json
        ├── model.safetensors
        ├── tokenizer.json
        └── .model_metadata.json
            {
              "name": "my-qwen-finetuned",
              "original_path": "/path/to/my-model/",
              "transferred_at": "2025-01-15T10:30:00",
              "size_bytes": 5368709120,
              "metadata": {"description": "Finetuned on math..."}
            }

Experiment Evolution
└── breeding_vat/data/experiments/reasoning_3B_2025-01-15_152347/
    └── merged_models/
        ├── mutant_c1_p0_sl/   (merged from my-qwen + Qwen-0.5B)
        ├── mutant_c1_p1_ti/
        └── ...
```

## Components

### 1. `ModelTransfer` (`breeding_vat/modules/model_transfer.py`)

Handles model registration and validation.

**Key Methods:**
- `register_local_model(local_path, model_name, experiment_id, metadata)` - Transfer a model to zoo
- `validate_model_path(path)` - Check if path contains valid model
- `list_local_models()` - List all transferred models
- `get_model_path(model_name)` - Get full path to a transferred model
- `get_model_info(model_name)` - Get metadata about a model

**Usage:**
```python
from breeding_vat.modules.model_transfer import ModelTransfer

transfer = ModelTransfer()

# Transfer a local model
success, dest_path, info = transfer.register_local_model(
    local_path="/home/user/my-qwen-finetuned",
    model_name="my-qwen-finetuned",
    experiment_id="reasoning_3B_exp",
    metadata={"description": "Finetuned on math dataset"}
)

if success:
    print(f"Model at: {dest_path}")
    print(f"Size: {info['size_bytes'] / (1024**3):.2f} GB")

# List all local models
local_models = transfer.list_local_models()
for model in local_models:
    print(f"{model['name']}: {model['size_bytes'] / (1024**3):.2f} GB")
```

### 2. `ModelPathResolver` (`breeding_vat/modules/model_path_resolver.py`)

Resolves model identifiers (HF IDs or local names) to actual paths.

**Key Methods:**
- `resolve(model_id)` - Convert ID to path (local or HF)
- `is_local_model(model_id)` - Check if it's a local model
- `is_hf_model(model_id)` - Check if it's a HF ID

**Usage:**
```python
from breeding_vat.modules.model_path_resolver import ModelPathResolver

resolver = ModelPathResolver(model_transfer=transfer)

# Resolve local model name
success, path = resolver.resolve("my-qwen-finetuned")
# Returns: (True, "breeding_vat/data/model_zoo/my-qwen-finetuned/")

# Resolve HF model ID
success, path = resolver.resolve("Qwen/Qwen2.5-0.5B-Instruct")
# Returns: (True, "Qwen/Qwen2.5-0.5B-Instruct")  # or cached path if available

# Check type
print(resolver.is_local_model("my-qwen-finetuned"))  # True
print(resolver.is_hf_model("Qwen/Qwen2.5-0.5B-Instruct"))  # True
```

### 3. Streamlit UI Integration

**Location:** `breeding_vat/ui/app.py` → "Evolution" tab → "Base Models" section

**UI Flow:**

1. **Model Selection:**
   - Multiselect combines HuggingFace models + previously uploaded local models
   - All options appear in the same dropdown

2. **Upload Local Model:**
   - Expander: "📤 Upload Local Model"
   - Inputs:
     - Local path (validated in real-time)
     - Display name (auto-sanitized)
     - Description (optional, for metadata)
   - Transfer button copies model to zoo
   - Automatic UI refresh after successful upload

3. **Usage in Evolution:**
   - Local models available immediately after upload
   - Treated identically to HuggingFace models in merge pipeline
   - Full lineage tracking (parents include local models)

**Example:**
```
User uploads: /home/user/my-qwen-finetuned
Display name: my-qwen-finetuned

Available in UI as:
- "my-qwen-finetuned" (local, 5.4 GB)

Can mix in evolution:
- Base model 1: Qwen/Qwen2.5-0.5B-Instruct (HF)
- Base model 2: my-qwen-finetuned (local)
- Merge via SLERP → mutant_c1_p0_sl
```

## Workflow: End-to-End

### Step 1: Upload Local Model (One-Time)

```
1. Open Streamlit UI
2. Navigate to "Evolution" tab
3. Expand "📤 Upload Local Model"
4. Enter:
   - Local path: /path/to/my-model/
   - Display name: my-qwen-finetuned
   - Description: Finetuned on math reasoning
5. Click "🚀 Transfer Model"
6. Wait for transfer (size dependent)
7. Model appears in selection dropdown
```

### Step 2: Create Evolution Experiment

```
1. Sidebar → "New Mission"
2. Define goal: "Combine my finetuned + Qwen"
3. Click "🚀 Initialize"
4. In "Evolution" tab → "Base Models":
   - Select: "my-qwen-finetuned"
   - Select: "Qwen/Qwen2.5-0.5B-Instruct"
5. Choose merge methods (e.g., SLERP, TIES)
6. Click "▶️ START EVOLUTION"
```

### Step 3: Lineage & Comparison

```
Evolution creates: mutant_c1_p0_sl
  Parents:
    - my-qwen-finetuned (local, original preserved)
    - Qwen/Qwen2.5-0.5B-Instruct (HF, original preserved)
  Method: SLERP
  Score: 0.7245

Comparison:
  - Original: my-qwen-finetuned score = 0.6890
  - Merged: mutant_c1_p0_sl score = 0.7245
  - Improvement: +5.2%
```

## File Validation

The UI validates local model directories by checking for:

**Required:** `config.json`
- Tokenizer config (HuggingFace format)

**Optional (any one):**
- `model.safetensors` (recommended, memory-efficient)
- `pytorch_model.bin` (PyTorch format)
- `model.bin` (older PyTorch format)
- `tokenizer.json`

If only `config.json` exists: ✓ Valid (weights may be downloaded on-demand)

## Important Notes

### Preservation of Originals

1. **Local models** are copied to `model_zoo/` → Never modified
2. **HuggingFace models** stay in `~/.cache/huggingface/` → Never modified
3. **Merged models** go to `experiments/{exp_id}/merged_models/` → Experiment-scoped

### Storage Management

- Each local model upload creates a copy
- Size displayed in UI (GB)
- Metadata stored in `.model_metadata.json`
- Can be deleted from zoo without affecting originals on disk

### Path Resolution

When evolution runs with mixed models:
1. Local model name → resolved to `model_zoo/` path
2. HF model ID → resolved to cache path or downloaded on-demand
3. Merger treats both as file paths (transparent to merge engine)

### Metadata Tracking

Each local model includes:
```json
{
  "name": "my-qwen-finetuned",
  "original_path": "/home/user/my-qwen-finetuned/",
  "transferred_at": "2025-01-15T10:30:00",
  "experiment_id": "reasoning_3B_2025-01-15_152347",
  "source": "local_upload",
  "size_bytes": 5368709120,
  "metadata": {
    "description": "Finetuned on math dataset",
    "uploaded_at": "2025-01-15T10:30:00"
  }
}
```

## Integration Points

### For Developers

To use local models programmatically:

```python
from breeding_vat.modules.model_transfer import ModelTransfer
from breeding_vat.modules.model_path_resolver import ModelPathResolver
from breeding_vat.modules.merge.merger import AdvancedMerger
from breeding_vat.orchestrator.runner import TaskRunner

# Setup
transfer = ModelTransfer()
resolver = ModelPathResolver(model_transfer=transfer)
runner = TaskRunner()
merger = AdvancedMerger(runner)

# Transfer local model
success, dest, info = transfer.register_local_model(
    "/path/to/local/model",
    "my-custom-model"
)

# Use in merge
if success:
    resolved, model_path = resolver.resolve("my-custom-model")
    
    # Merge with HF model
    output = merger.slerp_merge(
        base_model="Qwen/Qwen2.5-0.5B-Instruct",
        models=[model_path, "Qwen/Qwen2.5-1.5B-Instruct"],
        output_path="breeding_vat/data/merged_models/result/"
    )
```

### For Merge Engines

The `ModelPathResolver` can be integrated into MergeKit and FusionBench engines:

```python
# In AdvancedMerger or merge engines
def resolve_models(self, model_ids: list):
    """Convert all model IDs to paths before passing to merge backend."""
    paths = []
    for model_id in model_ids:
        success, path = self.resolver.resolve(model_id)
        if success:
            paths.append(path)
        else:
            raise ValueError(f"Could not resolve: {model_id}")
    return paths
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Upload fails - "Path not found" | Check path exists and is readable |
| Upload fails - "Invalid model name" | Use alphanumeric, dash, underscore only |
| Upload fails - "Model already exists" | Choose a different display name |
| Validation shows "No model config found" | Ensure `config.json` exists in directory |
| Model appears in UI but merge fails | Ensure model format matches (safetensors or PyTorch bin) |
| Local model not showing in dropdown | Try page refresh or check model zoo permissions |

---

**Date:** January 15, 2025  
**Status:** Ready for integration testing
