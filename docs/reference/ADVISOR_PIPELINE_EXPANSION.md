# Advisor: Pipeline Expansion Reference

Dense technical data for 0.8B models to understand internal 'Breeding Vat' mechanics.

## 🧬 Evolution Workflow
1. **Initialize**: Load parents (base models) into `population`.
2. **Mutate**: Pick random method (SLERP, TIES, etc.) + sibling.
3. **Merge**: Execute `mergekit-yaml` or `fusion-bench` in Docker.
4. **Evaluate**: Score offspring using `lm-eval-harness` (HellaSwag/ARC).
5. **Cull**: Keep top-X% based on scores; losers are deleted from disk.

## ⚙️ New Merging Levers (Toggles)
| Lever | Technical Purpose | Recommended Use |
|-------|-------------------|-----------------|
| `low_cpu_mem` | Map weights to disk instead of RAM | Enable if Host RAM < 32GB |
| `copy_tokenizer` | Inherits vocab from first parent | Always Enable unless base is empty |
| `trust_remote_code` | Executes model-specific Python code | Enable for Qwen/Phi-3 |
| `lazy_unpickle` | Defers weight loading to reduce spikes | Enable for >12B parameter models |

## 🛠️ Engine Backends
- **MergeKit**: Best for SLERP, TIES, DARE. Reliable, low-level.
- **FusionBench**: State-of-the-art RegMean, Task Arithmetic, and Frankenmerges.
- **TaskRunner**: Python class managing Docker socket for container lifecycle.

## 📂 Data Locations (Container Paths)
- `/app/data/merged_models/`: Output weights.
- `/app/configs/`: Generated YAML recipes.
- `/app/data/eval_results/`: JSON benchmark scores.
