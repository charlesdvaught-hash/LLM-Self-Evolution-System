# The Breeding Vat: System Architecture

## Overview
The Breeding Vat is an autonomous ecosystem for evolving Large Language Models (LLMs) on consumer hardware. It moves away from static "one-off" merges toward a continuous, lineage-tracked evolution pipeline.

## Core Components

### 1. The Orchestrator (`breeding_vat/orchestrator/`)
- **Task Runner**: Manages the lifecycle of Docker containers. Each task (merge, train, eval) runs in a fresh container with dedicated dependencies.
- **Database (SQLite)**: Tracks every model ever created, its recipe, parentage (lineage), and benchmark results.

### 2. The Advisor (`breeding_vat/modules/merge/advisor.py`)
- Uses **Qwen 3.5 0.8B** to act as a bridge between user goals and technical recipes.
- Analyzes benchmark failures to suggest mutations.

### 3. Evolution Engine (`breeding_vat/modules/merge/evolution.py`)
- Implements the **Waterfall Pipeline**:
    - **Branching**: Creating multiple mutants from high-performing parents.
    - **Mutation**: Applying stochastic changes to merge coefficients or layer selections.
    - **Culling**: Pruning the population based on fitness (benchmarks).

### 4. Specialized Modules
- **Merging**: Wraps MergeKit and implements RMM/Core-Space alignment.
- **Evaluation**: Interfaces with lm-eval-harness for automated fitness scoring.
- **SAE Analysis**: Uses Sparse Autoencoders to find specific "capability genes" in model layers.

## Data Flow
1. **User Input**: Defines goal and levers in the Streamlit UI.
2. **Advisor**: Proposes an initial recipe DAG.
3. **Orchestrator**:
    - Spawns Merge Container -> Saves Weights.
    - Spawns Eval Container -> Updates DB with Scores.
    - Spawns SAE Container -> Identifies Layer Features.
4. **Evolution Engine**: Compares scores, culls losers, and loops for the next cycle.
