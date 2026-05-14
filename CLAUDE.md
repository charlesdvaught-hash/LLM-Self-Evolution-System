# Breeding Vat — CLAUDE.md
## Session Notes & Standing Instructions

---

## 📚 Documentation Index & Current State

**Most Up-To-Date References** (as of this session):

| Document | Version | Freshness | Scope |
|----------|---------|-----------|-------|
| `Map.json` | 2.0 (Jan 15) | ✅ Current | Complete file inventory + dependencies |
| `DESIGN_PHILOSOPHY.md` | NEW | ✅ Current | **Ominous, technical, fabricator feel** |
| `Architecture.md` (RevampRefactor) | 3.0 (May 12) | ✅ Current | Full system design, 3-axis ASSAY framework |
| `PromptREADME.txt` | Latest | ✅ Current | Benchmark generation philosophy + 3-axis triangulation |
| `CLAUDE.md` | This file | ✅ Current | Session notes + constraints + critical path |

---

## Hard Constraints (never override without explicit user confirmation)

- **Options-first**: every new feature is opt-in, never a new default. Checkboxes, not auto-behaviors.
- **Code out of sight**: `setup.bat` installs, `run.bat` starts, everything else via Streamlit UI + AI assistants.
- **GPU work via Docker-out-of-Docker**: UI container is CPU-oriented; heavy inference hits a GPU container.
- **Never expand the default pipeline**: build standalone tools the user can invoke from the GUI or AI assistant. Do not add steps that run automatically without the user choosing them.
- **RTX 5070 / 8GB VRAM**: size all model loading and batch logic accordingly.
- **Use existing libraries**: prefer lighteval / lm-eval / mergekit / transformers over hand-rolled equivalents.

---

## CRITICAL PATH: Recipe System Backbone

**The recipe system is THE foundation.** It translates user "fabrication orders" into branching evolution execution.

### Recipe Flow (UI → Execution)

```
User sets parameters in UI
  ↓
UI generates recipe JSON:
{
  "metadata": {"name": "goal", "goal": "..."},
  "evolution": {
    "base_models": [...],
    "merge_methods": {...},
    "num_cycles": 5,
    "culling_rate": 50
  },
  "evaluation": {"tier": "standard"},
  "finetuning": {"enabled": false},
  "assay": {"enabled": false},
  "sae": {"enabled": false}
}
  ↓
RecipeExecutor.validate(recipe) — checks constraints
  ↓
RecipeValidator checks:
  ├─ Method is allowed
  ├─ Numeric params in bounds
  ├─ No shell injection
  ├─ Required fields present
  ↓
RecipeExecutor.build_evolution_config(recipe) — convert to engine config
  ↓
EvolutionEngine.run_waterfall(config)
  ├─ For each cycle:
  │  ├─ Merge N models (branching)
  │  ├─ Benchmark each (capture quirks)
  │  ├─ Cull bottom X%
  │  └─ Update UI live (genealogy, anomalies)
  └─ Return best model + full genealogy
```

### Key Recipe Modules

**RecipeExecutor** (`breeding_vat/modules/recipe_executor.py`):
- `load_recipe()` / `save_recipe()` — disk I/O
- `validate()` — check schema + constraints
- `build_evolution_config()` — convert recipe → engine config
- `build_finetuning_config()` — extract fine-tuning params
- `build_assay_config()` — extract ASSAY params
- `describe()` — human-readable summary

**RecipeValidator** (`breeding_vat/modules/merge/recipe_validator.py`):
- `validate()` — raises ValidationError on failure
- `check()` — non-raising (returns bool, reason)
- Checks: method allowed, params in bounds, no shell injection

---

## Pending Work — LOCAL PRIORITIZATION

**CRITICAL: Wire Recipe System into UI & Evolution**

### PHASE 1: Recipe System Integration (PRIORITY: IMMEDIATE)

**1.1 Wire RecipeExecutor into app.py**
- [ ] UI form generates recipe JSON (goal, methods, cycles, constraints)
- [ ] RecipeExecutor.validate() checks it before execution
- [ ] RecipeExecutor.build_evolution_config() → EvolutionEngine config
- [ ] Flow: UI form → recipe JSON → validated → executed
- Files: `breeding_vat/ui/app.py`, `recipe_executor.py`

**1.2 Test recipe → evolution execution (end-to-end)**
- [ ] Load recipe from UI or disk
- [ ] EvolutionEngine.run_waterfall() executes it
- [ ] Each cycle:
  - Merge N models (branching population)
  - Benchmark each (perplexity + arc_easy/challenge/hellaswag)
  - Capture anomalies (score jumps, specialization, structural damage)
  - Cull bottom X% (keep winners)
  - Track genealogy (parent IDs, method, scores, anomalies)
  - Update UI live (current cycle, best model, population count)
