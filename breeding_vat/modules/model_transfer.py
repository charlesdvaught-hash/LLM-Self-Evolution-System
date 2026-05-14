"""
Local Model Transfer Utility
Handles upload and registration of local models into experiments.
Allows for symbolic linking to avoid unnecessary copies.
"""

import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelTransfer:
    """Transfer or Link local models to experiment model zoo."""
    
    def __init__(self, base_data_path: str = "breeding_vat/data",
                 experiment_manager=None):
        self.base_data_path = base_data_path
        self.global_model_zoo = os.path.join(base_data_path, "model_zoo")
        self.experiment_manager = experiment_manager
        os.makedirs(self.global_model_zoo, exist_ok=True)
    
    def register_local_model(
        self,
        local_path: str,
        model_name: str,
        experiment_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        use_symlink: bool = True
    ) -> Tuple[bool, str, Dict]:
        """
        Transfer or link a local model to the model zoo.
        """
        
        if not os.path.exists(local_path):
            return False, "", {"error": f"Source path not found: {local_path}"}
        
        abs_local_path = os.path.abspath(local_path)
        safe_name = self._sanitize_name(model_name)
        if not safe_name:
            return False, "", {"error": "Invalid model name"}
        
        dest_path = os.path.join(self.global_model_zoo, safe_name)
        if os.path.exists(dest_path):
            return False, dest_path, {"error": f"Model '{safe_name}' already exists in zoo"}
        
        try:
            if use_symlink:
                logger.info(f"Linking model from {abs_local_path} to {dest_path}")
                os.symlink(abs_local_path, dest_path)
            else:
                logger.info(f"Transferring model from {abs_local_path} to {dest_path}")
                if os.path.isdir(abs_local_path):
                    shutil.copytree(abs_local_path, dest_path, dirs_exist_ok=False)
                else:
                    os.makedirs(dest_path, exist_ok=True)
                    shutil.copy2(abs_local_path, os.path.join(dest_path, os.path.basename(abs_local_path)))
            
            model_info = {
                "name": safe_name,
                "original_path": abs_local_path,
                "is_symlink": use_symlink,
                "transferred_at": datetime.now().isoformat(),
                "experiment_id": experiment_id,
                "source": "local_upload",
                "size_bytes": self._get_dir_size(abs_local_path),
                "metadata": metadata or {}
            }
            
            metadata_path = os.path.join(self.global_model_zoo, f".{safe_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            if experiment_id and self.experiment_manager:
                exp = self.experiment_manager.load_experiment(experiment_id)
                if exp:
                    self.experiment_manager.register_specimen(
                        exp, safe_name, dest_path,
                        source="local_upload",
                        metadata=metadata or {}
                    )

            return True, dest_path, model_info
        
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            if os.path.exists(dest_path):
                if os.path.islink(dest_path):
                    os.unlink(dest_path)
                else:
                    shutil.rmtree(dest_path, ignore_errors=True)
            return False, "", {"error": str(e)}

    def validate_model_path(self, path: str) -> Tuple[bool, str]:
        if not os.path.exists(path):
            return False, "Path does not exist"
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        required_files = ["config.json"]
        has_required = all(os.path.exists(os.path.join(path, f)) for f in required_files)
        if has_required:
            return True, "Valid model detected"
        return False, "No model config found"

    def list_local_models(self) -> list:
        models = []
        if not os.path.exists(self.global_model_zoo):
            return models
        
        for item in os.listdir(self.global_model_zoo):
            if item.startswith(".") and item.endswith("_metadata.json"):
                metadata_path = os.path.join(self.global_model_zoo, item)
                with open(metadata_path, 'r') as f:
                    models.append(json.load(f))
        return models
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        path = os.path.join(self.global_model_zoo, model_name)
        if os.path.exists(path):
            return path
        return None

    @staticmethod
    def _sanitize_name(name: str) -> str:
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        return sanitized.strip('_-')[:64]

    @staticmethod
    def _get_dir_size(path: str) -> int:
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except: pass
        return total
