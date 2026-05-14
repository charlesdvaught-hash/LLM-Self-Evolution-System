# Quick Start Guide

## Workflow

### First Time Setup (One-Time)

```
setup.bat  →  Builds Docker images + Downloads model specimens
              (15-30 minutes)
```

This does:
- Builds 5 Docker images for merging, evaluation, SAE analysis
- Downloads model specimens from HuggingFace:
  - **Working GGUFs**: Qwen3.5-0.8B (quantized, ~600MB) for quick reasoning
  - **Safetensor Specimens**: 4 full-precision models for breeding (~12GB total)
    - Qwen2.5-1.5B (general baseline)
    - DeepSeek-R1-Distill-Qwen-1.5B (reasoning)
    - Qwen3-1.7B-Sushi-Coder (code generation)
    - LaSER-Qwen3-0.6B (KB retriever)

### Every Time You Use It

```
run.bat  →  Launches Streamlit UI at http://localhost:8501
            (Reuses container if already running)
```

## Architecture

- **Docker Images**: Built once, cached in Docker
- **Model Specimens**: Downloaded to `breeding_vat/data/model_zoo/` (~15GB)
- **Application Code**: Mounted live from your filesystem (no rebuild needed)

## Edit & Iterate

Your code is mounted live in the container:

```
breeding_vat/
├── ui/
├── modules/
└── ...
```

Changes to Python files take effect immediately—just refresh your browser. No rebuild needed.

## Disk Space Required

- Docker images: ~10GB
- Model specimens: ~15GB
- Total: ~25GB minimum

## Troubleshooting

**"Docker is not running"**
→ Start Docker Desktop

**"Setup failed"**
→ Check: Docker running, ~25GB free space, internet connection

**"Images are already built but I need to rebuild"**
→ Run `python scripts/manager.py rebuild` to force full rebuild

**"I want to download different models"**
→ Run `python scripts/download_models.py --info` to see all presets
→ Then edit `scripts/manager.py` to change which preset to use

---

**TL;DR:**
1. `setup.bat` once
2. `run.bat` whenever you need the UI
3. Edit code directly, changes are live

No syncing, no complexity—just native Docker bind mounts.
