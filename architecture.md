# The Breeding Vat: Complete Architecture

**Version 2.0** - Verified January 15, 2025

This document describes the complete architecture of The Breeding Vat system. It covers:
- System design and component relationships
- Execution flow with variable pipelines
- Dependencies and module interactions
- Building from scratch
- Docker containerization strategy

---

## Part 1: System Overview

### What The Breeding Vat Does

The Breeding Vat is an **autonomous LLM evolution engine** that:

1. **Accepts user goals** ("Better reasoning at 3B scale")
2. **Automatically evolves models** via merge → evaluate → cull cycles
3. **Explores 20+ merging methods** (MergeKit + FusionBench)
4. **Tracks lineage** (genealogy of all models)
5. **Provides real-time UI** feedback (Streamlit)
6. **Saves experiments** with full logging and reproducibility

### Core Principles

- **Container-based**: All tools isolated (no dependency hell)
- **Docker-first**: Every operation runs in a container
- **Experiment-centric**: Each run is a self-contained, resumable experiment
- **Transparent**: Full logging, model genealogy, benchmark tracking
- **User-friendly**: High-level UI hides complexity

---

## Part 2: Component Architecture

### High-Level Data Flow

```
User Input (Streamlit UI)
    ↓
Experiment Manager
    ├─ Create dated experiment folder
    ├─ Save metadata (goal, models, methods)
    └─ Initialize master log
    ↓
Evolution Engine Loop (repeat N cycles)
    ├─ Select random merge method
    ├─ Merge models via Docker container
    ├─ Evaluate merged model via Docker container
    ├─ Log results to experiment
    └─ Cull poor performers
    ↓
Results
    ├─ Best model saved
    ├─ Full lineage in database
    └─ Benchmarks in results/
```

### Component Breakdown

#### 1. **Streamlit UI** (`breeding_vat/ui/app.py`)

**Purpose**: User interaction, parameter selection, real-time progress

**Key Responsibilities**:
- Display experiment creation form
- Show available merge methods (20+ from AdvancedMerger)
- Handle method parameter controls (DARE drop rate, TIES threshold, etc)
- Display real-time progress bars and logs
- Show model lineage genealogy
- Stream SAE analysis results

**Connections**:
- Reads from: ExperimentManager, EvolutionWithLogging
- Writes to: UI state (in-memory)
- Calls: AdvancedMerger.get_available_methods()

**Methods Called**:
```python
# Get available merge methods (20+)
methods = merger.get_available_methods()

# Run evolution with user-selected methods
best_model = evo_logged.run_waterfall(
    base_models=[...],
    goal="...",
    num_cycles=5,
    culling_rate=50,
    allowed_methods=[...],
    resume_from_cycle=0
)
```

#### 2. **Experiment Manager** (`breeding_vat/modules/experiment_manager.py`)

**Purpose**: Lifecycle management of experiments

**Key Responsibilities**:
- Create dated experiment folders (YYYY-MM-DD_HHMMSS)
- Save/load experiment metadata (JSON)
- Initialize master log file
- Track cycle results
- Persist model genealogy

**Connections**:
- Manages: `breeding_vat/data/experiments/{timestamp}/`
- Writes to: experiment.json, master.log, benchmarks.json

**Key Methods**:
```python
# Create new experiment
exp = manager.create_experiment(
    goal="Reasoning at 3B",
    base_models=["Qwen-0.5B", "Mistral-7B"],
    merge_methods=["slerp", "ties"],
    num_cycles=5
)
# Returns: {"name": "...", "goal": "...", "paths": {...}, ...}

# Resume existing experiment
exp = manager.load_experiment("reasoning_3B_2025-01-15_152347")

# Log cycle results
manager.log_cycle(exp, cycle_num=1, models=[...], best_model=m)
```

#### 3. **Evolution Engine** (`breeding_vat/modules/merge/evolution.py`)

**Purpose**: Core loop - merge, evaluate, cull

