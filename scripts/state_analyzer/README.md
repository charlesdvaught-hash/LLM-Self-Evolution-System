# System State Analyzer 🧬

The **System State Analyzer** is a standalone utility designed to generate a deterministic "shared truth" snapshot of your repository. It maps your code structure, Docker runtime, and documentation intent into a single JSON file (`system_state.json`), enabling external AI assistants (like Claude or Docker AI) to understand your project with zero hallucination.

## 🚀 Key Features

- **Execution Path Tracing**: Automatically discovers entrypoints from scripts (e.g., `run.bat`) and traces the full internal import chain.
- **Docker Discovery**: Scans root-level and script-dir files for Docker commands (`run`, `build`, `compose`) to identify orchestration intent.
- **Structural Health**: Identifies broken internal imports and potentially orphaned modules.
- **Intent vs. Truth**: Compares Markdown documentation against actual code to find contradictions and documentation drift.
- **Aider Integration**: Flags "suspicious" files (broken imports, contradictions, dead code) for review with Aider.
- **Hardware Guard**: Automatically skips files larger than a specified limit (default 5MB) to prevent memory issues.
- **Standalone**: No dependencies on the main project package. Only requires Python 3 and standard libraries.

## 🛠 Installation

No complex installation is required. Simply ensure you have Python 3.x installed.

```bash
# Clone or copy the scripts/state_analyzer directory into your repository
# No pip install required (uses standard library: ast, re, json, subprocess)
```

## 📖 Usage

Run the analyzer from the root of your repository:

```bash
python scripts/state_analyzer/analyzer.py
```

### Advanced Options

```bash
# Analyze a specific root directory
python scripts/state_analyzer/analyzer.py --root /path/to/your/repo

# Manually point to scripts containing Docker orchestration
python scripts/state_analyzer/analyzer.py --manual-docker-files setup.bat run.bat

# Specify a custom output filename
python scripts/state_analyzer/analyzer.py --output my_repo_truth.json

# Adjust hardware guard (file size limit)
python scripts/state_analyzer/analyzer.py --max-size-mb 10
```

## 🤖 Aider Integration

The analyzer identifies files that need attention and stores them in the `review_recommendations` section of the JSON. You can use this to quickly target problematic areas with Aider:

```bash
# Example: Review the highest priority problematic file
aider $(jq -r '.review_recommendations | sort_by(.priority) | reverse | .[0].file' system_state.json)
```

## 🤖 How to use with LLMs

Once you generate `system_state.json`, you can feed it into your AI assistant of choice along with your questions.

**Example Prompt:**
> "I am using the attached `system_state.json` as the ground truth for my repository. Based on the 'execution_paths' and 'structural_health' sections, what is the safest way to merge the 'feature-new-eval' branch without breaking the core orchestrator?"

## 📊 Output Schema

The tool produces a JSON object with the following top-level keys:

- `modules`: List of all Python modules with their imports, definitions, and unused code detection.
- `intent_from_md`: Fuzzy extraction of system goals and pipelines from documentation.
- `runtime_truth`: Current Docker state and orchestration intent discovered in scripts.
- `execution_paths`: Traced import chains starting from discovered entrypoints.
- `structural_health`: Report on broken imports and code complexity.
- `orphan_suspects`: Modules that appear unreferenced across code, docs, and runtime.
- `contradictions`: Specific mismatches where documentation disagrees with the filesystem.

---
*🧬 Stop guessing. Start evolving with ground truth.*
