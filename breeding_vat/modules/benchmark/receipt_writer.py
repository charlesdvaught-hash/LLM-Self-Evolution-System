import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

GOAL_BENCHMARK_CHANCE_LEVEL = 0.5


class ReceiptWriter:
    def __init__(self, experiment_path: str):
        self.experiment_path = experiment_path
        self.receipts_dir = os.path.join(experiment_path, "receipts")

        try:
            os.makedirs(self.receipts_dir, exist_ok=True)
            logger.info(f"Initialized receipts directory at {self.receipts_dir}")
        except Exception as e:
            logger.error(f"Failed to create receipts directory: {e}")

    def write(
        self,
        model_name: str,
        merge_recipe: Dict,
        goal_result: Dict,
        general_result: Dict,
        model_path: str = "",
        experiment_name: str = ""
    ) -> str:
        try:
            receipt_path = os.path.join(self.receipts_dir, f"{model_name}_receipt.json")

            if os.path.exists(receipt_path):
                logger.warning(f"Receipt already exists at {receipt_path}, skipping write")
                return receipt_path

            scaled_goal_score = self._apply_chance_correction(
                goal_result.get("raw_score", 0.0),
                GOAL_BENCHMARK_CHANCE_LEVEL
            )

            goal_benchmark = {
                "task": goal_result.get("task", ""),
                "raw_score": goal_result.get("raw_score", 0.0),
                "scaled_score": scaled_goal_score
            }

            general_anomalies = general_result.get("anomalies", [])
            goal_anomalies = goal_result.get("anomalies", [])
            all_anomalies = general_anomalies + goal_anomalies

            receipt = {
                "model_name": model_name,
                "locked_at": datetime.utcnow().isoformat(),
                "merge_recipe": merge_recipe,
                "goal_benchmark": goal_benchmark,
                "general_benchmark": general_result,
                "anomalies": all_anomalies,
                "model_path": model_path,
                "experiment_name": experiment_name
            }

            with open(receipt_path, 'w') as f:
                json.dump(receipt, f, indent=2)

            logger.info(f"Receipt written successfully to {receipt_path}")
            return receipt_path

        except Exception as e:
            logger.error(f"Error writing receipt for {model_name}: {e}")
            return ""

    def load(self, model_name: str) -> Optional[Dict]:
        try:
            receipt_path = os.path.join(self.receipts_dir, f"{model_name}_receipt.json")

            if not os.path.exists(receipt_path):
                logger.warning(f"Receipt not found at {receipt_path}")
                return None

            with open(receipt_path, 'r') as f:
                receipt = json.load(f)

            logger.info(f"Loaded receipt for {model_name}")
            return receipt

        except Exception as e:
            logger.error(f"Error loading receipt for {model_name}: {e}")
            return None

    def list_receipts(self) -> List[Dict]:
        receipts = []

        try:
            if not os.path.exists(self.receipts_dir):
                logger.warning(f"Receipts directory does not exist: {self.receipts_dir}")
                return receipts

            for filename in os.listdir(self.receipts_dir):
                if filename.endswith("_receipt.json"):
                    receipt_path = os.path.join(self.receipts_dir, filename)

                    try:
                        with open(receipt_path, 'r') as f:
                            receipt = json.load(f)
                            receipts.append(receipt)
                    except Exception as e:
                        logger.warning(f"Error loading receipt {filename}: {e}")
                        continue

            logger.info(f"Listed {len(receipts)} receipts from {self.receipts_dir}")
            return receipts

        except Exception as e:
            logger.error(f"Error listing receipts: {e}")
            return receipts

    @staticmethod
    def _apply_chance_correction(raw_score: float, chance_level: float) -> float:
        if raw_score < 0.0 or raw_score > 1.0:
            logger.warning(f"Raw score out of range: {raw_score}")
            return 0.0

        scaled = max(0.0, (raw_score - chance_level) / (1 - chance_level)) * 100
        return round(scaled, 2)