**Key Responsibilities**:
- Run multi-cycle evolution
- Randomly select merge methods
- Orchestrate merge → eval → cull
- Track population fitness
- Implement culling strategy (remove bottom X%)

**Connections**:
- Calls: AdvancedMerger (for merging)
- Calls: TaskRunner (for Docker execution)
- Reads: merged model benchmarks
- Writes: evolution state (population, fitness)

**Key Method**:
```python
# Main evolution loop
best_model = engine.run_waterfall(
    base_models=["Model A", "Model B"],
    goal="...",
    num_cycles=5,
    culling_rate=50,  # Remove bottom 50% each cycle
    allowed_methods=["slerp", "ties", "task_arithmetic"],
    resume_from_cycle=0
)
```

#### 4. **Advanced Merger** (`breeding_vat/modules/merge/merger.py`)

**Purpose**: Unified interface to all merging methods

**Key Responsibilities**:
- Route merge requests to appropriate backend (MergeKit or FusionBench)
- Manage method parameters
- Generate merge configs
- Return merged model paths

**Connections**:
- Calls: MergekitEngine (7 classical methods)
- Calls: FusionBenchEngine (13+ advanced methods)
- Returns: List of all available methods

**Key Methods**:
```python
# Get all available methods (20+)
methods_dict = merger.get_available_methods()
# Returns: {
#   "slerp": "Spherical linear interpolation",
#   "task_arithmetic": "Vector arithmetic...",
#   "regmean": "Regression-based mean",
#   ...
# }

# Merge via specific method
output = merger.slerp_merge(
    base_model="Qwen-1.5B",
    models=["Qwen-0.5B", "Mistral-7B"],
    output_path="breeding_vat/data/merged_models/mutant_1"
)

# Merge via FusionBench method
output = merger.task_arithmetic_merge(
    base_model="Qwen-1.5B",
    models=["Qwen-0.5B"],
    output_path="...",
    weights=[0.5]  # Optional parameter
)
```

#### 5. **MergeKit Engine** (`breeding_vat/modules/merge/mergekit_engine.py`)

**Purpose**: Classical weight interpolation methods

**Implemented Methods** (7):
- SLERP - Spherical linear interpolation
- TIES - Trim, Interleave, Elect Subnets
- DARE - Drop And REscale
- Task Arithmetic - Vector arithmetic
- MOE - Mixture of Experts
- RMM - Resurrection by Majority Merging
- NegMerge - Negative direction subtraction

**Connections**:
- Generates: YAML merge configs
- Calls: TaskRunner to execute in Docker container
- Container: breeding-vat-merge

#### 6. **FusionBench Engine** (`breeding_vat/modules/merge/fusionbench_engine.py`)

**Purpose**: Advanced merging techniques (regression, voting, layer-wise)

**Implemented Methods** (13+):
- Linear - Simple linear interpolation
- Task Arithmetic - Regression-optimized
- RegMean - Regression-based mean with optimization
- Voting - Majority voting on weight values
- Magnitude Prune - Sparse by magnitude threshold
- Git Rebasin - Geometric mean in task space
- DARE Linear - Drop & rescale variant
- TIES Linear - TIES with linear interpolation
- Frankenmerge - Layer-wise expert selection
- Layer Wise - Per-layer weighted merging
- Multi-Task - Multi-task optimization
- Expert Selection - Automatic expert routing
- Variance Reduction - Variance-aware blending

**Connections**:
- Generates: YAML configs
- Calls: TaskRunner to execute in Docker
- Container: breeding-vat-merge or breeding-vat-fusionbench

#### 7. **Task Runner** (`breeding_vat/orchestrator/runner.py`)

**Purpose**: Docker container orchestration

**Key Responsibilities**:
- Launch Docker containers
- Mount volumes (host dirs, GPU, docker socket)
- Execute commands in containers
- Capture output/logs

