# Multi-Advisor System Documentation

## Overview

The **Multi-Advisor System** lets you configure multiple specialized AI advisors with distinct prompting strategies. Each advisor has a unique role and perspective on model merging.

## Pre-Configured Advisors

### ⚡ Quick Advisor
- **Model**: Qwen/Qwen2.5-0.5B-Instruct (smallest, fastest)
- **Role**: Fast, pragmatic heuristics
- **Use Case**: Quick recommendations when you need immediate guidance
- **Output**: 1-2 sentence answers focused on speed
- **Prompt Focus**: Immediate heuristics, reliable methods, quick wins

### 🔬 Thorough Advisor
- **Model**: Qwen/Qwen2.5-1.5B-Instruct (medium, balanced)
- **Role**: Deep technical analysis
- **Use Case**: Detailed strategic planning for complex evolution
- **Output**: Structured response with reasoning, pros/cons, parameter suggestions
- **Prompt Focus**: Architecture analysis, capability complementarity, failure modes

### 🧠 Reasoning Specialist
- **Model**: Qwen/Qwen2.5-1.5B-Instruct
- **Role**: Optimize for reasoning capabilities
- **Use Case**: When your goal is to enhance reasoning, problem-solving, chain-of-thought
- **Output**: Reasoning-specific merge strategies
- **Prompt Focus**: Preserves logical chains, step-by-step solving, analytical capabilities
- **Special**: Aware of reasoning-focused GGUF models

### ⚙️ Inference Specialist
- **Model**: Qwen/Qwen2.5-0.5B-Instruct
- **Role**: Optimize for speed and efficiency
- **Use Case**: When you need fast inference or small model size
- **Output**: GGUF-compatible merge strategies
- **Prompt Focus**: Quantization-friendliness, layer pruning, memory optimization
- **Special**: Considers GGUF quantized models

### 🧬 Frankenstein Architect
- **Model**: Qwen/Qwen2.5-3B-Instruct (largest, most creative)
- **Role**: Radical creative experimentation
- **Use Case**: Exploring extreme merge combinations
- **Output**: Bold, unconventional strategies
- **Prompt Focus**: Layer-wise selection, MOE routing, experimental combinations

## Default Setup

By default, **two advisors are active**:
- `quick` — For fast guidance
- `thorough` — For detailed analysis

You can:
1. Add more advisors (e.g., add `reasoning` specialist)
2. Replace existing advisors with different roles
3. Create fully custom advisors with your own prompts

## Adding Advisors in UI

(Coming soon: Advisor configuration panel)

```python
# Manual setup (Python)
from breeding_vat.modules.multi_advisor import MultiAdvisor, MultiAdvisorConfig

ma = MultiAdvisor()
ma.add_advisor("quick", MultiAdvisorConfig("quick"))
ma.add_advisor("thorough", MultiAdvisorConfig("thorough"))
ma.add_advisor("reasoning", MultiAdvisorConfig("reasoning"))
```

## GGUF Model Integration

The system discovers GGUF models from `breeding_vat/data/GGUF Models/`:

```
breeding_vat/data/GGUF Models/
├── Ternary-Bonsai-8B-Q2_0.gguf          (local GGUF file)
├── qwen-ai-research-qa-q4_k_m.gguf.url (reference URL)
└── qwen-ai-research-qa-q4_k_m.gguf/    (model directory)
    └── qwen-ai-research-qa-q4_k_m.gguf
```

GGUF models are:
- **Not yet directly usable** as advisor backends (architecture limitation)
- **Available for reference** in advisor recommendations
- **Prepared for future** llama.cpp integration

### Your GGUF Models

1. **Ternary-Bonsai-8B-Q2_0.gguf** (2GB, ultra-quantized)
   - Extreme efficiency focus
   - Q2_0 quantization (minimal accuracy loss)
   - Best for inference optimization

2. **qwen-ai-research-qa-q4_k_m.gguf** (1.9GB, Q4_K_M)
   - Source: https://huggingface.co/InduwaraR/qwen-ai-research-qa-q4_k_m.gguf
   - Specialized in AI research Q&A
   - Good for reasoning advisor recommendations
   - Q4_K_M quantization (better quality than Q2)

3. **DeepSeek Qwen Fine-tune** (to be added)
   - TBD

4. **LaSER-Qwen3-8B** (long context specialist)
   - Source: https://huggingface.co/Alibaba-NLP/LaSER-Qwen3-8B
   - Specializes in long document understanding
   - Good for retrieval-focused evolution

## Usage Workflow

### Step 1: Create Experiment
Define your goal (e.g., "Reasoning at 3B scale")

### Step 2: Select Advisors
Pick which advisors you want (Quick + Thorough = default)

