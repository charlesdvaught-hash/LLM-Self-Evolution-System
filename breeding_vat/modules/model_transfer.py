"""
Local Model Transfer Utility
Handles upload and registration of local models into experiments.
Keeps originals pristine by copying to experiment-specific model zoo.
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
    """Transfer local models to experiment model zoo."""
    
    def __init__(self, base_data_path: str = "breeding_vat/data"):
        self.base_data_path = base_data_path
        self.global_model_zoo = os.path.join(base_data_path, "model_zoo")
        os.makedirs(self.global_model_zoo, exist_ok=True)
    
    def register_local_model(
        self,
        local_path: str,
        model_name: str,
        experiment_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Transfer a local model to the model zoo.
        
        Args:
            local_path: Path to local model directory or file
            model_name: Name to give the model (e.g., 'my-qwen-finetuned')
            experiment_id: Optional experiment ID for tracking
            metadata: Optional metadata dict (source, description, etc.)
        
        Returns:
            (success: bool, destination_path: str, model_info: dict)
        """
        
        # Validate source
        if not os.path.exists(local_path):
            return False, "", {"error": f"Source path not found: {local_path}"}
        
        # Sanitize model name
        safe_name = self._sanitize_name(model_name)
        if not safe_name:
            return False, "", {"error": "Invalid model name"}
        
        # Check if already exists
        dest_path = os.path.join(self.global_model_zoo, safe_name)
        if os.path.exists(dest_path):
            return False, dest_path, {"error": f"Model '{safe_name}' already exists in zoo"}
        
        try:
            # Copy to global model zoo
            logger.info(f"Transferring model from {local_path} to {dest_path}")
            
            if os.path.isdir(local_path):
                shutil.copytree(local_path, dest_path, dirs_exist_ok=False)
            else:
                # Single file - copy to a directory
                os.makedirs(dest_path, exist_ok=True)
                shutil.copy2(local_path, os.path.join(dest_path, os.path.basename(local_path)))
            
            # Create metadata file
            model_info = {
                "name": safe_name,
                "original_path": local_path,
                "transferred_at": datetime.now().isoformat(),
                "experiment_id": experiment_id,
                "source": "local_upload",
                "size_bytes": self._get_dir_size(dest_path),
                "metadata": metadata or {}
            }
            
            metadata_path = os.path.join(dest_path, ".model_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            logger.info(f"Model registered successfully: {safe_name}")
            return True, dest_path, model_info
        
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            # Cleanup partial transfer
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path, ignore_errors=True)
            return False, "", {"error": str(e)}
    
    def validate_model_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate if a path contains a valid model.
        Checks for common model files (config.json, model.safetensors, etc.)
        
        Returns:
            (is_valid: bool, message: str)
        """
        if not os.path.exists(path):
            return False, "Path does not exist"
        
        if not os.path.isdir(path):
            return False, "Path is not a directory"
        
        # Check for model indicators
        required_files = ["config.json"]
        optional_files = [
            "model.safetensors",
            "pytorch_model.bin",
            "model.bin",
            "tokenizer.json",
            "tokenizer_config.json"
        ]
        
        has_required = all(
            os.path.exists(os.path.join(path, f)) for f in required_files
        )
        has_optional = any(
            os.path.exists(os.path.join(path, f)) for f in optional_files
        )
        
        if has_required and has_optional:
            return True, "Valid model detected"
        elif has_required:
            return True, "Config found (weights not detected)"
        else:
            return False, "No model config found"
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get metadata about a transferred model."""
        metadata_path = os.path.join(
            self.global_model_zoo,
            model_name,
            ".model_metadata.json"
        )
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
    
    def list_local_models(self) -> list:
        """List all locally transferred models."""
        models = []
        if not os.path.exists(self.global_model_zoo):
            return models
        
        for item in os.listdir(self.global_model_zoo):
            item_path = os.path.join(self.global_model_zoo, item)
            if os.path.isdir(item_path):
                metadata_path = os.path.join(item_path, ".model_metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        models.append(json.load(f))
        
        return models
    
    def get_model_path(self, model_name: str) -> Optional[str]:
        """Get full path to a transferred model."""
        path = os.path.join(self.global_model_zoo, model_name)
        if os.path.exists(path):
            return path
        return None
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize model name for filesystem."""
        import re
        # Allow alphanumeric, dash, underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        # Remove leading/trailing underscores/dashes
        sanitized = sanitized.strip('_-')
        # Limit length
        return sanitized[:64] if sanitized else ""
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """Get total size of directory in bytes."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception as e:
            logger.warning(f"Could not calculate directory size: {e}")
        return total
