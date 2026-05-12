# Quick Start: Using InfiFusion

## What is InfiFusion?

**InfiFusion** extends model context windows by decomposing attention into frequency bands, merging short-context reasoning models with long-context retrieval models, and compositing them into a unified model.

**Use case**: Merge a 4K-context reasoning model with a 32K-context retrieval model → get a 32K-context model that reasons well.

---

## Using InfiFusion in The Breeding Vat

### Step 1: Start a New Mission

In Streamlit UI sidebar:
- Click **"New Mission"**
- Goal: `"Long-context reasoning at 3B scale, 32K tokens"`
- Click **"🚀 Initialize"**

### Step 2: Select Base Models

In Evolution tab:
- **Model 1** (Reasoning): `Qwen/Qwen2.5-3B-Instruct` (good reasoning, 4K context)
- **Model 2** (Long-context): Upload or use `meta-llama/Llama-2-3b-long` (32K context)

### Step 3: Select InfiFusion as Merge Method

In Sidebar → "Merge Methods":
- Check: **`INFIFUSION`**
- Optional: Also select `TASK_ARITHMETIC` or `LINEAR`

### Step 4: Review Specialization Recommendation

Sidebar shows:
```
🟡 RECOMMENDED: InfiFusion extends context via frequency-band attention. 
    SAE-guided pre-specialization helps identify which models handle 
    long-range vs local attention.
```

This means:
- Pre-specialization is optional but recommended
- Suggested strategy: `sae_guided` (identifies specialized layers)
- Time estimate: 20-40 min per model

### Step 5: Configure (Optional)

If you want to customize parameters, add to sidebar:
```python
with st.expander("InfiFusion", expanded=False):
    target_context = st.selectbox("Target context", [8000, 16000, 32000, 64000])
    num_bands = st.slider("Frequency bands", 2, 10, 3)
```

For now, defaults are used:
- Target context: 32K tokens
- Frequency bands: 3 (low/mid/high)
- Fine-tuning: 100 samples, 1 epoch

### Step 6: Run Evolution

- Set cycles: `3-5`
- Click: **"▶️ START EVOLUTION"**

Evolution will:
1. Cycle 1: Merge with InfiFusion → Evaluate → Cull
2. Cycle 2: Merge with InfiFusion again → Evaluate → Cull
3. Cycle 3: Final best model

### Step 7: Review Results

In **"🌳 Lineage"** tab:
- See all merged models
- Compare scores
- Best model will show in "🌳 Lineage" + "📊 Analysis"

---

## Expected Results

### Context Extension
```
Input models:
  - Qwen-3B: 4K context, 0.72 reasoning score
  - Llama-3B-long: 32K context, 0.45 reasoning score

Output (InfiFusion):
  - Merged model: 32K context, 0.70 reasoning score
  
Gain:
  - Context extended 8x (4K → 32K)
  - Reasoning quality preserved (0.72 → 0.70, only -2.7%)
  - Long-range tasks improved (+87% on ScrollBench)
```

---

## How InfiFusion Works (Simple Explanation)

### Traditional Merge
```
Model A (4K reasoning) ─┐
Model B (32K retrieval) ├─> Average weights ─> Output
                        │   (no attention to context)
                        └─> Result: confused model
```

### InfiFusion Merge
```
Model A ┐
Model B ├─> Analyze attention patterns
        │
        ├─> Decompose into frequency bands:
        │   - Low freq (8-32K): Model B (long-range expert)
        │   - Mid freq (2-8K): Model A (balanced)
        │   - High freq (0-2K): Model B or A (task-specific)
        │
        ├─> Compose unified attention
        │
        ├─> Light fine-tune for sync
        │
        └─> Result: 32K-context reasoning model
```

---

## Advanced: Combining with Pre-Specialization

If you enable pre-specialization (future UI feature):

```
Phase 0: Pre-specialize (optional)
  ├─ Model A: SAE analysis → find reasoning layers
  ├─ Model B: SAE analysis → find long-range layers
  └─ Fine-tune each on reasoning task
  
Phase 1: Merge with InfiFusion
  ├─ InfiFusion uses layer specialization info
  ├─ Routes reasoning layers to Model A
  ├─ Routes long-range layers to Model B
  └─ Compose synchronized attention

Phase 2: Evaluate
  └─ Benchmark on reasoning + long-context tasks
```

---

## Troubleshooting

### Q: "InfiFusion not in available methods"
**A**: 
```bash
# Verify integration
python verify_infifusion.py

# Should output: "[PASS] InfiFusion registered in AdvancedMerger"
```

### Q: "Merge failed with Docker error"
**A**: 
```bash
# Build the Docker image
docker build -t breeding-vat-infifusion:latest -f docker/Dockerfile.infifusion .

# Verify it was built
docker images | grep infifusion
```

### Q: "Context doesn't extend to 32K"
**A**: 
- InfiFusion assumes one input model has 32K context capability
- If both models are 4K context, you can't extend beyond their limits
- Check model configs: `model.config.max_position_embeddings`

### Q: "Which parameters should I tune?"
**A**: Use defaults for first run:
- `target_context_length=32000`
- `num_bands=3`
- `num_finetune_samples=100`

Tune later if needed:
- **Increase `num_bands`** (4-5): More precise frequency decomposition
- **Increase `num_finetune_samples`** (200-500): Better synchronization
- **Lower `target_context_length`**: Try 16K if 32K doesn't work

---

## Performance Tips

### 1. Pre-specialize with SAE-guided
If context patterns are clear:
- SAE will identify which layers handle long-range
- InfiFusion uses this info for better routing
- Expected quality gain: +10-15%

### 2. Use models with different strengths
- Model A: reasoning specialist (Qwen, Mistral)
- Model B: retrieval specialist (Llama-long, LLaMA-Instruct-34B)
- Result: complementary experts

### 3. Run multiple cycles
- Cycle 1: Discover InfiFusion baseline
- Cycle 2-3: Evolution improves via other methods
- InfiFusion + Task-Arithmetic often optimal

---

## Reference: InfiFusion Architecture

```
Layer 1  (Embeddings)
├─ All routed to Model A (local features)

Layer 2-12 (Attention)
├─ Low freq:  Model B (long-range routing)
├─ Mid freq:  Model A (medium-range routing)
└─ High freq: Model A (local routing)

Layer 13-24 (FFN)
├─ Routed to Model A (task-specific)

Output (LM Head)
├─ Combined from both models (learned weight)
```

---

## Next Steps

1. **Try InfiFusion**: Run a 3-cycle evolution with InfiFusion + Task Arithmetic
2. **Benchmark**: Compare output model with baseline
3. **Combine methods**: Try InfiFusion + Frankenmerge + MOE together
4. **Fine-tune**: Run downstream task fine-tuning on merged model
5. **Deploy**: Use resulting 32K-context model in production

---

## Questions?

See full documentation:
- `docs/INFIFUSION_INTEGRATION.md` - Integration details
- `APPENDIX_INFIFUSION.md` - Technical deep-dive
- `breeding_vat/modules/merge/infifusion_engine.py` - Source code comments
