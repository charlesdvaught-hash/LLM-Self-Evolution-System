"""
Model Path Resolver
Resolves HuggingFace IDs and local model names to actual paths.
"""

import os
from typing import Tuple, Optional
from pathlib import Path


class ModelPathResolver:
    """Resolve model identifiers to actual paths."""
    
    def __init__(self, model_transfer=None, huggingface_cache: Optional[str] = None):
        """
        Args:
            model_transfer: ModelTransfer instance for local model lookup
            huggingface_cache: Path to HF cache (default: ~/.cache/huggingface/hub)
        """
        self.model_transfer = model_transfer
        self.hf_cache = huggingface_cache or os.path.expanduser("~/.cache/huggingface/hub")
    
    def resolve(self, model_id: str) -> Tuple[bool, str]:
        """
        Resolve a model identifier to a path.
        
        Args:
            model_id: Either a HuggingFace ID (e.g., 'Qwen/Qwen2.5-0.5B')
                     or a local model name (e.g., 'my-qwen-finetuned')
        
        Returns:
            (success: bool, path: str)
        """
        
        # Check if it's a local model name
        if self.model_transfer:
            local_path = self.model_transfer.get_model_path(model_id)
            if local_path:
                return True, local_path
        
        # Try as HuggingFace model ID
        hf_path = self._resolve_hf_model(model_id)
        if hf_path:
            return True, hf_path
        
        # If not found locally, return the HF ID as-is
        # (Will be downloaded on-demand by the merge engine)
        return True, model_id
    
    def _resolve_hf_model(self, model_id: str) -> Optional[str]:
        """
        Try to find a HuggingFace model in local cache.
        
        HF cache structure:
        ~/.cache/huggingface/hub/models--org--modelname/
        """
        
        if "/" not in model_id:
            return None  # Not a HF ID
        
        # Convert 'Qwen/Qwen2.5-0.5B' to 'models--Qwen--Qwen2.5-0.5B'
        cache_dir_name = "models--" + model_id.replace("/", "--")
        cache_path = os.path.join(self.hf_cache, cache_dir_name)
        
        if os.path.exists(cache_path):
            # Find the snapshots directory with actual weights
            snapshots_path = os.path.join(cache_path, "snapshots")
            if os.path.exists(snapshots_path):
                # Return the first (most recent) snapshot
                snapshots = os.listdir(snapshots_path)
                if snapshots:
                    return os.path.join(snapshots_path, snapshots[0])
        
        return None
    
    def is_local_model(self, model_id: str) -> bool:
        """Check if model_id refers to a local model."""
        if self.model_transfer:
            return self.model_transfer.get_model_path(model_id) is not None
        return False
    
    def is_hf_model(self, model_id: str) -> bool:
        """Check if model_id is a HuggingFace ID."""
        return "/" in model_id
