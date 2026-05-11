"""
Benchmark and prediction module for Breeding Vat.

Provides:
- FusionBench integration for standardized merging + evaluation
- Experiment tracking database
- Method prediction engine for optimal merge strategies
"""

from .fusion_bench_wrapper import FusionBenchWrapper
from .prediction_engine import ExperimentDatabase, MethodPredictor

__all__ = [
    "FusionBenchWrapper",
    "ExperimentDatabase", 
    "MethodPredictor"
]
