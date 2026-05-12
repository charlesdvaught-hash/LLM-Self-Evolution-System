# Specialized Model Collections Guide

## Available Models

You now have **7 specialized models** ready for evolution:

### SAE Research Models (Interpretability)
```
Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50    # Lower sparsity, more features
Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_100   # Higher sparsity, concentrated features
```
**Use for**: Understanding what models learn (SAE analysis)
**Size**: 2B each
**Special**: Designed for sparse autoencoder research

### Reasoning Models (Enhanced Thinking)
```
deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B  # Reasoning distilled from R1
alpha-ai/qwen2.5-reason-thought-lite        # Chain-of-thought enhanced
```
**Use for**: Merging better reasoning capabilities
**Size**: 1.5B each
**Special**: Trained with reasoning/thought process

### Code Specialist
```
bigatuna/Qwen3-1.7B-Sushi-Coder             # Code generation optimized
```
**Use for**: Evolving code generation
**Size**: 1.7B
**Special**: Fine-tuned for programming tasks

### Math Specialist
```
DavidOKB/MathThink-Qwen-3.5-4B              # Math reasoning focused
```
**Use for**: Evolving math/logic reasoning
**Size**: 4B
**Special**: Math-specific fine-tuning

### General Baseline
```
Qwen/Qwen2.5-0.5B-Instruct                  # Smallest baseline
Qwen/Qwen2.5-1.5B-Instruct                  # Main baseline
```
**Use for**: Stable baseline merges
**Size**: 500M, 1.5B
**Special**: Production-tested

### Diverse Capabilities
```
microsoft/Phi-3-mini-4k-instruct            # Microsoft's compact
OusiaResearch/Aureth-4B-Qwen3.5             # Instruction-tuned variant
```
**Use for**: Diverse merge experiments
**Size**: 3.8B, 4B
**Special**: Different architectures/training

## Download Presets

### Quick Commands

```powershell
# Show everything
python scripts/download_models.py --info

# Show presets
python scripts/download_models.py --presets

# Show categories
python scripts/download_models.py --categories

# Download recommended (default - best for 12GB VRAM)
python scripts/download_models.py

# Download by preset
python scripts/download_models.py --preset reasoning
python scripts/download_models.py --preset code
python scripts/download_models.py --preset math
python scripts/download_models.py --preset research
python scripts/download_models.py --preset full

# Download by category
python scripts/download_models.py --category sae
python scripts/download_models.py --category reasoning
python scripts/download_models.py --category code
python scripts/download_models.py --category math

# Download specific models
python scripts/download_models.py --models "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" "bigatuna/Qwen3-1.7B-Sushi-Coder"
```

## Available Presets

| Preset | Models | Size | Use Case |
|--------|--------|------|----------|
| **baseline** | Qwen 0.5B + 1.5B | 4 GB | Safe baseline |
| **reasoning** | Qwen 0.5B + 2 reasoning | 7 GB | Better reasoning |
| **code** | Qwen 1.5B + coder | 5 GB | Code generation |
| **math** | Qwen 0.5B + math 4B | 5 GB | Math reasoning |
| **research** | 2 SAE models | 4 GB | SAE analysis |
| **recommended** | baseline + reasoning + code | 12 GB | **Best for your setup** |
| **full** | All 13 models | 50+ GB | Comprehensive research |

## Recommended for Your Setup

### Best All-Rounder: "recommended" Preset

```powershell
python scripts/download_models.py --preset recommended
```

**Downloads**:
- Qwen/Qwen2.5-0.5B-Instruct (baseline)
- Qwen/Qwen2.5-1.5B-Instruct (main)
- deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B (reasoning)
- bigatuna/Qwen3-1.7B-Sushi-Coder (code)

**Why this combo**:
- ✓ Covers baseline, reasoning, and code
- ✓ Fits in 12GB VRAM + 8GB RAM
- ✓ Diverse enough for interesting merges
- ✓ Fast iteration cycles
- ✓ Good merge results (2-4B range)

## Evolution Scenarios

### Scenario 1: Evolve Better Reasoning

```
Preset: --preset reasoning

Base Models:
  Qwen/Qwen2.5-0.5B-Instruct
  deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
  alpha-ai/qwen2.5-reason-thought-lite

Methods: SLERP, TIES

Result: 3-4B reasoning models
```

**Expected**: Merged models inherit reasoning traits

### Scenario 2: Evolve Code Generation

```
Preset: --preset code

Base Models:
  Qwen/Qwen2.5-1.5B-Instruct
  bigatuna/Qwen3-1.7B-Sushi-Coder

Methods: SLERP, DARE

Result: 2-3B code-capable models
```

**Expected**: Merged models with code ability + general knowledge

