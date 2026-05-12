# Best Bang for Buck: 20+ Pipeline Revolutions

Densely packed, data-focused improvements for VRAM reduction, speed increases, and capability boosts.

## 🚀 Implemented / Super Easy Wins (Toggles)

| Feature | Impact | Category | Implementation Status |
|---------|--------|----------|-----------------------|
| **Low CPU Memory** | Dramatic RAM savings (avoids loading full model in host RAM) | VRAM | ✅ [Implemented] |
| **Lazy Unpickle** | Faster loading, lower memory spikes | Speed/VRAM | ✅ [Implemented] |
| **Copy Tokenizer** | Ensures offspring inherits parent's specialized vocabulary | Capability | ✅ [Implemented] |
| **Trust Remote Code** | Required for newer architectures (Qwen2.5, etc.) | Capability | ✅ [Implemented] |
| **Safetensors Only** | Prevents loading heavy .bin files if .safetensors exist | VRAM/Security| ⏱️ [Available Flag] |
| **Write Model Card** | Auto-generates lineage metadata in model folder | Documentation| ⏱️ [Available Flag] |

## 🧠 Efficiency & Speed (Lean Libraries)

1. **Unsloth Integration**: Replace standard PEFT for 2x faster LoRA training and 70% less VRAM.
2. **Flash Attention 2**: Force-enable in merge/eval for 3-5x speedup on Ampere+ GPUs.
3. **vLLM for Eval**: Swap `lm-eval-harness` default backend for vLLM to increase benchmark throughput by 10x.
4. **BitsAndBytes 4-bit**: Toggle 4-bit loading for the Advisor model to free up ~1.5GB VRAM.
5. **FastChat Templates**: standardizing conversation templates for offspring to improve out-of-the-box performance.
6. **Weight Streaming**: Stream weights directly from disk to GPU during eval (avoid host RAM bottleneck).
7. **Xformers**: Memory-efficient attention for older GPUs (pre-Ampere).
8. **KV Cache Quantization**: Reduce VRAM usage during long context evaluations by 2-4x.

## 🛠️ Advanced Capability & Customization

9. **LoRA Merging**: Merge LoRA adapters instead of full weights for near-instant "mini-merges".
10. **Activation Shifting**: Tweak model biases post-merge to recover reasoning lost during weight averaging.
11. **DPO-Lite**: Use a tiny (100-sample) dataset for 5-minute DPO "vibe alignment" after a merge.
12. **SAE Feature Steering**: Use discovered SAE features to "clamp" specific behaviors during the merge.
13. **Dynamic Pruning**: Auto-remove layers with zero variance during the "Evolution" cull phase.
14. **Token Merging (ToMe)**: Merge redundant tokens during inference/eval to boost speed by 2x.
15. **Quantization-Aware Merging**: Merge models in their quantized state (GGUF/EXL2) to avoid dequantization cycles.
16. **Layer-wise Offloading**: Execute merge block-by-block on CPU if VRAM is < 8GB.

## 📈 Evaluation & Scanning

17. **Perplexity Vibe-Check**: Use 50 samples from WikiText for a 10-second "sanity check" before full eval.
18. **Hallucination Scanner**: Add a tiny "TruthfulQA" subset to every evolution cycle.
19. **Context Compression**: Evaluate models on compressed prompts to test reasoning density.
20. **Self-Correction Loop**: Let the 0.8B advisor read benchmark failures and auto-generate the "Mutation" recipe.

## ⚡ Hardware Optimizations

21. **CUDA Graphs**: Capture merge operations as graphs for 10-15% lower latency.
22. **P2P Transfers**: Use Peer-to-Peer GPU copies if multiple GPUs are detected.
23. **CPU Merging (Vectorized)**: Use Intel MKL/OpenBLAS for high-speed CPU merging when VRAM is full.