**Key Method**:
```python
runner.run_docker_task(
    image="breeding-vat-merge:latest",
    command=["mergekit-yaml", "/app/config.yaml", "/app/output/"],
    volumes={
        "breeding_vat/configs": "/app/configs",
        "breeding_vat/data": "/app/data"
    },
    gpus="all"
)
```

#### 8. **Evolution With Logging** (`breeding_vat/modules/evolution/evolution_with_logging.py`)

**Purpose**: Wraps EvolutionEngine with logging and progress callbacks

**Key Responsibilities**:
- Call underlying EvolutionEngine
- Log all events to master log file
- Call UI progress callback every cycle
- Save cycle results to experiment folder

#### 9. **SAE Analyzer** (`breeding_vat/modules/sae/scoped_analyzer.py`)

**Purpose**: Layer-wise introspection using Sparse Autoencoders

**Key Responsibilities**:
- Analyze model layer specialization
- Memory-efficient streaming (handles 0.5B-70B models)
- Generate feature descriptions

**Key Method**:
```python
analyzer = SAEScopedAnalyzer(model_id="gpt2", vram_gb=12)
results = analyzer.analyze_self(num_samples=30, num_layers=8)
# Returns: activation_statistics, specialized_layers, feature_importance
```

---

## Part 3: Data & Experiment Structure

### Experiment Folder Layout

When a user starts an experiment, this folder is created:

```
breeding_vat/data/experiments/
└── reasoning_3B_2025-01-15_152347/
    ├── experiment.json                  # Metadata
    │   {
    │     "name": "reasoning_3B_2025-01-15_152347",
    │     "goal": "Reasoning at 3B scale",
    │     "base_models": ["Qwen-0.5B", "Mistral-7B"],
    │     "merge_methods": ["slerp", "ties", "task_arithmetic"],
    │     "num_cycles_planned": 5,
    │     "cycles_completed": 3,
    │     "best_model": "mutant_c2_p1_ta",
    │     "best_score": 0.7234,
    │     "status": "running|completed|paused",
    │     "created_at": "2025-01-15T15:23:47",
    │     "paths": { "root": "...", "master_log": "...", ... }
    │   }
    │
    ├── master.log                       # Full timeline
    │   [15:24:00] Experiment created
    │   [15:24:01] Selected base models: Qwen-0.5B, Mistral-7B
    │   [15:24:12] Cycle 1 started
    │   [15:24:15] Merge method: SLERP
    │   [15:24:45] Merge complete: mutant_c1_p0_sl
    │   [15:25:00] Evaluation complete: score=0.6890
    │   [15:25:01] Culled 2 models from population
    │   ...
    │
    ├── merged_models/
    │   ├── mutant_c1_p0_sl/             # Cycle 1, Parent 0, Option SLERP
    │   │   ├── config.json              # Method parameters
    │   │   ├── model/                   # Model weights & configs
    │   │   └── metadata.json            # Timestamp, parents, method
    │   ├── mutant_c1_p1_ti/             # Cycle 1, Parent 1, Option TIES
    │   ├── mutant_c2_p0_ta/             # Cycle 2, Parent 0, Option TASK_ARITHMETIC
    │   └── mutant_c2_p1_rm/             # Cycle 2, Parent 1, Option REGMEAN
    │
    ├── configs/
    │   ├── cycle_1_slerp.yaml
    │   ├── cycle_1_ties.yaml
    │   ├── cycle_2_task_arithmetic.yaml
    │   └── cycle_2_regmean.yaml
    │
    ├── results/
    │   └── benchmarks.json
    │       {
    │         "cycles": [
    │           {
    │             "cycle": 1,
    │             "models": [
    │               {"name": "mutant_c1_p0_sl", "method": "slerp", "score": 0.6890},
    │               {"name": "mutant_c1_p1_ti", "method": "ties", "score": 0.7102}
    │             ]
    │           },
    │           ...
    │         ]
    │       }
    │
    └── logs/
        └── (container output logs from merge/eval)
```

