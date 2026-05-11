# The Breeding Vat: LLM Evolution Engine

**The Breeding Vat** is an autonomous laboratory for evolving high-performance, small-scale language models through intelligent merging, evaluation, and selection. Stop training from scratch—use this system to breed specialized "Franken-models" on consumer hardware.

## Quick Start

```bash
# Setup (one-time)
setup.bat

# Run
run.bat
# Open http://localhost:8501
```

## Core Loop

1. **Merge**: Combine models using 20+ mathematical strategies (FusionBench + MergeKit)
2. **Evaluate**: Benchmark offspring via LM Evaluation Harness
3. **Introspect**: Analyze layers with Sparse Autoencoders (SAE)
4. **Cull**: Keep winners, discard poor performers
5. **Repeat**: Evolved models become parents for next cycle

## New Feature: Local Model Upload

Users can now upload local models directly via the Streamlit UI:

1. **Evolution tab** → **Base Models** → **📤 Upload Local Model**
2. Validate model path (must contain `config.json`)
3. Transfer to model zoo (`breeding_vat/data/model_zoo/`)
4. Use in experiments alongside HuggingFace models
5. **Originals preserved** for comparison

**Documentation**: See `docs/LOCAL_MODEL_UPLOAD_GUIDE.md` and `docs/LOCAL_MODEL_UPLOAD_QUICKSTART.md`

## Documentation

All documentation has been consolidated in the `docs/` folder:

| Document | Purpose |
|----------|---------|
| `docs/Architecture.md` | Complete system architecture & design |
| `docs/LOCAL_MODEL_UPLOAD_GUIDE.md` | Local model integration details |
| `docs/LOCAL_MODEL_UPLOAD_QUICKSTART.md` | User guide for uploading models |
| `docs/guides/` | How-to guides and tutorials |
| `docs/reference/` | Technical reference materials |

## Directory Structure

```
breeding_vat/                    # Core application
├── ui/app.py                   # Streamlit dashboard
├── modules/
│   ├── merge/                  # Merging engines (FusionBench, MergeKit)
│   ├── model_transfer.py       # Local model registration
│   ├── model_path_resolver.py  # Model ID to path resolution
│   └── ...
├── orchestrator/               # Docker task management
└── data/
    ├── model_zoo/              # Transferred local models
    ├── experiments/            # Mission results & lineage
    └── merged_models/          # Evolved model weights

docker/                          # Container definitions
├── Dockerfile.ui               # Streamlit UI container
├── Dockerfile.merge            # Merge engine container
├── Dockerfile.eval             # Evaluation container
└── Dockerfile.sae              # SAE analysis container

docs/                           # Documentation
├── Architecture.md             # System design
├── LOCAL_MODEL_UPLOAD_*        # Local model features
├── guides/                     # How-to guides
└── reference/                  # Technical details

scripts/                         # Utilities
├── manager.py                  # Container orchestration
└── download_models.py          # Model fetching
```

## Tech Stack

- **Merging**: [FusionBench](https://github.com/j-fu/FusionBench) (20+ methods) + MergeKit
- **Evaluation**: [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- **Introspection**: Sparse Autoencoders (SAE)
- **Infrastructure**: Docker, Streamlit, SQLite
- **Base Models**: Qwen, Mistral, Llama, and custom local models

## Key Features

✅ **20+ Merge Methods**: SLERP, TIES, DARE, Task Arithmetic, RegMean, Git Rebasin, Frankenmerge, and more  
✅ **Automated Evaluation**: Benchmark on HellaSwag, ARC, Winogrande, and custom tasks  
✅ **Local Model Support**: Upload your own finetuned models for evolution  
✅ **Full Lineage Tracking**: SQLite genealogy database tracks all ancestors and scores  
✅ **Resumable Experiments**: Pause and resume evolution runs across sessions  
✅ **SAE Introspection**: Analyze layer specialization and feature drift  
✅ **Docker Isolation**: No dependency hell—all tools run in containers  

## Architecture

See `docs/Architecture.md` for:
- Complete system design and component relationships
- Data flow and execution pipelines
- Database schema for lineage tracking
- Extension points for custom methods and benchmarks

## Model Preservation Strategy

| Model Type | Location | Purpose |
|-----------|----------|---------|
| **Local (Uploaded)** | `breeding_vat/data/model_zoo/` | Original never modified |
| **HuggingFace** | `~/.cache/huggingface/` | Auto-cached, never modified |
| **Merged (Evolved)** | `breeding_vat/data/experiments/{exp_id}/merged_models/` | Evolution-scoped outputs |

Originals remain pristine for comparison; merged models are experiment-specific.

## Examples

### Basic Evolution

```
1. Sidebar → New Mission
   - Goal: "Reasoning at 3B scale"
   
2. Evolution tab → Base Models
   - Select: Qwen-0.5B, Mistral-7B
   
3. Choose methods: SLERP, TIES, Task Arithmetic
4. Cycles: 5
5. Click: "▶️ START EVOLUTION"
```

### Using Local Models

```
1. Evolution tab → Base Models → "📤 Upload Local Model"
   - Path: /path/to/my-finetuned/
   - Name: my-qwen-finetuned
   
2. After transfer, available in model selection
3. Mix with HF models: [my-qwen-finetuned, Qwen-0.5B]
4. Run evolution → merged_models contain both parents
```

## Contributing & Extension

To add a new merge method:

1. Implement in `breeding_vat/modules/merge/fusionbench_engine.py`
2. Add to `AVAILABLE_METHODS` dict
3. Register parameters in sidebar UI
4. Appears automatically in evolution

See `docs/Architecture.md` (Part 8) for extension points.

## Requirements

- Docker Desktop (or Docker Engine on Linux)
- Python 3.10+
- 8GB+ VRAM for model merging
- 12GB+ recommended for SAE analysis

## Cleanup & Maintenance

Old documentation files have been removed. The following have been deleted:
- ADVISOR_*, COMPLETE.md, DOCUMENTATION_*, FINAL_*, GIT_READY.md, RESIDUALS_*, SAFE_TO_DELETE_*

All current documentation is in `docs/`.

---

**Status**: Production-ready with local model upload feature  
**Last Updated**: January 15, 2025  

For questions, see documentation in `docs/` or check the inline code comments.

🧬 *Stop computing. Start evolving.*
