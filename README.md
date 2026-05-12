# The Breeding Vat: LLM Evolution Engine

**The Breeding Vat** is an autonomous laboratory for evolving high-performance, small-scale language models through intelligent merging, evaluation, and selection. Stop training from scratch—use this system to breed specialized "Franken-models" on consumer hardware.

## Quick Start

```bash
# Setup (one-time) - builds Docker images
setup.bat

# Run - launches UI in Docker container
run.bat
# Opens http://localhost:8501 automatically
```

**That's it!** The app now supports both granular expert control AND hands-off AI orchestration:
- **Granular Mode** 🎛️ — Pick every parameter manually, see exact model count
- **Exploratory Mode** 🚀 — Describe goal, AI asks 5 clarifying questions, generates strategy
- **Balanced Mode** ⚖️ — Smart defaults for most users

See `README_ENHANCEMENTS.md` for feature details.

## Core Loop

1. **Merge**: Combine models using 20+ mathematical strategies (FusionBench + MergeKit)
2. **Evaluate**: Benchmark offspring via LM Evaluation Harness
3. **Introspect**: Analyze layers with Sparse Autoencoders (SAE)
4. **Cull**: Keep winners, discard poor performers
5. **Repeat**: Evolved models become parents for next cycle

## Key Features

✅ **20+ Merge Methods**: All techniques available for granular selection  
✅ **Dual-Mode UI**: Granular (expert) or Exploratory (AI-orchestrated)  
✅ **Resource Transparency**: Know exactly how many models you'll generate before running  
✅ **Automated Evaluation**: Benchmark on HellaSwag, ARC, Winogrande, and custom tasks  
✅ **Local Model Support**: Upload your own finetuned models for evolution  
✅ **Full Lineage Tracking**: SQLite genealogy database tracks all ancestors and scores  
✅ **Resumable Experiments**: Pause and resume evolution runs across sessions  
✅ **SAE Introspection**: Analyze layer specialization and feature drift  
✅ **Docker Isolation**: No dependency hell—all tools run in containers  
✅ **Cleanup Tools**: Archive/delete old models to prevent storage bloat  

## What's New (v3)

The UI has been completely redesigned to support two extremes:

### Granular Mode (Expert Control)
- Pick specific merge techniques, set parameters, choose models
- See exact resource estimate: "4 techniques × 3 rounds = 12 models, 18 GB VRAM, 60 min"
- All prior features preserved (methods, specimens, parameters, benchmarks)

### Exploratory Mode (AI Orchestration)
- Describe goal: "Improve reasoning 15% on 4B model under 5GB"
- AI asks 5 clarifying questions (Quality/Speed, Intensity, SAE, Stopping, Technique count)
- AI generates strategy with resource estimates
- User approves or edits before launch

### Resource Management
- **See model count before running** — "You'll generate 12 models"
- **VRAM estimates** — "18 GB cumulative, peaks at 2.5 GB per operation"
- **Time estimates** — "60 minutes total"
- **Storage planning** — "60 GB if kept all, 16 GB if top 3 models"
- **Cleanup tools** — Archive old cycles, delete intermediates

## Directory Structure

```
breeding_vat/                    # Core application
├── ui/
│   ├── app.py                  # Main Streamlit UI (dual-mode)
│   ├── ui_v2_sleek.py          # Dark theme components
│   └── app_original_backup.py  # Previous version (reference)
├── modules/
│   ├── calibration_dual_mode.py  # NEW: Granular/Exploratory modes
│   ├── strategy_orchestrator.py  # NEW: AI strategy generation
│   ├── merge/                  # Merging engines
│   ├── model_transfer.py       # Local model management
│   └── ...
├── orchestrator/               # Docker task management
└── data/
    ├── model_zoo/              # Local models
    ├── experiments/            # Evolution results
    └── merged_models/          # Model weights

docker/                          # Container definitions
├── Dockerfile.ui               # Streamlit UI (runs app.py)
├── Dockerfile.merge            # Merge engine
├── Dockerfile.eval             # Evaluation
└── Dockerfile.sae              # SAE analysis

scripts/                         # Utilities
├── manager.py                  # Docker orchestration
└── download_models.py          # Model fetching
```