### Database Schema (`breeding_vat/data/schema.sql`)

```sql
-- Experiments table
CREATE TABLE experiments (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    goal TEXT,
    base_models JSON,           -- List of model IDs
    merge_methods JSON,         -- List of allowed methods
    num_cycles_planned INTEGER,
    cycles_completed INTEGER,
    best_model_id INTEGER,
    best_score REAL,
    status TEXT,                -- running, completed, paused
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Models table (lineage tracking)
CREATE TABLE models (
    id INTEGER PRIMARY KEY,
    experiment_id INTEGER,
    name TEXT,                  -- mutant_c1_p0_sl
    base_models JSON,           -- Parents used
    merge_method TEXT,          -- slerp, ties, etc
    benchmark_results JSON,     -- {hellaswag: 0.689, arc_challenge: 0.751}
    lineage_parent_id INTEGER,  -- Parent model ID
    status TEXT,                -- active, culled, best
    cycle_number INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id),
    FOREIGN KEY (lineage_parent_id) REFERENCES models(id)
);

-- Merge recipes (configs used)
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    model_id INTEGER,
    experiment_id INTEGER,
    method TEXT,
    config JSON,                -- {alpha: 0.5, beta: 0.3, ...}
    notes TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

-- SAE discoveries
CREATE TABLE sae_discoveries (
    id INTEGER PRIMARY KEY,
    model_id INTEGER,
    experiment_id INTEGER,
    layer_index INTEGER,
    feature_description TEXT,
    geometric_shape TEXT,       -- e.g., "disk", "simplex"
    importance_score REAL,
    created_at TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);
```

---

## Part 4: Execution Flow - Variable Pipelines

The evolution pipeline is **highly variable** based on user settings:

### Pipeline Scenario 1: Simple (Default)

**User selects**: SLERP, TIES only

```
Cycle 1:
  1. Evolution picks random method → SLERP
  2. MergeKit generates config
  3. TaskRunner launches breeding-vat-merge container
  4. Merge completes → mutant_c1_p0_sl
  5. TaskRunner launches breeding-vat-eval container
  6. Benchmark completes → score 0.6890
  7. Log to master.log + benchmarks.json
  8. Culling: remove bottom 50%

Cycle 2:
  1. Evolution picks random method → TIES
  2. Repeat from step 2...
```

### Pipeline Scenario 2: FusionBench Methods + Parameters

**User selects**: Task Arithmetic (reg=0.3), DARE (drop=0.15)

```
Cycle 1:
  1. Evolution picks → Task Arithmetic
  2. FusionBench generates config with reg=0.3
  3. TaskRunner launches breeding-vat-merge container with config
  4. Merge uses TaskArithmetic: base + 0.3*δ_A
  5. Merge completes → mutant_c1_p0_ta
  6. Evaluation... → score 0.7234
  7. Log + cull

Cycle 2:
  1. Evolution picks → DARE
  2. FusionBench generates config with drop=0.15
  3. Merge with sparsity (drop 15% of weights)
  4. Continue...
```

### Pipeline Scenario 3: Expert Mixed (All Methods + SAE)

**User selects**: All 20+ methods + SAE analysis enabled

```
Cycle 1:
  Merge: Randomly pick from 20 methods
  Eval: Standard benchmark
  SAE: (optional) Analyze layers of best models
  Cull: Remove bottom 50%

Cycle 2:
  If SAE enabled:
    - Identify specialized layers in best model
    - Use layer assignments in next Frankenmerge
  Else:
    - Standard merge/eval/cull

Cycle 3-N:
  Repeat, with SAE discoveries informing next merges
```

### Pseudo-Code: Main Evolution Loop

