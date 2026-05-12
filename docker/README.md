# The Breeding Vat - Docker Setup

## Architecture

The Breeding Vat uses a **lightweight orchestrator pattern**:

- **UI Container** (resident): `breeding-vat-ui` runs Streamlit + orchestrator logic
- **Task Containers** (ephemeral): Spawned on-demand by the orchestrator for:
  - **Merge**: MergeKit execution (Phase 2)
  - **Eval**: Benchmark scoring via lm-eval (Phase 4)
  - **SAE**: Layer feature analysis (Phase 1)
  - **Train**: LoRA/PEFT fine-tuning (Phase 4)

The UI container has access to `/var/run/docker.sock` to spawn and manage ephemeral task containers.

## Quick Start

### Build Images

```bash
# Build all Docker images
bash docker/build.sh
```

Or use docker-compose:
```bash
docker compose -f docker/docker-compose.yml build
```

### Start UI

```bash
# Start the Streamlit UI
bash docker/dev.sh up

# Or manually:
docker compose -f docker/docker-compose.yml up -d breeding-vat-ui
```

Access at: **http://localhost:8501**

### Optional: Development Environment

```bash
# Start with Jupyter notebook
bash docker/dev.sh up-dev

# Access at: http://localhost:8888
```

## Docker Images

| Image | Purpose | Base | Size |
|-------|---------|------|------|
| `breeding-vat-ui` | Streamlit UI + Orchestrator | python:3.10-slim | ~2GB |
| `breeding-vat-merge` | MergeKit execution | python:3.10-slim | ~1.5GB |
| `breeding-vat-eval` | lm-eval benchmarking | python:3.10-slim | ~1.5GB |
| `breeding-vat-sae` | SAE analysis | python:3.10-slim | ~1GB |

## Orchestrator Design

When you trigger a task in the UI:

1. **UI** (`breeding_vat/ui/app.py`) captures parameters
2. **Orchestrator** (`breeding_vat/orchestrator/runner.py`) creates config file
3. **Spawn Container**: Uses Docker API to create ephemeral container with task config
4. **Task Runs**: Container mounts `breeding_vat/data/` for R/W access
5. **Results Saved**: SQLite DB + model weights in `breeding_vat/data/`
6. **Cleanup**: Container stops; data persists

### Volumes (Shared)

```
breeding_vat/data/
├── breeding.db          # SQLite lineage database
├── merged_models/       # Saved model weights
├── eval_results/        # Benchmark scores
└── configs/             # Generated YAML merge recipes
```

## Environment Variables

Create `.env` (optional, defaults work):

```bash
# Task execution
TASK_TIMEOUT_SECONDS=3600
MAX_CONCURRENT_TASKS=2

# Evaluation
EVAL_TASKS=arc_easy,arc_challenge,hellaswag,mmlu

# Logging
LOG_LEVEL=info
```

## Troubleshooting

### UI won't start
```bash
docker compose -f docker/docker-compose.yml logs breeding-vat-ui
```

### Can't spawn task containers
Check that `/var/run/docker.sock` is readable:
```bash
docker exec breeding-vat-ui docker ps
```

### Out of disk space
Models are large. Ensure ~200GB free space before starting.

## Development

### Rebuild images
```bash
bash docker/build.sh
```

### Enter container shell
```bash
bash docker/dev.sh shell breeding-vat-ui
```

### View logs
```bash
bash docker/dev.sh logs-ui
```

## Production Deployment

For multi-GPU or Kubernetes:

1. Use `docker build` with `--build-arg` for GPU/CUDA selection
2. Set `CUDA_VISIBLE_DEVICES` per container
3. Mount model cache volumes across nodes (NFS/S3)
4. Use orchestrator's task queue for distributed scheduling

See `DOCKER_MANAGEMENT.md` for advanced configurations.