### Scenario 3: SAE Research

```
Preset: --preset research

Base Models:
  Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50
  Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_100

Methods: SLERP

Result: 2B models with different sparsity
```

**Expected**: Compare SAE feature structure across sparsity levels

### Scenario 4: Everything (If You Have Storage)

```
Preset: --preset full

Download all 13 models
Explore all capability combinations
```

**Warning**: Needs 50+ GB storage

## Model Compatibility Matrix

| Model A | Model B | Merge Safety | VRAM Peak | Notes |
|---------|---------|--------------|-----------|-------|
| Qwen 0.5B | Qwen 1.5B | ✓ High | 6 GB | Same architecture |
| Qwen 0.5B | DeepSeek-R1 | ✓ High | 6 GB | Both Qwen-based |
| Qwen 1.5B | Coder | ✓ High | 6 GB | Same architecture |
| Qwen 1.5B | Phi-3 | ⚠️ Medium | 8 GB | Different arch |
| DeepSeek-R1 | Coder | ✓ High | 6 GB | Both Qwen-based |
| SAE 2B L0_50 | SAE 2B L0_100 | ✓ High | 4 GB | Same model |
| Math 4B | Coder 1.7B | ⚠️ Low | 8 GB | Different sizes |

## Expected Merge Quality

### High Confidence Merges (Same Architecture)
```
Qwen + Qwen variants
DeepSeek-R1 + other Qwen
SAE models + SAE models
Result: Stable, predictable
```

### Medium Confidence Merges (Similar Size)
```
Qwen 1.5B + Phi-3 mini
Coder + Reasoning models
Result: Works, sometimes interesting
```

### Lower Confidence Merges (Different Sizes)
```
Qwen 0.5B + Math 4B
Phi-3 + Qwen 1.5B
Result: May have issues, unpredictable
```

## SAE Model Special Usage

### Comparing Sparsity Levels

```powershell
# Download both SAE models
python scripts/download_models.py --category sae

# Analyze both
python scripts/sae_self_analysis.py \
  --model "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50" \
  --output sae_l0_50.json

python scripts/sae_self_analysis.py \
  --model "Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_100" \
  --output sae_l0_100.json

# Compare: Which has better feature concentration?
```

### What L0 Means

- **L0_50**: Sparsity=50 average features active per input
- **L0_100**: Sparsity=100 average features active per input

**L0_50**: Sparser, more specialized features
**L0_100**: Less sparse, more redundancy but richer

**Merge insight**: Do merges benefit from sparse or redundant representations?

## Storage Planning

| Scenario | Models | Disk | Time to Download |
|----------|--------|------|------------------|
| Baseline | 2 | 4 GB | 5 min |
| Recommended | 4 | 12 GB | 15 min |
| Category (sae) | 2 | 4 GB | 5 min |
| Category (reasoning) | 2 | 5 GB | 8 min |
| Category (code) | 1 | 3 GB | 4 min |
| Full | 13 | 50+ GB | 60+ min |

## Tips for Your 12GB VRAM

### ✓ Safe Combinations
```
Qwen 0.5B + Qwen 1.5B        → Merge to 2B ✓
Qwen 1.5B + DeepSeek-R1      → Merge to 2B ✓
DeepSeek-R1 + Coder          → Merge to 2B ✓
SAE L0_50 + SAE L0_100       → Merge to 2B ✓
```

### ⚠️ Risky Combinations
```
Qwen 1.5B + Math 4B          → Merge to 3B (8GB peak)
Phi-3 mini + Coder           → Merge to 3B (8GB peak)
```

### ✗ Won't Work
```
Qwen 1.5B + Aureth 4B        → 5B result (16GB needed)
Phi-3 mini + Math 4B         → 4B result (12GB+ peak)
```

## Next Steps

1. **Choose a preset**:
   ```powershell
   python scripts/download_models.py --preset recommended
   ```

2. **Or mix and match**:
   ```powershell
   python scripts/download_models.py \
     --models "Qwen/Qwen2.5-1.5B-Instruct" \
             "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
   ```

3. **Analyze baseline**:
   ```powershell
   python scripts/sae_self_analysis.py \
     --model "Qwen/Qwen2.5-1.5B-Instruct" \
     --samples 50 \
     --output baseline.json
   ```

4. **Run evolution**:
   ```
   run.bat → Waterfall Pipeline → Select base models → RUN EVOLUTION
   ```

5. **Analyze results**:
   ```powershell
   python scripts/sae_self_analysis.py \
     --model "breeding_vat/data/merged_models/mutant_c0_p0_o0" \
     --compare "Qwen/Qwen2.5-1.5B-Instruct"
   ```

You now have a rich ecosystem for targeted model evolution!
