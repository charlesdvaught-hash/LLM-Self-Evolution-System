"""
Global Model Zoo Manager
Persistent, queryable model repository with metadata.
Enables slot-based selection and AI-assisted model recommendation.
"""

import os
import json
import shutil
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class GlobalModelZoo:
    """
    Centralized model zoo with:
    - Persistent model registry (JSON)
    - Query interface (filter, search, categorize)
    - Size/metadata tracking
    - UI-friendly listing
    """
    
    def __init__(self, base_path: str = "breeding_vat/data/model_zoo"):
        self.base_path = base_path
        self.registry_file = os.path.join(base_path, "_registry.json")
        os.makedirs(base_path, exist_ok=True)
        self._load_registry()
    
    def _load_registry(self):
        """Load or create registry."""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "models": {}
            }
            self._save_registry()
    
    def _save_registry(self):
        """Persist registry to disk."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def add_local_model(
        self,
        local_path: str,
        model_name: str,
        model_type: str = "generic",
        description: str = "",
        tags: Optional[List[str]] = None,
        size_gb: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Add a local model to the zoo.
        
        Args:
            local_path: Path to local model directory
            model_name: Display name (e.g., "my-qwen-finetuned")
            model_type: "reasoning", "retrieval", "instruction", "generic"
            description: Brief description
            tags: List of tags (e.g., ["3B", "reasoning", "finetuned"])
            size_gb: Model size in GB
        
        Returns:
            (success, message)
        """
        
        # Validate source
        if not os.path.exists(local_path):
            return False, f"Source path not found: {local_path}"
        
        # Check if has config.json
        is_valid, msg = self._validate_model_path(local_path)
        if not is_valid:
            return False, msg
        
        # Sanitize name
        safe_name = self._sanitize_name(model_name)
        if not safe_name:
            return False, "Invalid model name"
        
        # Check if already exists
        if safe_name in self.registry["models"]:
            return False, f"Model '{safe_name}' already in zoo"
        
        # Create destination
        dest_path = os.path.join(self.base_path, safe_name)
        
        try:
            # Copy model
            logger.info(f"Copying {local_path} → {dest_path}")
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(local_path, dest_path)
            
            # Calculate size
            if size_gb is None:
                size_bytes = self._get_dir_size(dest_path)
                size_gb = size_bytes / (1024**3)
            
            # Register
            self.registry["models"][safe_name] = {
                "name": safe_name,
                "display_name": model_name,
                "type": model_type,
                "description": description,
                "tags": tags or [],
                "size_gb": round(size_gb, 2),
                "path": dest_path,
                "added_at": datetime.now().isoformat(),
                "source": "local_upload"
            }
            
            self._save_registry()
            logger.info(f"Model registered: {safe_name}")
            return True, f"Added '{model_name}' ({size_gb:.2f} GB)"
        
        except Exception as e:
            logger.error(f"Failed to add model: {e}")
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path, ignore_errors=True)
            return False, f"Failed: {e}"
    
    def list_all_models(self, include_hf: bool = True) -> List[Dict]:
        """
        List all models in zoo.
        
        Args:
            include_hf: Include HuggingFace models (if True, returns local + HF names)
        
        Returns:
            List of model dicts with metadata
        """
        models = []
        
        # Local models from registry
        for name, info in self.registry["models"].items():
            models.append({
                **info,
                "source_type": "local"
            })
        
        # HuggingFace models (reference list)
        if include_hf:
            hf_models = [
                {"display_name": "Qwen 0.5B", "name": "Qwen/Qwen2.5-0.5B-Instruct", "type": "instruction", "source_type": "huggingface", "tags": ["0.5B", "instruction"]},
                {"display_name": "Qwen 1.5B", "name": "Qwen/Qwen2.5-1.5B-Instruct", "type": "reasoning", "source_type": "huggingface", "tags": ["1.5B", "reasoning"]},
                {"display_name": "Qwen 3B", "name": "Qwen/Qwen2.5-3B-Instruct", "type": "reasoning", "source_type": "huggingface", "tags": ["3B", "reasoning"]},
                {"display_name": "Qwen 7B", "name": "Qwen/Qwen2.5-7B-Instruct", "type": "reasoning", "source_type": "huggingface", "tags": ["7B", "reasoning"]},
                {"display_name": "Mistral 7B", "name": "mistralai/Mistral-7B-Instruct-v0.3", "type": "reasoning", "source_type": "huggingface", "tags": ["7B", "reasoning"]},
                {"display_name": "Llama 3B", "name": "meta-llama/Llama-2-3b-chat", "type": "instruction", "source_type": "huggingface", "tags": ["3B", "instruction"]},
                {"display_name": "Llama 3B Long", "name": "meta-llama/Llama-2-3b-long", "type": "retrieval", "source_type": "huggingface", "tags": ["3B", "retrieval", "long-context"]},
            ]
            models.extend(hf_models)
        
        return sorted(models, key=lambda x: x.get("display_name", ""))
    
    def get_models_by_type(self, model_type: str) -> List[Dict]:
        """Get models filtered by type."""
        models = self.list_all_models()
        return [m for m in models if m.get("type") == model_type]
    
    def get_models_by_tag(self, tag: str) -> List[Dict]:
        """Get models filtered by tag."""
        models = self.list_all_models()
        return [m for m in models if tag.lower() in [t.lower() for t in m.get("tags", [])]]
    
    def search_models(self, query: str) -> List[Dict]:
        """Search models by name/description/tags."""
        models = self.list_all_models()
        query_lower = query.lower()
        
        results = []
        for m in models:
            if (query_lower in m.get("display_name", "").lower() or
                query_lower in m.get("description", "").lower() or
                query_lower in str(m.get("tags", [])).lower() or
                query_lower in m.get("name", "").lower()):
                results.append(m)
        
        return results
    
    def remove_local_model(self, model_name: str) -> Tuple[bool, str]:
        """Remove a local model from zoo."""
        if model_name not in self.registry["models"]:
            return False, "Model not found"
        
        model_info = self.registry["models"][model_name]
        path = model_info.get("path")
        
        try:
            if path and os.path.exists(path):
                shutil.rmtree(path)
            del self.registry["models"][model_name]
            self._save_registry()
            return True, f"Removed '{model_name}'"
        except Exception as e:
            return False, f"Failed to remove: {e}"
    
    def get_model_display_name(self, model_id: str) -> str:
        """
        Get display name for a model.
        Works for both local and HuggingFace models.
        """
        # Check local registry
        if model_id in self.registry["models"]:
            return self.registry["models"][model_id].get("display_name", model_id)
        
        # Check HuggingFace list
        hf_models = {
            "Qwen/Qwen2.5-0.5B-Instruct": "Qwen 0.5B",
            "Qwen/Qwen2.5-1.5B-Instruct": "Qwen 1.5B",
            "Qwen/Qwen2.5-3B-Instruct": "Qwen 3B",
            "Qwen/Qwen2.5-7B-Instruct": "Qwen 7B",
            "mistralai/Mistral-7B-Instruct-v0.3": "Mistral 7B",
            "meta-llama/Llama-2-3b-chat": "Llama 3B",
            "meta-llama/Llama-2-3b-long": "Llama 3B Long",
        }
        
        return hf_models.get(model_id, model_id.split("/")[-1])
    
    @staticmethod
    def _validate_model_path(path: str) -> Tuple[bool, str]:
        """Check if path contains a valid model."""
        if not os.path.isdir(path):
            return False, "Not a directory"
        
        if not os.path.exists(os.path.join(path, "config.json")):
            return False, "No config.json found"
        
        return True, "Valid model"
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize model name."""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        sanitized = sanitized.strip('_-')
        return sanitized[:64] if sanitized else ""
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """Get directory size in bytes."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total
