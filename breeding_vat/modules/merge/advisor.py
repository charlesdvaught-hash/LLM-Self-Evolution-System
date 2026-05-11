import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

class MergeAdvisor:
    def __init__(self, model_id="Qwen/Qwen3.5-0.8B-Instruct"):
        self.model_id = model_id
        self.tokenizer = None
        self.model = None

    def load(self):
        if self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype="auto",
                device_map="auto"
            )

    def generate_recipe(self, goal, available_models, available_methods):
        self.load()
        prompt = f"""You are the Breeding Vat Advisor. Your goal is to design a model merging recipe.
Goal: {goal}
Available Models: {available_models}
Available Methods: {available_methods}

Suggest a 3-step waterfall evolution plan. For each step, specify the merge method, the models involved, and why this helps the goal.
Keep it concise.
"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in LLM merging and evolution."},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response

if __name__ == "__main__":
    # Test script (will try to download model if run)
    # advisor = MergeAdvisor()
    # print(advisor.generate_recipe("Improve logic", ["M1", "M2"], ["SLERP", "TIES"]))
    pass
