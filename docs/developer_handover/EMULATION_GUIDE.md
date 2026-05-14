# Breeding Vat: Emulation Mechanics & Debugging Guide

This guide explains **how** the current simulation mode emulates the Breeding Vat's Docker orchestration. Use this to identify discrepancies between the emulated logic and the real containerized pipeline.

## 1. The Emulation Core (`breeding_vat/orchestrator/runner.py`)

The `TaskRunner._emulate_docker_task` method is the heart of the simulation. It intercepts any call to `run_docker_task` when `SIMULATION_MODE=true`.

### How it emulates "Merge" (MergeKit/FusionBench)
- **Detection**: Checks if the image name contains "merge" or "fusionbench".
- **Logic**: It parses the command-line arguments to find the `output_name` or `output_path`.
- **Side Effects**:
  - Creates a directory in `breeding_vat/data/merged_models/<output_name>`.
  - Writes a minimal `config.json` and a dummy `mock_weights.bin`.
- **Potential Flaw**: The emulation assumes any non-hyphenated string in the command that isn't a path is the output name. If the real CLI structure changes, this parsing may fail to create the dummy folder, causing the `EvolutionEngine` to report a "Merge Failed" error even in simulation.

### How it emulates "Evaluation" (lm-eval)
- **Detection**: Checks for "eval", "lm_eval", or "ppl" in the command strings.
- **Logic**:
  - **Perplexity**: If "ppl" is found, it looks for an argument ending in `_ppl.json` and writes a hardcoded success result (`passed: true`, `perplexity: 12.5`).
  - **LM-Eval**: It parses `--output_path` or `--model_args` to determine the model name and writes a `results_<model>.json` to `breeding_vat/data/eval_results/`.
- **Side Effects**: Generates random scores between 0.5 and 0.9 for `arc_easy`, `arc_challenge`, and `hellaswag`.
- **Potential Flaw**: Real `lm-eval` results contain much more complex nested structures. If the `BenchmarkEvaluator` logic is updated to require more granular metrics (like `stderr` or specific task sub-metrics), the simulation must be updated to include those keys in the mock JSON.

## 2. Infrastructure Bypass (`scripts/manager.py`)

The `manager.py` script bypasses Docker existence checks when in simulation mode.

- **Check**: `image_exists()` returns `True` always.
- **Run**: `run_ui()` executes `streamlit run` directly in the local process instead of starting a container.
- **Potential Flaw**: This hides dependencies missing from the *host* environment that are present in the *Dockerfile*. If the app runs in simulation but fails in production, check `requirements.txt` vs the `Dockerfile.*` contents.

## 3. MergeKit Pydantic Patch (`test_merge/patch_mergekit.py`)

A known issue exists where MergeKit's Pydantic models with `ForwardRef` fail in some Python 3.10+ environments.
- **The Patch**: It manually triggers `model_rebuild()` on `ConfiguredModuleArchitecture` and `ConfiguredModelArchitecture` with an explicit `torch` namespace before calling the MergeKit CLI.
- **Debug Note**: If the real `vat-merge` container fails with a `PydanticUserError`, this patch (or its logic) must be integrated into the container's entrypoint or MergeKit itself.

## 4. Model Zoo Linking (`breeding_vat/modules/model_transfer.py`)

Local models are linked via `os.symlink` when `use_symlink=True`.
- **Emulation Logic**: Metadata is stored in a sidecar file `. <name>_metadata.json` in the zoo directory.
- **Potential Flaw**: Docker containers might not follow host symlinks unless the target path is also mounted as a volume. The `TaskRunner` logic converts `rel_path` to `abs_host_path`, but if a symlink points *outside* the project root, the worker container will see a broken link.