```python
def run_waterfall(base_models, goal, num_cycles, allowed_methods):
    population = [base_models]  # Start with base models
    
    for cycle in range(1, num_cycles + 1):
        print(f"Cycle {cycle}/{num_cycles}")
        
        # Phase 1: MERGE - Create new models
        offspring = []
        for _ in range(population_size):
            # Randomly select parents
            parents = random.sample(population, k=2)
            
            # Randomly select method from allowed_methods
            method = random.choice(allowed_methods)
            
            # Get method parameters from UI (e.g., drop_rate for DARE)
            params = get_params_for_method(method)
            
            # Merge via appropriate backend
            merged = merger.{method}_merge(
                models=parents,
                output_path=f"mutant_c{cycle}_p{parent_idx}_{method[:2]}",
                **params
            )
            offspring.append(merged)
        
        # Phase 2: EVALUATE - Score new models
        for model in offspring:
            score = evaluate(model)  # Run benchmarks
            model.fitness = score
            log_to_file(f"Cycle {cycle}: {model.name} = {score}")
        
        # Phase 3: SAE ANALYSIS (optional)
        if sae_enabled and cycle % sae_interval == 0:
            best_model = max(offspring, key=lambda m: m.fitness)
            sae_results = sae.analyze(best_model)
            save_to_db(sae_results)
        
        # Phase 4: CULL - Remove poor performers
        all_models = population + offspring
        all_models.sort(key=lambda m: m.fitness, reverse=True)
        population = all_models[:culling_rate]  # Keep top X%
        
        # Log cycle results
        best = max(population, key=lambda m: m.fitness)
        log(f"Cycle {cycle} best: {best.name} (score={best.fitness})")
    
    # Return best model found
    return max(population, key=lambda m: m.fitness)
```

---

## Part 5: Docker Containerization Strategy

### Why Containers?

Each component runs in **isolated containers** to avoid dependency conflicts:

| Component | Container Image | Purpose | Packages |
|-----------|-----------------|---------|----------|
| UI | breeding-vat-ui | Streamlit interface | streamlit, torch, transformers |
| Merge | breeding-vat-merge | Model merging | torch, mergekit, fusion-bench |
| Eval | breeding-vat-eval | Benchmarking | lm-eval-harness, torch |
| SAE | breeding-vat-sae | Layer analysis | transformer-lens, einops |
| FusionBench | breeding-vat-fusionbench | Advanced evaluation | fusion-bench, torch |

### Container Launch Pattern

```python
# Example: Launching merge container
runner.run_docker_task(
    image="breeding-vat-merge:latest",
    command=[
        "mergekit-yaml",
        "/app/configs/cycle_1_slerp.yaml",
        "/app/data/merged_models/mutant_c1_p0_sl/"
    ],
    volumes={
        "breeding_vat/configs": "/app/configs",
        "breeding_vat/data": "/app/data",
        "~/.cache/huggingface": "/root/.cache/huggingface"  # Model cache
    },
    gpus="all",
    env={"PYTHONUNBUFFERED": "1"}
)
```

### Container Lifecycle

```
1. TaskRunner.run_docker_task() called
2. Docker container created from image
3. Volumes mounted (configs, data, model cache)
4. GPU allocated (--gpus all)
5. Command executed
6. Output captured
7. Container exits
8. (Container remains for logs inspection)
```

---

## Part 6: Building From Scratch

If someone wanted to rebuild The Breeding Vat from scratch:

### Step 1: Core Dependencies

```bash
# Python packages (installed in containers, not locally)
pip install streamlit torch transformers accelerate
pip install mergekit fusion-bench hydra-core
pip install lm-eval transformer-lens

# Docker images (built from Dockerfiles)
docker build -t breeding-vat-ui -f docker/Dockerfile.ui .
docker build -t breeding-vat-merge -f docker/Dockerfile.merge .
docker build -t breeding-vat-eval -f docker/Dockerfile.eval .
docker build -t breeding-vat-sae -f docker/Dockerfile.sae .
```

### Step 2: Core Modules (Build Order)

