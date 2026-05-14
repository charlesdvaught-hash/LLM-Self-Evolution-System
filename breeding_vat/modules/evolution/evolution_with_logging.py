"""
Evolution Engine with Experiment Logging Integration

Wraps evolution cycles with real-time experiment tracking,
model staging, config saving, and resumption support.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger("EvolutionWithLogging")


class EvolutionWithLogging:
    """
    Wraps evolution to integrate experiment management.
    
    - Logs each cycle to experiment
    - Saves configs and models to experiment folder
    - Provides progress callbacks for UI streaming
    - Supports resumption from saved state
    """
    
    def __init__(self, evolution_engine, experiment_manager, experiment: Dict,
                 progress_callback: Optional[Callable] = None):
        """
        Args:
            evolution_engine: Your existing EvolutionEngine instance
            experiment_manager: ExperimentManager instance
            experiment: Experiment metadata dict (from create_experiment)
            progress_callback: Optional callback(cycle, total, status) for UI updates
        """
        self.evolution = evolution_engine
        self.exp_manager = experiment_manager
        self.experiment = experiment
        self.progress_callback = progress_callback
        logger.info(f"EvolutionWithLogging initialized for {experiment['name']}")
    
    def run_waterfall(self, base_models: List[str], goal: str, num_cycles: int,
                     culling_rate: float = 50, allowed_methods: List[str] = None,
                     resume_from_cycle: int = 0) -> Dict:
        """
        Run evolution with logging and progress updates.
        Wraps the underlying EvolutionEngine.run_waterfall().
        
        Args:
            base_models: List of base model IDs
            goal: User goal description
            num_cycles: Number of evolution cycles
            culling_rate: Percentage of models to keep
            allowed_methods: Merge methods to use
            resume_from_cycle: If resuming, start from this cycle (0-based)
            
        Returns:
            Best model dict with name, score, path
        """
        try:
            # Update experiment config
            self.experiment['base_models'] = base_models
            self.experiment['merge_methods'] = allowed_methods or []
            self.experiment['num_cycles_planned'] = num_cycles
            self.exp_manager._save_metadata(self.experiment)
            
            # Log to master log
            with open(self.experiment['paths']['master_log'], 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"EVOLUTION RUN STARTED\n")
                f.write(f"Resume from cycle: {resume_from_cycle}\n")
                f.write(f"Total cycles: {num_cycles}\n")
                f.write(f"Base models: {', '.join(base_models)}\n")
                f.write(f"Merge methods: {', '.join(allowed_methods or ['slerp'])}\n")
                f.write(f"Culling rate: {culling_rate}%\n")
                f.write(f"{'='*80}\n\n")
            
            self._emit_progress(0, num_cycles, "Initializing evolution...")
            
            # NEW: Inject experiment manager into evolution engine for genealogy tracking
            self.evolution._experiment_manager = self.exp_manager
            self.evolution._current_experiment = self.experiment
            
            # Call the underlying evolution engine
            best_model = self.evolution.run_waterfall(
                base_models=base_models,
                goal=goal,
                cycles=num_cycles,
                culling_rate=culling_rate,
                allowed_methods=allowed_methods or ["slerp"]
            )
            
            # Log final result
            self._log(f"Evolution complete! Best model: {best_model['name']} (score: {best_model['score']:.4f})")
            
            # Update experiment metadata
            self.experiment['cycles_completed'] = num_cycles
            self.experiment['best_model'] = best_model['name']
            self.experiment['best_score'] = best_model['score']
            self.exp_manager._save_metadata(self.experiment)
            
            # Finalize
            self.exp_manager.finalize_experiment(self.experiment, "completed")
            self._emit_progress(num_cycles, num_cycles, "Complete")
            
            return best_model
        
        except Exception as e:
            self._log(f"Evolution failed: {str(e)}")
            self.exp_manager.finalize_experiment(self.experiment, "failed")
            logger.error(f"Evolution failed: {e}")
            raise
    

    

    
    def _log(self, message: str):
        """Internal logging to master log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.experiment['paths']['master_log'], 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _emit_progress(self, current_cycle: int, total_cycles: int, status: str):
        """Emit progress update to UI callback."""
        if self.progress_callback:
            try:
                self.progress_callback(current_cycle, total_cycles, status)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
