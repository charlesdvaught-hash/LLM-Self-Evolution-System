# Repository Map: The Breeding Vat

```text
.
├── breeding_vat/
│   ├── orchestrator/        # Core task management & DB logic
│   │   ├── runner.py        # Docker Task Runner
│   │   └── ...
│   ├── ui/                  # Streamlit Frontend
│   │   └── app.py           # Control Room UI
│   ├── modules/             # Functional "Engines"
│   │   ├── merge/           # MergeKit, RMM, Advisor, Evolution
│   │   ├── eval/            # Benchmarking wrappers
│   │   ├── sae/             # SAE discovery tools
│   │   └── train/           # LoRA/PEFT training logic
│   ├── data/                # Persistent Storage
│   │   ├── schema.sql       # Database structure
│   │   ├── breeding.db      # SQLite Lineage DB (Generated)
│   │   └── merged_models/   # Weights storage (Ignored by Git)
│   └── configs/             # Generated YAML recipes
├── docker/                  # Specialized environment bundles
│   ├── Dockerfile.ui        # Streamlit environment
│   ├── Dockerfile.merge     # MergeKit + SVD tools
│   ├── Dockerfile.eval      # Evaluation harness
│   └── Dockerfile.sae       # SAE & Feature analysis
├── architecture.md          # System design overview
├── map.md                   # This file
├── setup.bat                # One-click installation
├── run.bat                  # One-click startup
└── requirements.txt         # Core Python dependencies
```
