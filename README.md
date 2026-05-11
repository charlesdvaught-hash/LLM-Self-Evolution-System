# The Breeding Vat: Local Model Evolution Lab

A one-stop shop for model merging and "creation" from base models.

## Core Features
- **Evolutionary Search**: Automate merging recipes using CMA-ES and genetic algorithms.
- **Waterfall Pipeline**: Linear-appearing but branching evolution cycles with culling.
- **Advanced Merging**: Support for RMM, Latent Merging, Core Space, and NegMerge.
- **SAE Analysis**: Identify high-potential layers using Sparse Autoencoders.
- **Advisor Integration**: Qwen 3.5 0.8B helps design recipes and analyze benchmarks.

## Setup (Windows)
1. Ensure you have Docker and Python 3.10+ installed.
2. Run `setup.bat`.
3. Start the UI: `streamlit run breeding_vat/ui/app.py`.

## Resource Management
Designed for consumer hardware:
- **Max VRAM**: 12GB (Aggressive process management).
- **Max RAM**: 16GB.
- **Max Model Size**: 12B parameters.

## Directory Structure
- `breeding_vat/orchestrator/`: Task management and Docker runner.
- `breeding_vat/ui/`: Streamlit interface.
- `breeding_vat/modules/`: Merge, Eval, Train, and SAE logic.
- `breeding_vat/data/`: SQLite database and merged model storage.
- `breeding_vat/configs/`: YAML recipes.
