"""
Experiment Manager: Handle experiment lifecycle, logging, resumption.
Organizes outputs into dated folders, tracks metadata, enables resumption.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger("ExperimentManager")


class ExperimentManager:
    """
    Manages experiment lifecycle:
    - Create dated experiment folder
    - Log all artifacts (models, logs, configs, benchmarks)
    - Track experiment metadata
    - Enable resumption (load prior state, continue evolution)
    """
    
    def __init__(self, base_dir: str = "breeding_vat/data/experiments"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"ExperimentManager initialized at {base_dir}")
    
    def create_experiment(self, goal: str, base_models: List[str], 
                         merge_methods: List[str], num_cycles: int,
                         custom_name: Optional[str] = None) -> Dict:
        """
        Create a new experiment folder and metadata.
        
        Args:
            goal: User-defined goal for this experiment
            base_models: List of base model names/IDs
            merge_methods: Merge methods to use (SLERP, TIES, etc)
            num_cycles: Number of evolution cycles planned
            custom_name: Optional custom name (uses goal + date if None)
            
        Returns:
            Experiment metadata dict with paths and IDs
        """
        # Generate experiment name: goal_YYYY-MM-DD_HHMMSS
        if custom_name:
            exp_name = custom_name.replace(" ", "_").replace("/", "_")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            exp_name = f"{goal[:30].replace(' ', '_')}_{timestamp}"
        
        exp_dir = os.path.join(self.base_dir, exp_name)
        
        # Create subdirectories
        self.models_dir = os.path.join(exp_dir, "merged_models")
        self.logs_dir = os.path.join(exp_dir, "logs")
        self.configs_dir = os.path.join(exp_dir, "configs")
        self.results_dir = os.path.join(exp_dir, "results")
        
        for d in [self.models_dir, self.logs_dir, self.configs_dir, self.results_dir]:
            os.makedirs(d, exist_ok=True)
        
        # Create experiment metadata
        experiment = {
            "id": exp_name,
            "name": exp_name,
            "goal": goal,
            "base_models": base_models,
            "merge_methods": merge_methods,
            "num_cycles_planned": num_cycles,
            "created_at": datetime.now().isoformat(),
            "status": "in_progress",
            "cycles_completed": 0,
            "best_model": None,
            "best_score": 0.0,
            "registered_models": [],  # local specimens registered to this experiment
            "paths": {
                "root": exp_dir,
                "models": self.models_dir,
                "logs": self.logs_dir,
                "configs": self.configs_dir,
                "results": self.results_dir,
                "metadata": os.path.join(exp_dir, "experiment.json"),
                "master_log": os.path.join(self.logs_dir, "master.log"),
                "benchmark_db": os.path.join(self.results_dir, "benchmarks.json"),
                "assay_cache": os.path.join(self.results_dir, "assay_reference_cache.json"),
            }
        }
        
        # Save metadata
        self._save_metadata(experiment)
        
        # Initialize logs
        self._init_log_file(experiment["paths"]["master_log"], experiment)
        
        # Initialize benchmark database
        self._init_benchmark_db(experiment)
        
        logger.info(f"Created experiment: {exp_name}")
        logger.info(f"  Root: {exp_dir}")
        logger.info(f"  Models: {self.models_dir}")
        logger.info(f"  Logs: {self.logs_dir}")
        
        return experiment
    
    def load_experiment(self, exp_name: str) -> Optional[Dict]:
        """
        Load an existing experiment by name.
        Enables resumption of prior runs.
        
        Args:
            exp_name: Experiment folder name
            
        Returns:
            Experiment metadata dict, or None if not found
        """
        metadata_path = os.path.join(self.base_dir, exp_name, "experiment.json")
        
        if not os.path.exists(metadata_path):
            logger.error(f"Experiment not found: {exp_name}")
            return None
        
        with open(metadata_path, 'r') as f:
            experiment = json.load(f)
        
        logger.info(f"Loaded experiment: {exp_name}")
        logger.info(f"  Status: {experiment['status']}")
        logger.info(f"  Cycles completed: {experiment['cycles_completed']}")
        logger.info(f"  Best score: {experiment['best_score']:.4f}")
        
        return experiment
    
    def list_experiments(self) -> List[Dict]:
        """List all available experiments."""
        experiments = []
        
        for exp_folder in os.listdir(self.base_dir):
            exp_path = os.path.join(self.base_dir, exp_folder)
            metadata_path = os.path.join(exp_path, "experiment.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    exp = json.load(f)
                experiments.append(exp)
        
        # Sort by creation date (newest first)
        experiments.sort(key=lambda x: x['created_at'], reverse=True)
        
        return experiments
    
    def log_cycle(self, experiment: Dict, cycle_num: int, 
                  models: List[Dict], best_model: Dict):
        """
        Log results from an evolution cycle.
        
        Args:
            experiment: Experiment metadata
            cycle_num: Cycle number (1-based)
            models: List of models generated this cycle
            best_model: Best model from this cycle
        """
        master_log_path = experiment["paths"]["master_log"]
        benchmark_db_path = experiment["paths"]["benchmark_db"]
        
        # Append to master log
        with open(master_log_path, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"CYCLE {cycle_num} | {datetime.now().isoformat()}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Models evaluated: {len(models)}\n")
            f.write(f"Best model: {best_model['name']} (score: {best_model['score']:.4f})\n")
            
            for model in models:
                f.write(f"  - {model['name']}: {model['score']:.4f}\n")
            f.write("\n")
        
        # Update benchmark database
        with open(benchmark_db_path, 'r') as f:
            benchmarks = json.load(f)
        
        benchmarks["cycles"].append({
            "cycle": cycle_num,
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "best_model": best_model
        })
        
        with open(benchmark_db_path, 'w') as f:
            json.dump(benchmarks, f, indent=2)
        
        # Update experiment metadata
        experiment["cycles_completed"] = cycle_num
        experiment["best_model"] = best_model['name']
        experiment["best_score"] = best_model['score']
        self._save_metadata(experiment)
        
        logger.info(f"Logged cycle {cycle_num}: best={best_model['name']} ({best_model['score']:.4f})")
    
    def save_model(self, experiment: Dict, model_path: str, 
                  model_name: str, metadata: Dict = None) -> str:
        """
        Copy a merged model to the experiment folder.
        
        Args:
            experiment: Experiment metadata
            model_path: Path to source model
            model_name: Name for the model in experiment
            metadata: Optional metadata dict
            
        Returns:
            Destination path
        """
        dest_dir = os.path.join(experiment["paths"]["models"], model_name)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copy model files
        try:
            import shutil
            for item in os.listdir(model_path):
                src = os.path.join(model_path, item)
                dst = os.path.join(dest_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            # Save metadata if provided
            if metadata:
                with open(os.path.join(dest_dir, "model_metadata.json"), 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved model: {dest_dir}")
            return dest_dir
        
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return None
    
    def save_config(self, experiment: Dict, config: Dict, 
                   config_name: str) -> str:
        """Save a merge config to the experiment folder."""
        config_path = os.path.join(
            experiment["paths"]["configs"],
            f"{config_name}.json"
        )
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved config: {config_path}")
        return config_path
    
    def register_specimen(self, experiment: Dict, model_name: str,
                           zoo_path: str, source: str = "local_upload",
                           metadata: Optional[Dict] = None) -> Dict:
        """
        Register a model as a specimen for this experiment.
        Records it in experiment.json so the run is fully reproducible.
        """
        entry = {
            "name": model_name,
            "zoo_path": zoo_path,
            "source": source,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        if "registered_models" not in experiment:
            experiment["registered_models"] = []
        # Avoid duplicates
        existing = [m["name"] for m in experiment["registered_models"]]
        if model_name not in existing:
            experiment["registered_models"].append(entry)
            self._save_metadata(experiment)
            logger.info(f"Registered specimen '{model_name}' to experiment {experiment['id']}")
        return entry

    def get_specimens(self, experiment: Dict) -> List[Dict]:
        """Return all specimens registered to this experiment."""
        return experiment.get("registered_models", [])

    def finalize_experiment(self, experiment: Dict, status: str = "completed"):
        """
        Mark experiment as complete and save final state.
        
        Args:
            experiment: Experiment metadata
            status: Final status (completed, paused, failed)
        """
        experiment["status"] = status
        experiment["completed_at"] = datetime.now().isoformat()
        self._save_metadata(experiment)
        
        # Write summary to master log
        with open(experiment["paths"]["master_log"], 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"EXPERIMENT {status.upper()}\n")
            f.write(f"Completed at: {experiment['completed_at']}\n")
            f.write(f"Best model: {experiment['best_model']}\n")
            f.write(f"Best score: {experiment['best_score']:.4f}\n")
            f.write(f"Cycles completed: {experiment['cycles_completed']}\n")
            f.write(f"{'='*80}\n")
        
        logger.info(f"Finalized experiment: {experiment['id']} ({status})")
    
    def _save_metadata(self, experiment: Dict):
        """Save experiment metadata to JSON."""
        with open(experiment["paths"]["metadata"], 'w') as f:
            json.dump(experiment, f, indent=2, default=str)
    
    def _init_log_file(self, log_path: str, experiment: Dict):
        """Initialize master log file."""
        with open(log_path, 'w') as f:
            f.write(f"{'='*80}\n")
            f.write(f"EXPERIMENT: {experiment['name']}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Goal: {experiment['goal']}\n")
            f.write(f"Base Models: {', '.join(experiment['base_models'])}\n")
            f.write(f"Merge Methods: {', '.join(experiment['merge_methods'])}\n")
            f.write(f"Planned Cycles: {experiment['num_cycles_planned']}\n")
            f.write(f"Created: {experiment['created_at']}\n")
            f.write(f"{'='*80}\n\n")
    
    def _init_benchmark_db(self, experiment: Dict):
        """Initialize benchmark database JSON."""
        benchmarks = {
            "experiment_id": experiment['id'],
            "goal": experiment['goal'],
            "base_models": experiment['base_models'],
            "created_at": experiment['created_at'],
            "cycles": []
        }
        
        with open(experiment["paths"]["benchmark_db"], 'w') as f:
            json.dump(benchmarks, f, indent=2)
