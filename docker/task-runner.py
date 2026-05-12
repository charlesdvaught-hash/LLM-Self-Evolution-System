#!/usr/bin/env python
"""
Task Runner: Ephemeral container entrypoint for merge/eval/sae tasks.
Called by orchestrator.runner with task config + type (merge|eval|sae|train).
"""

import sys
import os
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for ephemeral task containers.
    Usage: python task-runner.py <task_type> <config_path>
    """
    
    if len(sys.argv) < 2:
        logger.error("Usage: task-runner.py <task_type> [config_path]")
        sys.exit(1)
    
    task_type = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    logger.info(f"Starting task: {task_type}")
    logger.info(f"Config: {config_path}")
    
    try:
        if task_type == "merge":
            from breeding_vat.modules.merge.runner import run_merge
            run_merge(config_path)
        
        elif task_type == "eval":
            from breeding_vat.modules.eval.runner import run_eval
            run_eval(config_path)
        
        elif task_type == "sae":
            from breeding_vat.modules.sae.runner import run_sae_analysis
            run_sae_analysis(config_path)
        
        elif task_type == "train":
            from breeding_vat.modules.train.runner import run_training
            run_training(config_path)
        
        else:
            logger.error(f"Unknown task type: {task_type}")
            sys.exit(1)
        
        logger.info(f"Task {task_type} completed successfully")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Task {task_type} failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
