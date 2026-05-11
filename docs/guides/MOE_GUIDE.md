# Frankenstein MoE Models - Interesting Combinations

## Novel MoE Models to Consider

### Small Efficient MoE Models (Good for Merging)

#### 1. **Mixtral 8x7B-32K** (Most Compatible)
```
Model: mistralai/Mixtral-8x7B-Instruct-v0.1
Size: ~32B (sparse = ~12.9B active)
Type: Mixture of Experts (8 experts)
Use: Add MoE routing to dense models
Download: Fits with sampling
```
**Why interesting**: 
- Only 1-2 experts active per token (sparse)
- Can merge experts selectively with dense models
- Already benchmarked and stable

#### 2. **Mixtral 8x22B-32K** 
```
Model: mistralai/Mixtral-8x22B-Instruct-v0.1
Size: ~141B (sparse = ~39B active)
Type: Mixture of Experts (8 experts)
Too Large: For your VRAM, but mergeable in pieces
```

#### 3. **Qwen MoE (Emerging)**
```
Model: Qwen/Qwen-4B-MoE or similar
Status: Check HF for availability
Type: Qwen-based MoE
Advantage: Native to your Qwen collection
```

### Micro MoE Models (Small Enough for Direct Use)

#### 4. **DPO-MoE-Llama** (Experimental)
```
Model: Look for "DPO MoE" on HF
Type: Small MoE variants
Size: Often 3-8B
Advantage: DPO-trained (better alignment)
```

#### 5. **Phi MoE Models** (Microsoft)
```
Model: microsoft/Phi-3-medium-MoE or variants
Type: Phi-based MoE
Size: ~25B (sparse)
Status: Check availability
```

### Novel Architecture Models (Interesting Merges)

#### 6. **Hybrid Dense-Sparse Models**
```
Models with mixed dense/sparse layers:
- Some experimental Qwen variants
- Custom research models
- Value: Can expose different reasoning paths
```

#### 7. **Recurrent Transformer Models** (DeepSeek Focus)
```
Model: deepseek-ai/DeepSeek-V2 or similar
Type: Recurrent architecture (different from standard)
Use: Merge with dense for architectural diversity
```

## Frankenstein MoE Combinations for Your Setup

### Combination A: Dense → MoE Distillation
**Strategy**: Merge dense reasoning models, then extract into MoE routing

```
Base:
  Qwen 1.5B (dense reasoning-capable)
  +
  Claude Opus (dense advanced reasoning)
  =
  3B hybrid reasoning (dense)
  
Then:
  Extract expert patterns → MoE structure
  Result: 3B MoE with reasoning-expert focus
```

**Why**: Creates specialized expert routes for reasoning vs general

### Combination B: Code + Reasoning + MoE
**Strategy**: Merge code + reasoning, then add MoE dispatch

```
Base:
  Sushi-Coder (1.7B code)
  +
  DeepSeek-R1 (1.5B reasoning)
  =
  2B code-reasoning hybrid
  
MoE Enhancement:
  Layer-wise MoE gating for task-specific routing
  Experts: [code_expert, reasoning_expert, general_expert]
  Result: 2B MoE that routes to best expert per task
```

**Why**: Code problems need different paths than reasoning problems

### Combination C: SAE Features → MoE Experts
**Strategy**: Use SAE analysis to identify expert dimensions, build MoE

```
Step 1: Analyze merged model with SAE
  - Identify high-importance feature dimensions
  - Find specialized layer concentrations
  
Step 2: Create MoE experts from features
  - Expert 1: High-variance dimensions (reasoning)
  - Expert 2: Specialized layers (code?)
  - Expert 3: Low-variance dimensions (general)
  
Step 3: Train routing network
  - Route tokens to appropriate experts
  
Result: MoE structure derived from learned SAE features
```

**Why**: MoE structure based on what model actually learned

### Combination D: Math + Code + Reasoning MoE
**Strategy**: Three-expert MoE from three specialists

```
Experts:
  Expert A: Math-focused (MathThink 4B)
  Expert B: Code-focused (Sushi-Coder 1.7B)
  Expert C: Reasoning-focused (Claude Opus 4B)
  
Routing:
  Math problem → Expert A
  Code problem → Expert B
  Logic problem → Expert C
  
Challenges:
  - Different sizes (need normalization)
  - Different vocabularies (need alignment)
  - Complex merging
  
Potential:
  - Highly specialized MoE
  - Novel frankenstein architecture
  - Very interesting evolution scenario
```

**Why**: True multi-specialist system

## Research-Grade Frankenstein Ideas

