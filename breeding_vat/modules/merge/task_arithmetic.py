import os
import logging
from typing import Dict, List, Optional
from breeding_vat.orchestrator.runner import TaskRunner
from breeding_vat.modules.merge.mergekit_engine import MergekitEngine

logger = logging.getLogger("TaskArithmeticMerger")

class TaskArithmeticMerger:
    """
    Task Arithmetic merging via Mergekit.
    
    Vector-space model composition:
    δ_A = model_A - base_model
    δ_B = model_B - base_model
    result = base_model + α*δ_A + β*δ_B
    
    Advantages:
    - More principled than SLERP
    - Can compose multiple deltas
    - Better for multi-model blending
    - Weight deltas are more interpretable
    - Handles large models (70B+) via streaming
    """
    
    def __init__(self, runner: TaskRunner = None,
                 output_dir="breeding_vat/data/merged_models"):
        self.runner = runner
        self.engine = MergekitEngine(runner, output_dir) if runner else None
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info("TaskArithmeticMerger initialized (Mergekit backend)")
    
    def merge(self, base_model_path: str, task_models: Dict[str, float],
             output_path: str, dtype: str = "float16") -> Optional[str]:
        """
        Merge multiple task models using task arithmetic via Mergekit.
        
        Args:
            base_model_path: Path to base model
            task_models: Dict of {model_path: weight}
                        Example: {"model_a": 0.5, "model_b": 0.3}
            output_path: Output model directory
            dtype: Data type (float16, float32)
            
        Returns:
            output_path if successful, None otherwise
        """
        logger.info(f"Task Arithmetic merge starting...")
        logger.info(f"  Base: {base_model_path}")
        logger.info(f"  Task models: {task_models}")
        logger.info(f"  Output: {output_path}")
        
        if not self.engine:
            logger.error("No TaskRunner provided. Cannot execute merge.")
            return None
        
        try:
            # Extract model paths and weights
            merge_models = list(task_models.keys())
            weights = list(task_models.values())
            
            # Create Mergekit config for task arithmetic
            config_path = self.engine.create_config(
                "task_arithmetic",
                base_model_path,
                merge_models,
                {"weights": weights}
            )
            
            # Run merge
            output_name = os.path.basename(output_path)
            result = self.engine.run_merge(config_path, output_name)
            
            if result:
                logger.info(f"Task Arithmetic merge complete: {result}")
            else:
                logger.error(f"Task Arithmetic merge failed")
            
            return result
        
        except Exception as e:
            logger.error(f"Task Arithmetic merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def multi_delta_merge(self, base_model_path: str,
                         deltas: Dict[str, tuple],
                         output_path: str, dtype: str = "float16") -> Optional[str]:
        """
        Merge using pre-computed deltas (e.g., from LoRA).
        
        Args:
            base_model_path: Path to base model
            deltas: Dict of {delta_name: (delta_path, weight)}
            output_path: Output model directory
            dtype: Data type
            
        Returns:
            output_path if successful, None otherwise
        """
        logger.info(f"Multi-delta merge starting...")
        logger.info(f"  Base: {base_model_path}")
        logger.info(f"  Deltas: {list(deltas.keys())}")
        
        if not self.engine:
            logger.error("No TaskRunner provided. Cannot execute merge.")
            return None
        
        try:
            # For delta merging, we use task arithmetic with delta weights
            # This is a simplified approach - full delta support would require
            # additional Mergekit extensions
            logger.warning("Multi-delta merge: Using task arithmetic approximation")
            
            delta_weights = {name: weight for name, (_, weight) in deltas.items()}
            
            config_path = self.engine.create_config(
                "task_arithmetic",
                base_model_path,
                list(delta_weights.keys()),
                {"weights": list(delta_weights.values())}
            )
            
            output_name = os.path.basename(output_path)
            result = self.engine.run_merge(config_path, output_name)
            
            if result:
                logger.info(f"Multi-delta merge complete: {result}")
            else:
                logger.error(f"Multi-delta merge failed")
            
            return result
        
        except Exception as e:
            logger.error(f"Multi-delta merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def compute_delta(self, base_model_path: str, task_model_path: str,
                     output_path: str, dtype: str = "float16") -> Optional[str]:
        """
        Compute and save delta weights (task_model - base_model).
        
        Note: Mergekit doesn't have a built-in delta extraction tool,
        so this would require custom implementation.
        For now, we recommend using LoRA extraction instead.
        
        Args:
            base_model_path: Path to base model
            task_model_path: Path to task model
            output_path: Where to save delta weights
            dtype: Data type
            
        Returns:
            output_path if successful, None otherwise
        """
        logger.warning("Delta computation: Not directly supported by Mergekit")
        logger.warning("Consider using LoRA-based delta extraction instead")
        logger.info(f"Skipping delta computation: {base_model_path} -> {task_model_path}")
        return None