- Files: `evolution.py`, `evolution_with_logging.py`, `experiment_manager.py`

**1.3 Verify branching + culling logic**
- [ ] Each cycle produces exponential population (2 → 4 → 8, etc.)
- [ ] Culling removes bottom 50% (or user-configured rate)
- [ ] Winners breed next cycle
- [ ] Full genealogy preserved (never deleted)
- Test case: 2 base models, SLERP+TIES, 3 cycles → should have ~16 models in genealogy, 2-4 survivors

**1.4 Test quick benchmark on every model**
- [ ] Perplexity check (15s) — catches broken merges
- [ ] Arc Easy (30s) — basic reasoning
- [ ] Arc Challenge (30s) — constrained reasoning
- [ ] HellaSwag (1min) — narrative understanding
- [ ] Quirk detection (30s) — flags anomalies:
  - ⚠️ Score jumped 20% vs parent
  - ⚠️ Perplexity spiked (structural damage?)
  - ⚠️ One task >> other tasks (specialization? loss?)
  - ✓ Perplexity stable (merge OK)
- Files: `benchmark/evaluator.py`, `benchmark/scope_filter.py`

### PHASE 2: Docker + Infrastructure (PRIORITY: HIGH)

- [ ] Build all Docker images locally (ui, merge, eval, sae, fusionbench)
- [ ] Verify TaskRunner launches containers correctly
- [ ] Test volume mounts (data, configs, models)
- [ ] Test GPU allocation (RTX 5070, 8GB VRAM) — profile peak memory per operation
- [ ] Test container health checks + error handling

### PHASE 3: Test Full Fabrication Run (PRIORITY: HIGH)

- [ ] Run test fabrication locally: 2 base models, SLERP+TIES, 3 cycles
- [ ] Verify all genealogy data collected (parents, methods, scores, anomalies)
- [ ] Verify UI updates live (real-time progress)
- [ ] Verify export works (save best model, genealogy tree)
- [ ] Verify no data loss (every model preserved)
- [ ] Collect timing profile (how long per cycle? total time?)

### PHASE 4: Local Stabilization (PRIORITY: HIGH)

- [ ] Fix any import errors or missing dependencies
- [ ] Document any bugs found locally
- [ ] Clean up duplicate SCOPE-Qwen (gguf/ and model_zoo/)
- [ ] Delete incomplete cognitive-behaviors-Qwen2.5-3B
- [ ] Update run.bat / setup.bat if paths changed
- [ ] Verify all base models download correctly

### PHASE 5: Optional Enhancements (PRIORITY: LATER)

- [ ] Fine-tuning per-cycle (optional checkbox)
- [ ] Synthetic benchmark generation (post-Phase 1 stabilization)
- [ ] Fill prompt pack placeholders (QuickAssistant, Smartassistant)
- [ ] ASSAY tab (3-axis measurement)
- [ ] Receipt generation (opt-in, 2-stage lighteval)
- [ ] SAE analysis integration (optional)
- [x] **Advanced orthogonal toggles** (11 opt-in S+A-tier) — wired May 2026:
  - `breeding_vat/modules/merge/advanced_toggles.py` — post-merge transforms + outer-loop helpers
  - `MergekitConfigBuilder.apply_*` in `mergekit_engine.py` — YAML emitters (slices / filter / density / weight / tokenizer_source / passthrough)
  - `MergekitEngine.config_hook` — pluggable YAML mutator
  - `EvolutionEngine.advanced` + `_apply_advanced_yaml` + `_apply_post_transforms` + `_mutate_advanced_for_cycle` — cycle-time application & evolutionary mutation
  - `RecipeValidator.PARAM_BOUNDS / PARAM_CHOICES / ADVANCED_TOGGLE_KEYS / _check_advanced` — validation
  - `RecipeExecutor.build_advanced_config` — recipe → engine config bridge
  - `app.py` "🧬 Advanced Presets (Opt-in)" sidebar expander — 11 toggles, each with `mutate across cycles` checkbox + help text
  - Reference doc: `docs/reference/MERGING_METHODS_INVENTORY.md` → "Advanced Orthogonal Toggles (Opt-in)"
  - 8 toggles ride MergeKit YAML (existing CLI); 3 use post-merge streaming state_dict transform (safetensors shard-by-shard, 8GB-VRAM safe); 1 outer-loop sampler.

---

## ASSAY — Full Three-Axis Measurement Pipeline

ASSAY is the user's name for the complete triangulated diagnosis system. It is NOT just activation contrast. It has three orthogonal axes:

