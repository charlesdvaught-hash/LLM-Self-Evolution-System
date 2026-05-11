import os
import torch
import logging
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset

logger = logging.getLogger("TrainEngine")

class TrainEngine:
    def __init__(self, output_dir="breeding_vat/data/merged_models"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def run_lora_fine_tuning(self, model_path, output_name, dataset_path=None, num_train_steps=100):
        """
        Performs lightweight LoRA fine-tuning.
        
        Args:
            model_path: Path or HF model ID
            output_name: Output model name
            dataset_path: Path to dataset or HF dataset ID
            num_train_steps: Number of training steps
        """
        logger.info(f"Starting LoRA fine-tuning for {model_path}...")
        
        try:
            # Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            tokenizer.pad_token = tokenizer.eos_token
            
            # Configure LoRA
            config = LoraConfig(
                r=8,
                lora_alpha=16,
                target_modules=["q_proj", "v_proj"],
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM"
            )
            model = get_peft_model(model, config)
            
            # Load dataset
            if dataset_path:
                try:
                    dataset = load_dataset(dataset_path)
                    logger.info(f"Loaded dataset from {dataset_path}")
                except Exception as e:
                    logger.warning(f"Failed to load dataset {dataset_path}: {e}. Using dummy data.")
                    # Dummy dataset for demo
                    dataset = self._create_dummy_dataset(tokenizer, size=100)
            else:
                dataset = self._create_dummy_dataset(tokenizer, size=100)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=os.path.join(self.output_dir, f"{output_name}_checkpoints"),
                num_train_epochs=1,
                max_steps=num_train_steps,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=4,
                learning_rate=1e-4,
                bf16=torch.cuda.is_available(),
                logging_steps=10,
                save_strategy="steps",
                save_steps=50,
            )
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset["train"],
                tokenizer=tokenizer,
            )
            
            # Train
            trainer.train()
            
            # Save
            output_path = os.path.join(self.output_dir, output_name)
            model.save_pretrained(output_path)
            tokenizer.save_pretrained(output_path)
            logger.info(f"Model saved to {output_path}")
            
            # Cleanup
            del model
            del trainer
            torch.cuda.empty_cache()
            
            return output_path
            
        except Exception as e:
            logger.error(f"LoRA training failed: {e}")
            raise
    
    def _create_dummy_dataset(self, tokenizer, size=100):
        """Create a dummy dataset for testing."""
        texts = ["Hello, this is a test."] * size
        
        def tokenize_fn(batch):
            return tokenizer(batch, max_length=128, truncation=True, padding="max_length")
        
        from datasets import Dataset
        dataset = Dataset.from_dict({"text": texts})
        dataset = dataset.map(
            lambda x: tokenize_fn(x["text"]),
            batched=True,
            remove_columns=["text"]
        )
        
        # Rename to match Trainer expectations
        dataset = dataset.rename_column("input_ids", "input_ids")
        
        return {"train": dataset}
