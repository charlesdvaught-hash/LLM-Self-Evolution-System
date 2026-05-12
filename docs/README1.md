---
license: other
license_name: qwen
license_link: https://huggingface.co/Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50/blob/main/LICENSE
language:
- en
tags:
- sparse-autoencoder
- sae
- mechanistic-interpretability
- interpretability
- qwen-scope
base_model: Qwen/Qwen3.5-2B
---

## Qwen-Scope: Decoding Intelligence, Unleashing Potential

![Overview](https://qianwen-res.oss-cn-beijing.aliyuncs.com/qwen-scope/Figures/overview.png)

We are excited to introduce Qwen-Scope, an interpretability module trained on the Qwen3 and Qwen3.5 series models. Specifically, we integrated and trained Sparse Autoencoders (SAEs) within Qwen’s hidden layers. By implementing sparsity constraints, we can automatically extract data features that are highly decoupled, low-redundancy, and significantly more interpretable. Qwen-Scope can be used not only to analyze the internal mechanisms of Qwen’s behavior but also holds immense potential for model optimization. Application scenarios include steerable inference control, evaluation sample distribution analysis and comparison, data classification and synthesis, and model training and optimization. See our [technical report](https://qianwen-res.oss-accelerate.aliyuncs.com/qwen-scope/Qwen_Scope.pdf) for more details.

## Model Details

| Property | Value |
|---|---|
| Base model | [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) |
| SAE width (`d_sae`) | 32768 |
| Hidden size (`d_model`) | 2048 |
| Expansion factor | 16× |
| Top-K | 50 |
| Hook point | Residual stream |
| Layers covered | 0 – 23 (24 layers total) |
| File format | PyTorch `.pt` dict |

## Architecture

This is a **TopK SAE** — at each forward pass, exactly **50** features are kept non-zero.

Each checkpoint file `layer{n}.sae.pt` is a Python `dict` with four tensors:

| Key | Shape | Description |
|---|---|---|
| `W_enc` | `(32768, 2048)` | Encoder weight matrix |
| `W_dec` | `(2048, 32768)` | Decoder weight matrix |
| `b_enc` | `(32768,)` | Encoder bias |
| `b_dec` | `(2048,)` | Decoder bias |

## Files

This repository contains one SAE checkpoint per transformer layer (layers 0–23):

```
layer0.sae.pt
layer1.sae.pt
...
layer23.sae.pt
```

## Feature Activation Extraction

End-to-end demo: run the base LLM, hook the residual stream at a chosen layer, and extract sparse SAE feature activations.
For most of the situations, using SAEs trained on base models to explore the internal process of post-training checkpoints is also reasonable.

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ── 1. Load base model ────────────────────────────────────────────────────────
model_name = "Qwen/Qwen3.5-2B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
model.eval()

# ── 2. Load SAE for a target layer ───────────────────────────────────────────
LAYER = 0  # choose any layer in 0–23
sae = torch.load(f"layer{LAYER}.sae.pt", map_location="cpu")
W_enc = sae["W_enc"]  # (32768, 2048)
b_enc = sae["b_enc"]  # (32768,)

def get_feature_acts(residual: torch.Tensor) -> torch.Tensor:
    """residual: (..., 2048) → sparse feature activations (..., 32768)"""
    pre_acts = residual @ W_enc.T + b_enc
    topk_vals, topk_idx = pre_acts.topk(50, dim=-1)
    acts = torch.zeros_like(pre_acts)
    acts.scatter_(-1, topk_idx, topk_vals)
    return acts

# ── 3. Hook residual stream after the target transformer layer ────────────────
captured = {}

def _hook(module, input, output):
    hidden = output[0] if isinstance(output, tuple) else output
    captured["residual"] = hidden.detach().cpu()

hook = model.model.layers[LAYER].register_forward_hook(_hook)

# ── 4. Forward pass ───────────────────────────────────────────────────────────
text = "The capital of France is"
inputs = tokenizer(text, return_tensors="pt")
with torch.no_grad():
    model(**inputs)
hook.remove()

# ── 5. Extract feature activations ───────────────────────────────────────────
residual = captured["residual"]               # (1, seq_len, 2048)
feature_acts = get_feature_acts(residual)     # (1, seq_len, 32768)

# Inspect active features for the last token
last_token_acts = feature_acts[0, -1]         # (32768,)
active_idx = last_token_acts.nonzero(as_tuple=True)[0]
print(f"Active features : {active_idx.tolist()}")
print(f"Feature values  : {last_token_acts[active_idx].tolist()}")
```

## Gradio Demo

We also provide a gradio demo `app.py`. You can run it locally:
```
python app.py \
    --model Qwen/Qwen3.5-2B \
    --model-name-sae-trained-from qwen3.5-2b-base \
    --model-name-analyzing-now qwen3.5-2b \
    --sae-path Qwen/SAE-Res-Qwen3.5-2B-Base-W32K-L0_50 \
    --top-k 50 \
    --num-layers 24 \
    --sae-width 32768 \
    --d-model 2048 \
    --server-port 7860
```

## Caution
It is strictly prohibited to use interpretability tools for non-scientific research purposes to interfere with model capabilities, or to fabricate, generate, and disseminate harmful information that violates public order, good morals, and socialist core values, including pornographic, violent, discriminatory, or incendiary content. Violators will have their authorization automatically terminated and shall bear all legal liabilities arising therefrom. The right of final interpretation of this statement belongs to the project owner.

## Citation

If you use these SAEs in your research, please cite:


```bibtex
@misc{qwen_scope,
    title = {{Qwen-Scope}: Turning Sparse Features into Development Tools for Large Language Models},
    url = {https://qianwen-res.oss-accelerate.aliyuncs.com/qwen-scope/Qwen_Scope.pdf},
    author = {{Qwen Team}},
    month = {April},
    year = {2026}
}
```
