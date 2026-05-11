# The Breeding Vat: Startup & Directory Structure

## What Gets Created

When you run `setup.bat` and `run.bat`, the system creates this structure:

```
LLM-Self-Evolution-System-breeding-vat-init-{id}/
├── breeding_vat/
│   ├── data/                          # ← DATA DIRECTORY (auto-created)
│   │   ├── breeding.db                # SQLite database (created on first run)
│   │   ├── merged_models/             # ← MODEL ZOO (merged models go here)
│   │   │   ├── mutant_c0_p0_o0/       # Automatically created during evolution
│   │   │   ├── mutant_c0_p0_o1/
│   │   │   └── ...
│   │   └── eval_results/              # Evaluation scores (JSON files)
│   │       ├── mutant_c0_p0_o0.json
│   │       └── ...
│   ├── configs/                       # Merge recipes (YAML configs)
│   │   ├── merge_slerp.yaml
│   │   ├── merge_ties.yaml
│   │   └── ...
│   ├── modules/                       # Python implementation
│   ├── orchestrator/                  # Docker task runner
│   ├── ui/                            # Streamlit UI
│   └── __init__.py
├── docker/                            # Container definitions
│   ├── Dockerfile.ui
│   ├── Dockerfile.merge
│   ├── Dockerfile.eval
│   └── Dockerfile.sae
├── scripts/
│   ├── manager.py                     # Orchestrator (called by .bat files)
│   ├── download_models.py             # ← MODEL DOWNLOADER (auto-called)
│   └── ...
├── setup.bat                          # Builds Docker images
├── run.bat                            # Starts UI + downloads models
└── requirements.txt                   # Python dependencies
```

## The Model Zoo: Where Models Live

### Base Models (Downloaded on First Run)
**Location**: `~/.cache/huggingface/hub/` (HuggingFace default cache)

**What gets downloaded** (`scripts/download_models.py` auto-downloads):
```
Qwen/Qwen2.5-0.5B-Instruct
Qwen/Qwen2.5-1.5B-Instruct
gpt2
```

These are the **source models** you specify in the UI sidebar under "Base Models (comma separated)".

### Merged Models (Evolution Output)
**Location**: `breeding_vat/data/merged_models/`

**What appears here**:
- `mutant_c0_p0_o0/` - Cycle 0, Parent 0, Offspring 0
- `mutant_c0_p0_o1/` - Cycle 0, Parent 0, Offspring 1
- `mutant_c1_p2_o1/` - Cycle 1, Parent 2, Offspring 1
- etc.

Each is a complete HuggingFace model directory (tokenizer + weights).

### Evaluation Results
**Location**: `breeding_vat/data/eval_results/`

**What's stored**:
- `mutant_c0_p0_o0.json` - lm-eval results (hellaswag, arc_challenge scores)
- `mutant_c0_p0_o1.json`
- etc.

### Lineage Database
**Location**: `breeding_vat/data/breeding.db`

**Contains**:
- `models` table: name, base_models, recipe, parent_id, status, benchmark_results
- `recipes` table: merge method, config
- `sae_discoveries` table: layer analysis

## First Run Sequence

### 1. `setup.bat` (One-time)
```
✓ Check Docker installed
✓ Build vat-ui image
✓ Build vat-merge image
✓ Build vat-eval image
✓ Build vat-sae image
```

### 2. `run.bat` (Every session)
```
✓ Check Docker running
✓ manager.py verify          (ensure images exist)
✓ manager.py run             (launch UI)
  └─ ensure_directories()    (creates breeding_vat/data/*, etc.)
  └─ download_models()       (calls scripts/download_models.py)
     └─ Downloads to ~/.cache/huggingface/hub/
  └─ Launch Streamlit UI at http://localhost:8501
```

## Storage Requirements

### Minimum Space
- **Images**: ~5 GB (Python, CUDA runtime, libraries)
- **Base models (3)**: ~4 GB total
- **Per merged model**: 1-12 GB (depends on size)

### Recommended
- **Total**: 50-100 GB (for multiple evolution cycles)

## First Evolution Run

1. Open http://localhost:8501
2. In sidebar:
   - Base Models: `Qwen/Qwen2.5-0.5B, Qwen/Qwen2.5-1.5B` (default)
   - Evolution Cycles: 3
   - Merging Methods: SLERP, TIES
3. Click "RUN EVOLUTION"

**What happens**:
```
Cycle 1:
  - Merge base model 1 with random base model (SLERP)
  - Merge base model 1 with random base model (TIES)
  - Merge base model 2 with random base model (SLERP)
  - Merge base model 2 with random base model (TIES)
  - Evaluate all 4 mutants → hellaswag + arc_challenge scores
  - Cull bottom 50% (keep 2 best)

Cycle 2:
  - Merge best from Cycle 1 with random models
  - Evaluate
  - Cull

Cycle 3:
  - Repeat
  - Return best overall
```

**Output**:
- New models in `breeding_vat/data/merged_models/mutant_c*`
- Eval results in `breeding_vat/data/eval_results/`
- Lineage tracked in `breeding_vat/data/breeding.db`
- Browse in "Lineage Browser" tab

## Troubleshooting

### Models not downloading
```powershell
python scripts/download_models.py
```

### Models not found in UI
Check HuggingFace model IDs exist:
```
https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
```

### merged_models directory missing
Created automatically on first evolution run. If not:
```powershell
mkdir breeding_vat\data\merged_models
mkdir breeding_vat\data\eval_results
mkdir breeding_vat\configs
```

### Database corrupted
Delete and re-create:
```powershell
rm breeding_vat\data\breeding.db
```
(Next run will recreate via schema.sql)
