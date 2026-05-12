import sqlite3
import json
import logging
from datetime import datetime

logger = logging.getLogger("SeedingSystem")

# Data extracted from FusionBench (Arxiv: 2406.03280v3)
FUSIONBENCH_DATA = [
    {
        "name": "FusionBench GPT-2 Historical",
        "goal": "Multi-task text classification (GLUE)",
        "base_models": ["gpt2-cola", "gpt2-mnli", "gpt2-mrpc", "gpt2-qnli", "gpt2-qqp", "gpt2-rte", "gpt2-sst2"],
        "merge_methods": ["simple_average", "fisher", "regmean", "task_arithmetic", "ties"],
        "results": [
            {"method": "simple_average", "score": 0.561, "tasks": {"avg": 0.561}},
            {"method": "fisher", "score": 0.587, "tasks": {"avg": 0.587}},
            {"method": "regmean", "score": 0.688, "tasks": {"avg": 0.688}},
            {"method": "task_arithmetic", "score": 0.700, "tasks": {"avg": 0.700}},
            {"method": "ties", "score": 0.700, "tasks": {"avg": 0.700}}
        ]
    },
    {
        "name": "FusionBench Flan-T5-Large Historical",
        "goal": "Multi-task text-to-text generation (GLUE)",
        "base_models": ["flan-t5-large-cola", "flan-t5-large-mnli", "flan-t5-large-mrpc", "flan-t5-large-qnli", "flan-t5-large-qqp", "flan-t5-large-rte", "flan-t5-large-sst2", "flan-t5-large-stsb"],
        "merge_methods": ["weight_averaging", "task_arithmetic", "ties", "adamerging"],
        "results": [
            {"method": "weight_averaging", "score": 0.865, "tasks": {"avg": 0.865}},
            {"method": "task_arithmetic", "score": 0.873, "tasks": {"avg": 0.873}},
            {"method": "ties", "score": 0.874, "tasks": {"avg": 0.874}},
            {"method": "adamerging", "score": 0.876, "tasks": {"avg": 0.876}}
        ]
    }
]

def seed_database(db_path="breeding_vat/data/breeding.db"):
    """Populate the database with historical results from research papers."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if we already have these experiments
    cursor.execute("SELECT count(*) FROM experiments WHERE status = 'historical'")
    if cursor.fetchone()[0] > 0:
        logger.info("Database already contains historical data. Skipping seeding.")
        conn.close()
        return False

    logger.info(f"Seeding database at {db_path} with FusionBench data...")

    for exp_data in FUSIONBENCH_DATA:
        # 1. Insert Experiment
        cursor.execute(
            "INSERT INTO experiments (name, goal, base_models, merge_methods, status, best_score) VALUES (?, ?, ?, ?, ?, ?)",
            (
                exp_data["name"],
                exp_data["goal"],
                json.dumps(exp_data["base_models"]),
                json.dumps(exp_data["merge_methods"]),
                "historical",
                max(r["score"] for r in exp_data["results"])
            )
        )
        exp_id = cursor.lastrowid

        # 2. Insert Models
        for i, res in enumerate(exp_data["results"]):
            model_name = f"fusionbench_{res['method']}_{exp_id}_{i}"
            cursor.execute(
                """INSERT INTO models
                   (experiment_id, name, base_models, method, benchmark_results, status, cycle_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    exp_id,
                    model_name,
                    json.dumps(exp_data["base_models"]),
                    res["method"],
                    json.dumps({"avg_score": res["score"], "tasks": res["tasks"], "source": "FusionBench Paper"}),
                    "completed",
                    0
                )
            )
            model_id = cursor.lastrowid

            # Update best_model_id if this is the winner
            if res["score"] == max(r["score"] for r in exp_data["results"]):
                cursor.execute("UPDATE experiments SET best_model_id = ? WHERE id = ?", (model_id, exp_id))

    conn.commit()
    conn.close()
    logger.info("Seeding complete.")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
