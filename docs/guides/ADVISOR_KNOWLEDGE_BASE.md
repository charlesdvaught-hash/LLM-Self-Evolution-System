# Advisor Knowledge Base

**For the 0.8B Advisor Model**

This document helps the advisor model navigate The Breeding Vat's knowledge base and provide accurate recommendations.

## Knowledge Base Location

All documentation is in: `docs/`

**Structure:**
- `docs/guides/` - How-to guides and tutorials
- `docs/reference/` - Technical reference and architecture
- `docs/KNOWLEDGE_BASE_MANIFEST.json` - Machine-readable index (use this!)

## How to Find Information

### Use the Manifest First

The file `docs/KNOWLEDGE_BASE_MANIFEST.json` contains:
- `guides` - Links to all how-to documentation
- `reference` - Links to all technical documentation
- `quick_answers` - Quick lookup for common questions
- `search_index` - By topic (local, merge, models, advanced, architecture)
- `advisor_prompts` - Guide for advisor recommendations

**Example usage:**
```json
// In manifest:
"merge_methods_overview": {
  "guide": "docs/guides/FUSIONBENCH_QUICKSTART.md",
  "reference": "docs/reference/MERGING_METHODS_INVENTORY.md"
}

// When user asks "what merge methods are available?"
→ Read: docs/guides/FUSIONBENCH_QUICKSTART.md (for overview)
→ Reference: docs/reference/MERGING_METHODS_INVENTORY.md (for details)
```

---

## Core Knowledge Areas

### 1. Local Models (User's Question: "How do I use my own model?")

**Quick Answer Files:**
- `docs/guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md` - 3-minute read
- `docs/guides/LOCAL_MODEL_UPLOAD_GUIDE.md` - Comprehensive guide

**Key Points to Remember:**
- Users upload via Streamlit UI → Evolution tab → Base Models → "📤 Upload Local Model"
- Models copied to `breeding_vat/data/model_zoo/` (originals preserved)
- Can be mixed with HuggingFace models in same experiment
- Metadata stored in `.model_metadata.json`

**Common Advisor Recommendation:**
```
User: "I have a finetuned Qwen model I want to evolve"
Advisor should:
1. Guide to LOCAL_MODEL_UPLOAD_QUICKSTART.md
2. Explain upload process
3. Suggest pairing with complementary base model
4. Recommend merge methods that work well with local models
```

### 2. Merge Methods (User's Question: "What methods should I use?")

**Reference Files:**
- `docs/guides/FUSIONBENCH_QUICKSTART.md` - Overview of all 20+
- `docs/reference/MERGING_METHODS_INVENTORY.md` - Full technical details

**Quick Reference:**
- **SLERP** - Best for similar models, smooth interpolation
- **TIES** - Trim and select high-performing weights
- **DARE** - Sparse, good for diverse model pairs
- **Task Arithmetic** - Vector math on task deltas
- **RegMean** - Regression-based optimization
- **Frankenmerge** - Layer-wise selection (advanced)
- **Git Rebasin** - Geometric mean in task space
- **Voting** - Majority vote on weights

**Common Advisor Recommendation:**
```
User: "I want to merge Qwen-0.5B with my custom model"
Advisor should:
1. Check similarity (similar size → SLERP, diverse → DARE)
2. Suggest 3-5 methods to try
3. Recommend parameters (alpha, drop_rate, etc.)
4. Suggest evaluation metrics
→ Reference: MERGING_METHODS_INVENTORY.md for parameters
```

### 3. Available Models (User's Question: "What base models can I use?")

**Reference File:**
- `docs/reference/SPECIALIZED_MODELS.md` - Complete list

**Categories:**
- Reasoning models (Qwen, Llama 3.1, etc.)
- Code models (DeepSeek, etc.)
- Math models (specialized variants)
- General instruction-following
- Local/custom models (via upload)

**Common Advisor Recommendation:**
```
User: "I need a good base for reasoning"
Advisor should:
1. Check SPECIALIZED_MODELS.md
2. Suggest models known for reasoning
3. Recommend size constraints (3B, 7B, etc.)
4. Pair with complementary second model
```

### 4. System Architecture (User's Question: "How does this work?")

**Reference File:**
- `docs/reference/Architecture.md` - Complete architecture

**Key Components:**
1. **Streamlit UI** - User interface (`breeding_vat/ui/app.py`)
2. **Experiment Manager** - Lifecycle management
3. **Evolution Engine** - Merge → Eval → Cull loop
4. **Advanced Merger** - Routes to FusionBench/MergeKit
5. **Task Runner** - Docker orchestration
6. **SAE Analyzer** - Layer introspection

**Data Flow:**
```
User Input (Streamlit)
  ↓
Experiment Manager (creates dated folder)
  ↓
Evolution Engine (runs cycles)
  ├─ Merge (via FusionBench/MergeKit)
  ├─ Evaluate (via lm-eval harness)
  ├─ SAE Analyze (optional)
  └─ Cull (remove bottom performers)
  ↓
Results (merged_models/ with lineage tracking)
```

