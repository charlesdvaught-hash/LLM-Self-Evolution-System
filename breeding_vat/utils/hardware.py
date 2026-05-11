import psutil
import torch
import shutil
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("HardwareUtils")

def get_hardware_stats() -> Dict[str, Any]:
    """Detect available VRAM, RAM, and disk space."""
    stats = {
        "vram_total": 0.0,
        "vram_free": 0.0,
        "ram_total": 0.0,
        "ram_available": 0.0,
        "disk_free": 0.0
    }

    # RAM
    ram = psutil.virtual_memory()
    stats["ram_total"] = ram.total / (1024**3)
    stats["ram_available"] = ram.available / (1024**3)

    # Disk (check project root or data dir)
    path = "breeding_vat/data"
    if not os.path.exists(path):
        path = "."
    disk = shutil.disk_usage(path)
    stats["disk_free"] = disk.free / (1024**3)

    # VRAM
    if torch.cuda.is_available():
        try:
            device = torch.cuda.current_device()
            free, total = torch.cuda.mem_get_info(device)
            stats["vram_total"] = total / (1024**3)
            stats["vram_free"] = free / (1024**3)
        except Exception as e:
            logger.warning(f"Failed to get CUDA stats: {e}")

    return stats

def predict_resources(method: str, model_sizes_gb: list[float]) -> Dict[str, float]:
    """Estimate resource requirements for a merge operation."""
    max_model_size = max(model_sizes_gb) if model_sizes_gb else 0
    sum_model_size = sum(model_sizes_gb)

    if method == "slerp":
        return {
            "vram": max_model_size * 1.2,
            "ram": sum_model_size * 1.1,
            "disk": max_model_size * 1.0
        }
    elif method in ["ties", "dare", "task_arithmetic"]:
        return {
            "vram": max_model_size * 1.5,
            "ram": sum_model_size * 2.0,
            "disk": max_model_size * 1.0
        }
    elif method == "moe":
        return {
            "vram": max_model_size * 1.2,
            "ram": max_model_size * 2.0,
            "disk": sum_model_size * 1.1
        }
    else:
        return {
            "vram": max_model_size * 1.5,
            "ram": sum_model_size * 1.5,
            "disk": max_model_size * 1.1
        }

def get_risk_assessment(prediction: Dict[str, float], actual: Dict[str, float]) -> Dict[str, Any]:
    """Calculate failure risk based on predicted vs actual hardware."""
    risks = {}
    if actual["vram_total"] > 0:
        vram_ratio = prediction["vram"] / actual["vram_free"]
        risks["vram"] = vram_ratio * 100
    else:
        risks["vram"] = 0 # No GPU, maybe CPU merge

    risks["ram"] = (prediction["ram"] / actual["ram_available"]) * 100
    risks["disk"] = (prediction["disk"] / actual["disk_free"]) * 100

    max_risk = max(risks.values())
    return {
        "risks": risks,
        "max_risk": max_risk,
        "status": "danger" if max_risk > 75 else "warning" if max_risk > 50 else "safe"
    }
