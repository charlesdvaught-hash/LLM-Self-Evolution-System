# QUICK REFERENCE — Exact Imports & File Locations

For implementing the 5 code changes in EXACT_CODE_CHANGES.md

---

## File 1: evolution.py

**Full path**: `breeding_vat/modules/merge/evolution.py`

**Imports to add** (at top):
```python
from datetime import datetime  # For timestamps in metadata
```

**Current imports** (verify they exist):
```python
import random
import time
import torch
import gc
import os
import json
import sqlite3
import logging
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.mergekit_engine import MergekitEngine
from breeding_vat.modules.merge.merger import AdvancedMerger
from breeding_vat.modules.benchmark.evaluator import BenchmarkEvaluator
```

**Changes**:
1. Line ~20 (in `__init__`): Add `self._experiment_manager = None` and `self._current_experiment = None`
2. Line ~70 (after culling): Add log_cycle() call
3. Line ~55 (in offspring loop): Enhance metadata dict

---

## File 2: evolution_with_logging.py

**Full path**: `breeding_vat/modules/evolution/evolution_with_logging.py`

**Current imports** (verify):
```python
import os
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
```

**Changes**:
1. Line ~75 (before evolution.run_waterfall()): Inject manager + experiment

---

## File 3: evaluator.py

**Full path**: `breeding_vat/modules/benchmark/evaluator.py`

**Imports to add** (at top):
```python
from datetime import datetime  # For timestamps
from breeding_vat.modules.benchmark.receipt_runner import BenchmarkRunner  # For anomalies
```

**Current imports** (verify):
```python
import os
import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
from breeding_vat.modules.benchmark.prediction_engine import ExperimentDatabase
```

**Changes**:
1. Line ~18: Add return type hint to evaluate() method signature
2. Replace entire evaluate() method body (lines ~115-180)

---

## File 4: app.py

**Full path**: `breeding_vat/ui/app.py`

**Status**: Already handles dict returns, no changes needed

**Verify**: Line where we call `best_model = evo_logged.run_waterfall(...)`

If BenchmarkEvaluator.evaluate() now returns dict, this should work fine because:
- best_model still has `best_model['score']`
- best_model still has `best_model['name']`
- UI still works

---

## File 5: experiment_manager.py

**Full path**: `breeding_vat/modules/experiment_manager.py`

**Status**: Already correct, no changes needed

**Key method**: `log_cycle()` at line ~120

**Signature**:
```python
def log_cycle(self, experiment: Dict, cycle_num: int, 
              models: List[Dict], best_model: Dict):
```

**Expected input**:
```python
models = [
    {
        "name": "mutant_c1_p0_slerp",
        "score": 0.748,
        "method": "slerp",
        "method_params": {},
        "parents": ["model_a", "model_b"],
        "benchmark": {...},
        "anomalies": [...]
    }
]
best_model = {"name": "mutant_c1_p0_slerp", "score": 0.748}
```

---

## Dependency Check

**Libraries already in project** (verified working):
- ✅ torch (EvolutionEngine uses it)
- ✅ transformers (BenchmarkEvaluator uses it)
- ✅ lm-eval (BenchmarkEvaluator uses it)
- ✅ datetime (standard library)

**No new external dependencies needed**

---

## Constants & Magic Numbers

From evaluator.py:
```python
PERPLEXITY_FAIL_THRESHOLD = 1000.0  # Broken merge threshold
```

From receipt_runner.py:
```python
CHANCE_LEVEL = 0.25  # 4-choice multiple choice
```

Anomaly thresholds (add to evolution.py if needed):
```python
SCORE_JUMP_THRESHOLD = 0.2  # 20% change flags anomaly
TASK_DISPARITY_THRESHOLD = 0.2  # Tasks differ by >20%
```

---

## Test Files Created This Session

After implementing changes, create test:

**New file**: `breeding_vat/test_genealogy.py`

```python
import pytest
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.orchestrator.runner import TaskRunner

def test_genealogy_capture():
    # See EXACT_CODE_CHANGES.md for full test code
    pass
```

---

## File Structure After Changes

```
breeding_vat/
├── modules/
│   ├── merge/
│   │   └── evolution.py (MODIFIED: +70 lines)
│   ├── evolution/
│   │   └── evolution_with_logging.py (MODIFIED: +3 lines)
│   ├── benchmark/
│   │   └── evaluator.py (MODIFIED: ~120 lines)
│   └── experiment_manager.py (UNCHANGED)
├── ui/
│   └── app.py (UNCHANGED)
└── test_genealogy.py (NEW: if you create it)
```

---

## Verification Checklist After Implementation

```
Code changes applied:
- [ ] evolution.py: injection points added
- [ ] evolution.py: log_cycle() call added
- [ ] evolution.py: model metadata enriched
- [ ] evolution_with_logging.py: injection added
- [ ] evaluator.py: returns dict instead of float
- [ ] evaluator.py: anomaly detection added

Imports verified:
- [ ] datetime imported in evolution.py
- [ ] datetime imported in evaluator.py
- [ ] BenchmarkRunner imported in evaluator.py

Tests run:
- [ ] Python syntax check: python -m py_compile breeding_vat/modules/merge/evolution.py
- [ ] Import check: python -c "from breeding_vat.modules.merge.evolution import EvolutionEngine"
- [ ] E2E test: run UI with test experiment

Genealogy captured:
- [ ] benchmarks.json exists in exp folder
- [ ] Contains cycle 1 results
- [ ] Each model has: name, score, method, parents, benchmark, anomalies
- [ ] Culling happened (models removed from population)
- [ ] Survivors have correct parent references
```

---

## Quick Debug Checklist

If something breaks:

**ImportError**: Missing module?
```python
# Check these are importable:
from breeding_vat.modules.merge.evolution import EvolutionEngine
from breeding_vat.modules.evolution.evolution_with_logging import EvolutionWithLogging
from breeding_vat.modules.experiment_manager import ExperimentManager
from breeding_vat.modules.benchmark.evaluator import BenchmarkEvaluator
```

**TypeError**: evaluate() returns wrong type?
```python
# Should now return dict:
result = evaluator.evaluate(model_name)
assert isinstance(result, dict)
assert "score" in result
assert "anomalies" in result
```

**AttributeError**: experiment_manager not injected?
```python
# In EvolutionWithLogging, before run_waterfall():
assert self.evolution._experiment_manager is not None
assert self.evolution._current_experiment is not None
```

**FileNotFoundError**: benchmarks.json not created?
```python
# Check:
exp_path = exp['paths']['results']
json_path = os.path.join(exp_path, "benchmarks.json")
assert os.path.exists(json_path), f"Not found: {json_path}"
```

---

## Performance Expectations

After implementing genealogy wiring:

**Per cycle** (2 base models, SLERP+TIES):
- Merge 4 offspring: ~10 min
- Evaluate 4 models: ~8 min (2 min per model = 15s perplexity + 1m45s lm-eval)
- Cull to 2: instant
- Log to benchmarks.json: <1s
- **Total per cycle: ~18-20 min**

**3 cycles**:
- Cycle 1: 4 offspring → 2 survivors
- Cycle 2: 4 offspring → 2 survivors
- Cycle 3: 4 offspring → 2 survivors
- **Total genealogy**: ~6-8 model lineage (with culling)
- **Total time**: ~60 min locally

---

**End of QUICK_REFERENCE.md**

Use this alongside EXACT_CODE_CHANGES.md for implementation.