## Tech Stack

- **Merging**: [FusionBench](https://github.com/j-fu/FusionBench) (20+ methods) + MergeKit
- **Evaluation**: [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- **Introspection**: Sparse Autoencoders (SAE)
- **Infrastructure**: Docker, Streamlit, SQLite
- **Base Models**: Qwen, Mistral, Llama, and custom local models

## Usage Examples

### Example 1: Expert (Granular Mode)

```
1. Calibration tab → Click "🎛️ Granular"
2. Select techniques: linear, task_arithmetic, regmean
3. Set: 3 rounds, 50% culling, balanced benchmarks
4. See: "9 models, 13.5 GB VRAM, 45 min"
5. Evolution tab → Select base models → START
```

### Example 2: Discovery (Exploratory Mode)

```
1. Calibration tab → Click "🚀 Exploratory"
2. Goal: "Better reasoning, 4B model, under 5GB"
3. Click "Ask AI Strategy"
4. Answer 5 questions (yes/no or choose option)
5. AI shows: "15 models, 22.5 GB VRAM, 1.2 hours"
6. [✓ Approve] → Evolution starts
```

### Example 3: Quick Test (Balanced Mode)

```
1. Calibration tab → Click "⚖️ Balanced" (default)
2. Uses smart presets
3. Evolution tab → Pick 2 models + 2 methods
4. START → Done in 20 minutes
```

## Model Preservation Strategy

| Type | Location | Preserved? |
|------|----------|-----------|
| **Local (Uploaded)** | `breeding_vat/data/model_zoo/` | ✅ Original untouched |
| **HuggingFace** | `~/.cache/huggingface/` | ✅ Auto-cached |
| **Merged (Evolved)** | `breeding_vat/data/experiments/{id}/` | ✅ Experiment-scoped |

## Resource Planning

### VRAM Budget
- **8 GB**: 2 techniques × 2 rounds (tight)
- **12 GB**: 3 techniques × 3 rounds (OK)
- **24 GB**: 4-5 techniques × 3-4 rounds (comfortable)
- **48+ GB**: 6-7 techniques × 4-5 rounds (unlimited)

### Time Budget
- **Quick benchmarks**: 5 min per model
- **Balanced benchmarks**: 10 min per model
- **Thorough benchmarks**: 20 min per model

### Storage
- Per model: ~3-5 GB (weights) + 50 MB (logs)
- Keep only best: 5.5 GB per experiment
- Keep top 3: 16.5 GB per experiment
- Keep all (12 models): ~60 GB

## Cleanup After Evolution

Advanced tab has cleanup tools:
- **Archive old models** — Move cycles 1-2 to external storage
- **Delete intermediates** — Free space between runs
- **Clean logs** — Keep only best model logs

Prevents storage bloat from accumulating experiments.

## Architecture

See `docs/Architecture.md` for:
- Complete system design and component relationships
- Data flow and execution pipelines
- Database schema for lineage tracking
- Extension points for custom methods and benchmarks

## Requirements

- Docker Desktop (or Docker Engine on Linux)
- Python 3.10+
- 8GB+ VRAM for model merging
- 12GB+ recommended for SAE analysis

## Backward Compatibility

✅ All old experiments load in new app  
✅ Database schema unchanged  
✅ Merge configs compatible  
✅ Can rollback instantly (app_original_backup.py available)  

## Documentation

Quick start: See `README_ENHANCEMENTS.md`  
Feature details: See `FINAL_SUMMARY.md`  
Integration: See `INTEGRATION_GUIDE.md`  
Quick lookup: See `QUICK_START_ENHANCED.md`  
Architecture: See `docs/Architecture.md`  

---

**Status**: Production-ready with dual-mode calibration  
**Last Updated**: January 2025  
**Backward Compatible**: ✅ Yes

For questions, see documentation files or check inline code comments.

🧬 *Stop computing. Start evolving.*