```
1. breeding_vat/data/schema.sql
   → Initialize SQLite database

2. breeding_vat/orchestrator/runner.py
   → TaskRunner for Docker orchestration

3. breeding_vat/modules/merge/
   ├─ mergekit_engine.py (MergeKit methods)
   ├─ fusionbench_engine.py (FusionBench methods)
   └─ merger.py (unified interface)

4. breeding_vat/modules/merge/
   ├─ evolution.py (core loop)
   └─ advisor.py (AI guidance)

5. breeding_vat/modules/experiment_manager.py
   → Experiment lifecycle

6. breeding_vat/modules/evolution/evolution_with_logging.py
   → Evolution with logging

7. breeding_vat/ui/app.py
   → Streamlit UI (imports all above)

8. scripts/manager.py
   → Container management
```

### Step 3: Entry Points

```bash
# setup.bat
→ Calls scripts/manager.py rebuild
→ Builds all Docker images
→ Initializes directories

# run.bat
→ Calls scripts/manager.py run
→ Ensures images exist
→ Launches breeding-vat-ui container
→ Opens http://localhost:8501
```

---

## Part 7: Key Design Decisions

### 1. **Why Docker for Everything?**

**Problem**: Different tools have conflicting dependencies
- MergeKit needs specific torch version
- lm-eval needs different transformers version
- SAE needs transformer-lens

**Solution**: Each tool in its own container with pinned dependencies

### 2. **Why Streamlit?**

**Problem**: Building a web UI from scratch is complex

**Solution**: Streamlit provides instant UI with real-time updates, no JavaScript

### 3. **Why SQLite?**

**Problem**: Need lightweight, portable database for genealogy tracking

**Solution**: SQLite embedded, no external database needed, files versioned in git

### 4. **Why 20+ Methods?**

**Problem**: No single merge method is best for all goals

**Solution**: Let evolution explore multiple methods, discover winner empirically

### 5. **Why Resumable Experiments?**

**Problem**: Evolution can take hours; user might interrupt

**Solution**: Save experiment state, allow resume from last cycle

---

## Part 8: Extension Points

### Adding a New Merge Method

```python
# 1. Implement in FusionBenchEngine (or MergekitEngine)
class FusionBenchEngine:
    def my_new_method_merge(self, base_model, models, output_path, **kwargs):
        config = FusionBenchConfigBuilder.build_my_method_config(...)
        return self.run_merge(config, output_path)

# 2. Add to AdvancedMerger
class AdvancedMerger:
    def my_new_method_merge(self, ...):
        return self.fusionbench.my_new_method_merge(...)

# 3. Register in AVAILABLE_METHODS
AVAILABLE_METHODS = {
    "my_new_method": "Description of what it does"
}

# 4. It appears automatically in UI
```

### Adding New Benchmark

```python
# In breeding_vat/modules/benchmark/ or Dockerfile.eval
# Add to lm-eval supported benchmarks:
# - Currently: hellaswag, arc_challenge, winogrande
# - Can add: commonsense_qa, truthfulqa, etc.

benchmark_cmd = [
    "lm-eval",
    "--model", model_id,
    "--tasks", "my_new_benchmark",
    "--output-path", results_dir
]
```

### Adding SAE Layer Analysis

```python
# Extend SAEScopedAnalyzer to identify new layer features
class SAEScopedAnalyzer:
    def analyze_self(self, ...):
        # ... existing code ...
        # Add new feature detector
        specialized_layers = self.identify_specialized_features()
        # Save to database
```

---