### 5. Advanced Topics

#### SAE Layer Analysis
**Files:**
- `docs/reference/SAE_GUIDE.md` - What SAE does
- `docs/reference/SAE_MEMORY_OPTIMIZATION.md` - Memory optimization

**Use Case:** Understand feature drift during merging

#### Mixture of Experts (MoE)
**File:**
- `docs/guides/MOE_GUIDE.md` - Building MoE models

**Use Case:** Advanced: layer-wise expert selection via Frankenmerge

---

## Advisor Decision Tree

When a user asks a question, follow this logic:

```
User Question
  ↓
Check manifest "quick_answers" section
  ↓
Is it a "how to" question?
  → Yes: Read the "guide" file
  → No: Continue
  ↓
Is it a technical question?
  → Yes: Read the "reference" file
  → No: Continue
  ↓
Is it a recommendation question?
  → Yes: Read all relevant files, synthesize recommendation
  → No: Continue
  ↓
Is it about system design?
  → Yes: Read Architecture.md
  → No: Re-read manifest, check search_index
```

---

## Common Questions & Where to Find Answers

| User Question | Search Manifest For | Read These Files |
|---|---|---|
| "How do I upload my model?" | `how_to_upload_model` | LOCAL_MODEL_UPLOAD_QUICKSTART.md |
| "What merge methods exist?" | `merge_methods_overview` | FUSIONBENCH_QUICKSTART.md + MERGING_METHODS_INVENTORY.md |
| "What base models are available?" | `available_models` | SPECIALIZED_MODELS.md |
| "How does the system work?" | `system_architecture` | Architecture.md |
| "How do I use local models?" | `how_to_upload_model` | LOCAL_MODEL_UPLOAD_GUIDE.md |
| "Which merge method should I use?" | `merge_methods_overview` | FUSIONBENCH_QUICKSTART.md |
| "Can I mix local and HF models?" | `local_models` or `merge_methods_overview` | LOCAL_MODEL_UPLOAD_GUIDE.md |
| "How is memory optimized?" | `sae_analysis` | SAE_MEMORY_OPTIMIZATION.md |
| "What are MoE models?" | `advanced_moe` | MOE_GUIDE.md |

---

## Metadata Files for Programmatic Access

### KNOWLEDGE_BASE_MANIFEST.json

```json
{
  "guides": { ... },        // All how-to docs
  "reference": { ... },     // All technical docs
  "quick_answers": { ... }, // Common questions → file mapping
  "search_index": { ... },  // By topic (local, merge, models, etc)
  "advisor_prompts": { ... } // Guide for recommendations
}
```

**How to use it:**
```python
import json

with open('docs/KNOWLEDGE_BASE_MANIFEST.json', 'r') as f:
    manifest = json.load(f)

# Find files about local models
local_files = manifest['search_index']['local']
# → ['docs/guides/LOCAL_MODEL_UPLOAD_QUICKSTART.md', ...]

# Get quick answer for common question
answer = manifest['quick_answers']['merge_methods_overview']
# → {'guide': '...', 'reference': '...'}
```

---

## Best Practices for the Advisor

1. **Always cite the file** - "According to LOCAL_MODEL_UPLOAD_GUIDE.md..."
2. **Provide specific examples** - Reference actual method names from MERGING_METHODS_INVENTORY.md
3. **Match user's technical level** - Start with guide files, escalate to reference if needed
4. **Cross-reference when relevant** - "See also: Architecture.md for system flow"
5. **Provide actionable steps** - Don't just describe, guide the user through the process

---

## File Locations (Quick Reference)

```
docs/
├── guides/
│   ├── LOCAL_MODEL_UPLOAD_QUICKSTART.md    ← Start here for local models
│   ├── LOCAL_MODEL_UPLOAD_GUIDE.md         ← Complete local model guide
│   ├── FUSIONBENCH_QUICKSTART.md           ← Merge methods overview
│   └── MOE_GUIDE.md                        ← Advanced MoE
├── reference/
│   ├── Architecture.md                     ← System design
│   ├── MERGING_METHODS_INVENTORY.md        ← All 20+ methods with params
│   ├── SPECIALIZED_MODELS.md               ← Available base models
│   ├── MODEL_ZOO.md                        ← Storage & preservation
│   ├── SAE_GUIDE.md                        ← Layer introspection
│   └── SAE_MEMORY_OPTIMIZATION.md          ← Memory efficiency
├── KNOWLEDGE_BASE_MANIFEST.json            ← Machine-readable index
└── ADVISOR_KNOWLEDGE_BASE.md               ← This file
```

---

**Last Updated**: January 15, 2025  
**For**: 0.8B Advisor Model (Qwen/Qwen2.5-0.8B-Instruct)  
**Status**: Ready for integration
