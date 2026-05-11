# Merge Resources & Large Model Techniques

Data-focused repository of merge info and strategies for low-VRAM hardware.

## 📂 Data Repositories
- **Open LLM Leaderboard**: The primary source for finding "parent" candidates. Filter by size (e.g., 3B, 7B).
- **HuggingFace Merge Tag**: Search `tag:merge` on HF to find thousands of existing recipes to replicate.
- **Model Stock**: Research on using "Model Soup" techniques for zero-shot capability boosts.
- **MergeKit Examples**: The official `cg123/mergekit` repository contains a `examples/` folder with YAML templates.

## 📉 Merging Beyond VRAM (12GB GPU Tips)
1. **Layer-by-Layer CPU Merging**:
   - MergeKit can merge models on CPU by processing one layer at a time.
   - RAM Requirement: ~2x the size of a single layer (e.g., for a 7B model, only ~500MB RAM is active at once).
   - Use flag: `--low-cpu-mem` (now implemented in UI).

2. **Model Sharding**:
   - Save merged models in 1GB shards (`--max-shard-size 1GB`) to ensure they can be loaded for evaluation on 8GB-12GB GPUs.

3. **Disk Offloading (mmap)**:
   - Use `torch.load(..., mmap=True)` to read weights directly from NVMe instead of loading into system RAM.

4. **GGUF Merging**:
   - Merge models in GGUF format using `llama.cpp` tools to avoid high-precision FP16 memory requirements.

## 🔮 Anticipating Success (Merge Prediction)
- **Weight Cosine Similarity**: High similarity between parents usually leads to stable but "boring" merges. Low similarity (diversity) leads to high-risk/high-reward offspring.
- **Fisher Information**: Merging layers with high Fisher information overlap preserves the most "intelligence".
- **Activation Variance**: If parents have similar activation patterns for the same prompt, they are safe to merge.