## Part 9: Summary Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                │
│  ├─ Method Selection (20+)                             │
│  ├─ Parameter Tuning (per-method)                      │
│  ├─ Real-time Progress                                 │
│  └─ Lineage Visualization                              │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │ Experiment Mgr   │ ◄─── Save/Load experiment state
        │ ExperimentMgr    │      (experiment.json, master.log)
        └────────┬─────────┘
                 │
        ┌────────▼──────────────────────────┐
        │  Evolution Engine                  │
        │  ├─ Run Waterfall Loop             │
        │  ├─ Select random method           │
        │  ├─ Merge → Eval → Cull            │
        │  └─ Track population fitness       │
        └────────┬───────────────────────────┘
                 │
        ┌────────┴────────────────────┬───────────────────┐
        │                             │                   │
   ┌────▼─────┐             ┌────────▼───────┐    ┌──────▼──────┐
   │ Advanced │             │ SAE Analyzer   │    │ Task Runner │
   │ Merger   │             │ (optional)     │    │ (Docker)    │
   └────┬─────┘             └────────────────┘    └──────┬──────┘
        │                                                 │
   ┌────┴──────────────────┬──────────────────────┐      │
   │                       │                      │      │
┌──▼──────┐    ┌───────────▼─────┐   ┌──────────▼─┐     │
│ MergeKit │    │  FusionBench    │   │  Config    │     │
│ Engine   │    │  Engine         │   │  Builder   │     │
│ (7 meth) │    │  (13+ methods)  │   │  (YAML)    │     │
└──┬───────┘    └────────────────┬┘   └────────────┘     │
   └────────────────┬─────────────┘                       │
                    │                                     │
        ┌───────────▼──────────────────┐                 │
        │  Merge Config (YAML)         │                 │
        │  {method, models, params...} │                 │
        └───────────┬──────────────────┘                 │
                    │                                     │
                    │                                     │
        ┌───────────▼──────────────────────────────────┐ │
        │  Docker Container (TaskRunner)                │ │
        │  ├─ breeding-vat-merge                        │ │
        │  │  └─ MergeKit / FusionBench execution       │ │
        │  ├─ breeding-vat-eval                         │ │
        │  │  └─ lm-eval harness benchmarking           │ │
        │  └─ breeding-vat-sae                          │ │
        │     └─ Sparse Autoencoder analysis            │ │
        └───────────┬──────────────────────────────────┘ │
                    │                                     │
        ┌───────────▼──────────────────┐                 │
        │  Results                      │                 │
        │  ├─ merged_model/weights      │                 │
        │  ├─ benchmarks.json (scores)  │                 │
        │  └─ master.log (timeline)     │                 │
        └──────────┬───────────────────┘                  │
                   │                                      │
        ┌──────────▼──────────────────┐                   │
        │  SQLite Database (lineage)   │                  │
        │  ├─ experiments table         │                  │
        │  ├─ models table (genealogy)  │                  │
        │  └─ recipes table (configs)   │                  │
        └──────────────────────────────┘                  │
                                                          │
                    ◄─────────────────────────────────────┘
                    (Feedback loop to Evolution Engine)
```

---

## Part 10: Critical Paths & Dependencies

### Critical Path 1: Container Startup
```
run.bat
  → scripts/manager.py run
    → ensure_images()
      → image_exists("breeding-vat-ui")
      → (if missing) rebuild_image("breeding-vat-ui", "docker/Dockerfile.ui")
    → run_ui()
      → docker run breeding-vat-ui:latest
      → webbrowser.open("http://localhost:8501")
```

### Critical Path 2: Evolution Execution
```
EvolutionEngine.run_waterfall()
  → for cycle in cycles:
      → merger.{random_method}(...)
      → (config generated)
      → TaskRunner.run_docker_task("breeding-vat-merge")
      → (merge completes, returns path)
      → TaskRunner.run_docker_task("breeding-vat-eval")
      → (score returned)
      → ExperimentManager.log_cycle()
      → (update database, master.log)
```

### Critical Path 3: SAE Analysis
```
SAEScopedAnalyzer.analyze_self()
  → (loads model in streaming fashion)
  → (analyzes each layer with memory management)
  → (identifies feature specialization)
  → (saves to breeding_vat/data/sae_analysis/)
```

---

**End of Architecture Document**

This document describes the complete system as of January 15, 2025 with FusionBench integration (20+ methods). It covers all dependencies, design decisions, and extension points needed to understand or rebuild the system.
