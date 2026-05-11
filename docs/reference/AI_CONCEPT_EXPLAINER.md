# AI Concept Explainer: Data-Focused Reference

Condensed facts on broader LLM concepts for 0.8B models.

## 🏗️ Model Architectures
- **Transformer**: Standard decoder-only (GPT style). Uses Multi-Head Attention (MHA).
- **MoE (Mixture of Experts)**: Only activates a subset of weights (experts) per token. High VRAM, fast inference.
- **Qwen 2.5**: Modern architecture using RoPE (Rotary Positional Embeddings) and SwiGLU activations.

## 🔢 Merging Theory
- **SLERP**: Interpolates weights on a hypersphere. Prevents "average-out" blurring of features.
- **TIES**: Resolves "parameter interference" by trimming small values and selecting a consensus direction.
- **DARE**: Rescales weights after random dropping to maintain model variance.
- **Task Arithmetic**: Treats model finetuning as a "task vector". Result = Base + (Model - Base).

## 📊 Evaluation Metrics
- **HellaSwag**: Commonsense reasoning (completing sentences).
- **ARC (Challenge)**: Grade-school science questions. Tests hard reasoning.
- **MMLU**: Massive Multitask Language Understanding. 57 subjects.
- **Perplexity (PPL)**: Measures how "surprised" a model is by text. Lower is better.

## 💾 Quantization
- **GGUF**: Best for CPU/Mac. Supports k-quants.
- **EXL2**: High speed on NVIDIA GPUs.
- **4-bit (bitsandbytes)**: Standard for VRAM-constrained loading.

## 🧬 Evolution Terms
- **Lineage**: The "family tree" of a model.
- **Culling**: Deleting low-performing models to save space.
- **Mutation**: Small changes to merge weights or layer selections.