### Step 3: Consult Advisors
Ask advisors questions:
- "How should I merge these models?"
- "What methods work best for reasoning?"
- "Optimize for inference speed"

### Step 4: Execute Evolution
Run evolution with advisor-suggested parameters

## Advisor Prompts (Reference)

### Quick Advisor System Prompt
```
You are a fast, pragmatic model merging advisor. Your role is to suggest QUICK 
merge strategies in 2-3 sentences.

Focus on:
- Speed over precision
- Methods that work reliably (slerp, ties, task_arithmetic)
- Immediate heuristics based on model names/sizes
- Quick wins without deep analysis

CRITICAL: Answer in exactly 1-2 sentences. No elaboration.
```

### Thorough Advisor System Prompt
```
You are a meticulous model merging expert. Your role is to provide DEEP, THOUGHTFUL 
merge recommendations.

Analyze systematically:
1. Model architectures and training objectives
2. Capability complementarity
3. Merge method pros/cons for this specific pair
4. Parameter tuning suggestions
5. Expected outcome and failure modes

Format your response clearly with headers. Be thorough but concise.
```

### Reasoning Specialist System Prompt
```
You are a reasoning-focused merging specialist trained on AI research datasets.
Your expertise: merging models for enhanced reasoning, chain-of-thought, and problem-solving.

Recommend merges that:
- Preserve logical reasoning chains
- Enhance step-by-step problem solving
- Combine disparate reasoning approaches
- Avoid catastrophic forgetting of analytical capabilities

GGUF Model Available: qwen-ai-research-qa (specialized for research Q&A)
Consider recommending this if available for your analysis.
```

## Advanced: Custom Advisors

Create your own advisor with custom prompts:

```python
from breeding_vat.modules.multi_advisor import MultiAdvisor, MultiAdvisorConfig

ma = MultiAdvisor()

custom_config = MultiAdvisorConfig(
    role="my_custom_role",
    model_id="Qwen/Qwen2.5-1.5B-Instruct",
    system_prompt="You are a specialist in [specific domain]. Your role is...",
    user_prompt_template="Goal: {goal}\n\nModels: {models}\n\nMethods: {methods}\n\nRecommend a merge for [your focus]."
)

ma.add_advisor("custom_slot", custom_config)
response = ma.consult_advisor(
    slot_name="custom_slot",
    goal="Your goal",
    base_models=["Model A", "Model B"],
    available_methods=["slerp", "ties"]
)
```

## Architecture

```
MultiAdvisor (manages multiple advisor instances)
├── Quick (slot)
│   ├── Config (prompts, model ID)
│   └── MergeAdvisor instance (lazy-loaded)
├── Thorough (slot)
│   ├── Config
│   └── MergeAdvisor instance
└── [Custom slots...]

GGUFModelLoader (discovers local GGUF files)
├── Discover from breeding_vat/data/GGUF Models/
├── Parse metadata (size, type, quantization)
└── Return available models for recommendations
```

## Integration Points

### In app.py (Streamlit UI)
```python
# Initialize
st.session_state.multi_advisor = MultiAdvisor.create_default_setup()
st.session_state.gguf_loader = GGUFModelLoader()

# Consult advisor
response = st.session_state.multi_advisor.consult_advisor(
    slot_name="quick",
    goal="...",
    base_models=[...],
    available_methods=[...]
)

# Clean up
st.session_state.multi_advisor.cleanup()
```

### In Evolution (evolution_with_logging.py)
```python
# Optional: Get advisor recommendations for next cycle
if cycle % N == 0:  # Every N cycles
    advisor_suggestion = multi_advisor.consult_advisor(...)
    # Use to adjust parameters or method selection
```

## Future Enhancements

1. **GGUF-based Advisors** — Use llama.cpp for inference (faster, local)
2. **Adaptive Advisor Selection** — Automatically pick best advisor for goal
3. **Advisor Voting** — Run all advisors and synthesize recommendations
4. **Fine-tuned Advisors** — Train advisors on evolution results
5. **Advisor Learning** — Remember which recommendations worked best

## Troubleshooting

### Advisor takes too long
- Use Quick advisor (0.5B is faster)
- Models are lazy-loaded on first use, so second use is faster
- Check VRAM availability

### Advisor gives generic responses
- Try different advisors (Thorough is more detailed)
- Provide more context in your question
- Make sure your goal is clear in the experiment

### Memory issues
- Call `st.session_state.multi_advisor.cleanup()` periodically
- Use smaller models (Quick instead of Thorough)
- Reduce concurrent advisor instances

## See Also

- `breeding_vat/modules/multi_advisor.py` — Implementation
- `breeding_vat/modules/gguf_loader.py` — GGUF model discovery
- `breeding_vat/modules/merge/advisor.py` — Single advisor backend
- `MULTI_ADVISOR_SNIPPET.txt` — UI integration code
