# Breeding Vat: Codebase Knowledge Map (Handover)

This document provides a manageable, indexable directory of the Breeding Vat system for local agents.

## 1. Core Logic & Merging
- `breeding_vat/modules/merge/evolution.py`: The **EvolutionEngine**. Implements the waterfall merging strategy.
- `breeding_vat/modules/merge/merger.py`: The **AdvancedMerger**. Dispatches to MergeKit or FusionBench.
- `breeding_vat/modules/merge/mergekit_engine.py`: Generates MergeKit YAML and triggers the worker container.
- `breeding_vat/modules/merge/fusionbench_engine.py`: Integration for 15+ advanced merging methods via FusionBench.
- `breeding_vat/modules/merge/advanced_toggles.py`: 11 orthogonal toggles (nuSLERP, Top-K, etc.) that can be layered onto any merge.

## 2. Infrastructure & Orchestration
- `breeding_vat/orchestrator/runner.py`: The **TaskRunner**. Handles Docker-out-of-Docker sibling container launches and `SIMULATION_MODE`.
- `scripts/manager.py`: The "Maintenance Spine". Handles setup, repairs, and UI launching.
- `docker/`: Contains all environment definitions (UI, Merge, Eval, SAE, FusionBench, Finetune).

## 3. Data & Persistence
- `breeding_vat/data/breeding.db`: SQLite database for experiments, models, and genealogy.
- `breeding_vat/data/schema.sql`: Authoritative schema for the DB.
- `breeding_vat/modules/experiment_manager.py`: Handles filesystem metadata and DB records for Missions.
- `breeding_vat/modules/model_transfer.py`: Manages the Model Zoo (HuggingFace downloads and local model symlinking).

## 4. Evaluation & Analysis
- `breeding_vat/modules/benchmark/evaluator.py`: Tiered evaluation logic (Perplexity -> lm-eval).
- `breeding_vat/modules/benchmark/receipt_writer.py`: Generates immutable JSON "receipts" for models.
- `breeding_vat/modules/assay/analyzer.py`: The **ASSAY** triangulated diagnosis system.
- `breeding_vat/modules/sae/scoped_analyzer.py`: Sparse Autoencoder analysis for layer introspection.

## 5. User Interface
- `breeding_vat/ui/app.py`: The Streamlit Control Room.
- `breeding_vat/modules/recipe_executor.py`: Translates UI configurations into executable Engine configs.

## 6. Simulation & Debugging
- Enable simulation by setting `SIMULATION_MODE=true`.
- Emulated responses are logged to the console and create dummy files in `breeding_vat/data/`.
- Reference `docs/developer_handover/EMULATION_GUIDE.md` for details.
