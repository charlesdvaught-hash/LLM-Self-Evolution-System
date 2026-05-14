"""
Benchmark and prediction module for Breeding Vat.

Provides:
- FusionBench integration for standardized merging + evaluation
- Experiment tracking database
- Method prediction engine for optimal merge strategies
- Receipt-based immutable model evaluation results
"""

from .fusion_bench_wrapper import FusionBenchWrapper
from .prediction_engine import ExperimentDatabase, MethodPredictor
from .receipt_runner import BenchmarkRunner
from .receipt_writer import ReceiptWriter

__all__ = [
    "FusionBenchWrapper",
    "ExperimentDatabase",
    "MethodPredictor",
    "BenchmarkRunner",
    "ReceiptWriter"
]