### Idea 1: Emergent MoE from Evolution
```
1. Run evolution on your models
2. SAE analyze top-performing merges
3. Find where different models "specialize"
4. Construct MoE from specialization patterns
5. Results: Data-driven expert identification
```

### Idea 2: Sparse Merge + MoE Gating
```
1. Use DARE sparse merging (already supported)
2. Apply to multiple model pairs separately
3. Create MoE that routes between sparse variants
4. Result: Sparse MoE (ultra-efficient)
```

### Idea 3: Reasoning Path Experts
```
1. Merge DeepSeek-R1 + Claude Opus
2. SAE analyze which layers do reasoning
3. Extract reasoning pathway as expert
4. Create complementary code/general experts
5. Build MoE that can toggle reasoning depth
```

### Idea 4: Adaptive Task-Routing MoE
```
1. Collect your merged models
2. Test each on different task types
3. Identify which perform best at:
   - Math
   - Code
   - Reasoning
   - General knowledge
   - Instruction following
4. Create MoE with task-specific experts
5. Add dynamic router based on input analysis
```

## Technical Considerations for MoE Merging

### Challenge 1: Expert Alignment
```
Problem: Experts from different sources have different vocabularies
Solution:
  - Project to common space before merging
  - Use SAE features as alignment basis
  - Learn alignment layer
```

### Challenge 2: Routing Function
```
Problem: How to decide which expert to use?
Solution Options:
  - Learned router (train on your dataset)
  - Heuristic router (based on input characteristics)
  - SAE-guided router (use important features)
  - Sparse mixture (all experts slightly active)
```

### Challenge 3: Token-Expert Pairing
```
Problem: MoE expects fixed number of tokens per expert
Solution:
  - Load-balancing loss during training
  - Auxiliary loss to encourage diversity
  - Manual expert assignment for experiments
```

## Models to Download & Try

### Tier 1: Easy to Experiment With
```
mistralai/Mixtral-8x7B-Instruct-v0.1
- Already MoE
- Smaller experts than 8x22B
- Can extract individual experts
- Merge with your dense models

Download: ~15GB (sparse routing, can sample)
```

### Tier 2: Research-Grade
```
Experimental models on HF:
- Search: "MoE" + "small" + "-Instruct"
- Search: "expert" + "mixture"
- Look for: Qwen MoE variants
- Look for: Phi MoE variants

Potential finds:
- Custom fine-tuned MoE models
- Research MoE architectures
- Experimental efficient MoE
```

### Tier 3: Custom Candidates
```
Create novel frankenstein by:
1. Taking your best merged model (dense)
2. Analyzing with SAE (find expert dimensions)
3. Manually constructing MoE structure
4. Training routing layer on sample data
5. Result: Custom MoE from evolution
```

## Recommended Experimental Path

### Phase 1: Baseline (This Week)
```
1. Download: mistralai/Mixtral-8x7B-Instruct-v0.1
2. Analyze: SAE features of Mixtral
3. Extract: Individual expert analysis
4. Compare: Experts vs your merged models
```

### Phase 2: Merging (Next)
```
1. Merge: Your best dense model + Mixtral expert
2. Result: Dense-MoE hybrid
3. Test: Does it maintain capabilities?
4. Analyze: SAE of hybrid
```

### Phase 3: Custom MoE (Advanced)
```
1. SAE analyze your top-5 merged models
2. Identify common specializations
3. Build custom MoE from specializations
4. Create routing based on task type
5. Evaluate: Better than single merged model?
```

## Quick Command to Add MoE Models

When you want to download and experiment:

```powershell
# Create MoE experimental preset
python scripts/download_models.py --models \
  "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Or add to existing collection
python scripts/download_models.py --preset recommended

# Then manually add Mixtral
# (for reference/expert extraction)
```

## Documentation Needed

I recommend creating:
- `MOE_MERGING_GUIDE.md` - Theoretical background
- `MOE_EXPERIMENTS.md` - Practical walkthrough
- `MOE_RECIPES.md` - Specific merge configurations

## Questions for You

1. **Interest level**: How interested are you in MoE architecture research?
2. **Storage**: Can you dedicate 20+ GB for MoE experiments?
3. **Compute**: Ready to do training for routing networks?
4. **Focus**: Which MoE type most interesting?
   - Task-routing (math/code/reasoning)
   - Sparse-merge based
   - SAE-feature derived
   - Architectural (dense→MoE transformation)

Would you like me to:
1. Create detailed MoE download recommendations?
2. Write MoE merging guides and recipes?
3. Add MoE preset to download_models.py?
4. Create SAE-to-MoE conversion tooling?
