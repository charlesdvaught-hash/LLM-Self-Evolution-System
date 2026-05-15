# Breeding Vat — Source of Truth (ULTIMATE HANDOFF VERSION)

**Purpose:** The authoritative reference for the Breeding Vat "Spine". This document states what actually runs, how it connects, and how to safely develop/debug the system.

---

## 1. Canonical operator entrypoints (Windows)

| Action | Command | Notes |
|--------|---------|--------|
| First-time / repair env | `setup.bat` | Calls `python scripts/manager.py setup`. Builds **6** images, downloads base models. |
| Daily launch | `run.bat` | Calls `python scripts/manager.py run`. Starts Streamlit UI. |
| Status only | `status.bat` | Docker + images + containers check. |

---

## 2. Infrastructure spine (`scripts/manager.py`)

- **REQUIRED_IMAGES:** `breeding-vat-ui`, `breeding-vat-merge`, `breeding-vat-eval`, `breeding-vat-sae`, `breeding-vat-fusionbench`, **`breeding-vat-finetune`**.
- **Simulation Mode:** If `SIMULATION_MODE=true` is set in the environment:
  - Docker builds are bypassed.
  - Streamlit UI is launched locally (non-containerized) using the local Python environment.
  - Useful for debugging logic and UI on machines without GPUs/Docker.

---

## 3. Application spine — Streamlit (primary product)

| Item | Path |
|------|------|
| UI module | `breeding_vat/ui/app.py` |
| Container CMD | `streamlit run /app/breeding_vat/ui/app.py` |

### 3.1 Core Components (Initialized in `app.py`)
- **TaskRunner**: `breeding_vat/orchestrator/runner.py`. The "DooD" orchestrator.
- **ExperimentManager**: `breeding_vat/modules/experiment_manager.py`. Persistence & metadata.
- **AdvancedMerger**: `breeding_vat/modules/merge/merger.py`. The merge dispatcher.
- **ModelTransfer**: `breeding_vat/modules/model_transfer.py`. **Supports Symlinking** to host models.

---

## 4. Simulation & Debugging (CRITICAL FOR HANDOVER)

The system includes a robust **Simulation Mode** for environments without high-end hardware.

### 4.1 Enabling Simulation
```bash
export SIMULATION_MODE=true
```

### 4.2 Behavior in Simulation
- **TaskRunner**: Intercepts `run_docker_task`.
- **Merge Emulation**: Automatically creates a directory in `breeding_vat/data/merged_models/` with mock `config.json` and dummy weights.
- **Eval Emulation**: Generates a mock `results_*.json` in `breeding_vat/data/eval_results/` with randomized success scores.
- **Genealogy**: Full SQLite tracking works normally, allowing verification of the "Waterfall" logic.

---

## 5. Model Management

- **Location:** `breeding_vat/data/model_zoo/`.
- **Symlinking (NEW):** To avoid duplicating large models, use `ModelTransfer.register_local_model(..., use_symlink=True)`. This links your local drive to the "Lab" without using extra disk space.
- **Specimen Models:** Files do **not** have to be inside the container image; they are mounted via volumes by the `TaskRunner` at runtime.

---

## 6. Known Off-Spine or Legacy

| Artifact | Status | Note |
|----------|--------|------|
| `docker/task-runner.py.legacy` | **LEGACY** | Do not use. Replaced by `breeding_vat/orchestrator/runner.py`. |
| `docker/Dockerfile.mergekit` | **DEPRECATED** | Use `Dockerfile.merge` instead. |
| `scripts/finetune_runner.py` | **STUB** | Current version is a stub for the `vat-finetune` entrypoint. |

---

## 7. Developer Tools

- **System State Analyzer**: `python scripts/state_analyzer/analyzer.py`. Generates `system_state.json`. Use this to verify internal wiring and catch broken imports.
- **Advanced Toggle Verification**: `python scripts/verify_advanced_toggles.py`. Validates the math/YAML logic for the 11 orthogonal merge toggles (nuSLERP, Top-K, etc.).
- **Smoke Test**: `python scripts/smoke_test_evolution.py`. Runs a 2-cycle simulated evolution mission to verify the end-to-end pipeline.

---

## 8. Summary for Local Agents

1.  **Imports**: Always check `__init__.py` files in `modules/benchmark` and `modules/assay` if adding new analytical tools to the UI.
2.  **Runner**: The `TaskRunner` is the single point of failure for Docker orchestration. It uses `HOST_PWD` to resolve host paths for volume mounts.
3.  **MergeKit**: If `mergekit-yaml` fails locally due to Pydantic errors, use the monkeypatch found in `test_merge/patch_mergekit.py`.

---

**Last Updated:** 2025-05-15 by Jules (Simulation Mode Safeguards & UI Warning)