| Axis | Tool | What it measures |
|------|------|-----------------|
| Structural | SCOPE-Qwen activation contrast | Which layers fire per quality class (great / acceptable / wrong / hallucinated) |
| Geometric | LaSER output embedding comparison | Pre/post-merge embedding distribution shift on the same prompt set |
| Semantic | MergeAdvisor / QA model | Behavioral quality and strategy interpretation |

**Implementation note**: To use LaSER as the geometric oracle, run the same prompt set through the model before and after a merge, encode outputs with LaSER, then compare embedding distributions alongside SCOPE-Qwen's internal predictions. This full pipeline = ASSAY.

ASSAY is a GUI tool (tab 7 in app.py, "⚗️ ASSAY"). It is opt-in.

Outputs feed into:
- `frankenmerge_layer_assignment` (signal layers → layer-selective merge targets)
- `assay_lora_targets` (instability layers → LoRA fine-tuning targets)

---

## Receipt System

Every produced model gets a locked, write-once receipt (JSON). Receipts live in `breeding_vat/data/experiments/<name>/receipts/`.

Key modules:
- `breeding_vat/modules/benchmark/receipt_runner.py` — lighteval-based two-stage benchmark runner
  - Stage 1: 25 questions; if scaled_score ≥ 65 → Stage 2: 50 questions
  - Scoring: `max(0, (accuracy - 0.25) / 0.75) × 100` (chance-corrected for 4-choice MC)
  - Anomaly flags: `below_chance`, `early_failure`, `strong_ceiling`
- `breeding_vat/modules/benchmark/receipt_writer.py` — write-once ReceiptWriter
  - `write()` enforces single-write; `load()`; `list_receipts()`
- `breeding_vat/data/benchmark/general_benchmark.json` — 40 questions, domain-relevant (merge methods, layer behavior, activation analysis, etc.), NOT general knowledge
- `breeding_vat/data/benchmark/general_benchmark.jsonl` — lighteval-compatible format

Receipt auto-generation into the evolution cycle is **not yet wired** — it's a pending opt-in feature.

Receipts are displayed in the Lineage tab (tab 2) of app.py.

---

## Prompt Packs

Located in `breeding_vat/data/Prompts/`. User-created, drop-in system prompts for local models:

| File | Role | Model size |
|------|------|-----------|
| `qwenbasedAImergespecialistq&a.txt` | Merge theory Q&A / semantic axis | 1.5B |
| `qwenbasedbenchmarkgenerator.txt` | Synthetic benchmark generator (4 modes) | 1.5B |
| `QuickAssistant.txt` | Restricted codebase operator, defers to 4B | 1.5B |
| `Smartassistant.txt` | Strategic system designer | 4B |
| `PromptREADME.txt` | Design doc — three-axis triangulation framework overview | — |

**Pending**: Both `QuickAssistant.txt` and `Smartassistant.txt` have `[USER_DEFINED_INTERACTION_LAYER_HERE]` placeholders that need filling with actual file paths, key function invocations, and execution patterns from this codebase.

---

## SCOPE-Qwen (scoped_analyzer.py) — Known Bugs Fixed

Three bugs were fixed in `breeding_vat/modules/sae/scoped_analyzer.py`:
1. `hidden_dim` hardcoded to 768 — fixed with sentinel=1 + first-chunk-only init
2. Sparsity calc used `.item()` on multi-element tensor — fixed with `.float().mean().item()`
3. `analyze_self()` had no `topic` param — added `Optional[str]`, prefixes prompts when provided

---

## Models — Status Notes

- **SCOPE-Qwen**: duplicate copies in both `gguf/` and `model_zoo/` — not yet cleaned up
- **cognitive-behaviors-Qwen2.5-3B**: only shard 3/3 present (incomplete download, ~2.4GB of 12.3GB); also requires float32 = 12GB VRAM. Irrelevant to this domain. Set aside.
- **LaSER** is Qwen3-4B; **SCOPE** is the DeepSeek-based introspection model — naming was confused in early brainstorming, now clarified.

---

## Naming

- **ASSAY** — the three-axis measurement tool (chosen for uniqueness; no competing LLM tools with that name at time of selection)
- **The Breeding Vat** — the full system (LLM fabricator)
- **MergeFusion** — the merge routing / evolution engine
- **Fabrication** — the process of evolving models (not "training")
- **Recipe** — the configuration that drives a fabrication run

---

## Context Refresh

When starting a new session on this project, proactively read (without asking):
- `DESIGN_PHILOSOPHY.md` (aesthetic + intent)
- `CLAUDE.md` (this file, critical path)
- `Map.json` (file inventory)
- `Architecture.md` (if digging into design)
