
import sys, json, math, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path, output_path = sys.argv[1], sys.argv[2]

try:
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype="auto", device_map="auto"
    )
    model.eval()

    # Simple in-memory test corpus so we don't need datasets lib
    texts = [
        "The quick brown fox jumps over the lazy dog and runs away.",
        "Machine learning models are trained on large datasets to learn patterns.",
        "The capital of France is Paris, a city famous for the Eiffel Tower.",
        "In mathematics, a prime number is divisible only by one and itself.",
        "Python is a high-level programming language known for its readability.",
        "The human brain contains approximately 86 billion neurons connected by synapses.",
        "Climate change is driven primarily by greenhouse gas emissions from human activity.",
        "The speed of light in a vacuum is approximately 299,792 kilometres per second.",
        "Natural language processing enables computers to understand and generate text.",
        "Photosynthesis converts carbon dioxide and water into glucose using sunlight.",
    ] * 5  # 50 samples

    total_loss, n = 0.0, 0
    for text in texts:
        try:
            inputs = tok(
                text, return_tensors="pt", max_length=256, truncation=True
            ).to(model.device)
            with torch.no_grad():
                loss = model(**inputs, labels=inputs["input_ids"]).loss.item()
            if not (math.isnan(loss) or math.isinf(loss)):
                total_loss += loss
                n += 1
        except Exception:
            pass

    if n == 0:
        result = {"perplexity": 9999.0, "passed": False, "samples": 0,
                  "reason": "all samples failed"}
    else:
        ppl = math.exp(total_loss / n)
        result = {
            "perplexity": round(ppl, 2),
            "passed": ppl < 1000.0,
            "samples": n,
            "reason": f"perplexity={ppl:.1f}",
        }

except Exception as e:
    result = {"perplexity": 9999.0, "passed": False, "samples": 0,
              "reason": f"model load failed: {e}"}

with open(output_path, "w") as f:
    json.dump(result, f)
