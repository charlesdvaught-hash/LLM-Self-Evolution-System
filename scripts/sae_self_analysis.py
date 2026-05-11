#!/usr/bin/env python3
"""
SAE Self-Analysis Tool
Runs introspective analysis on models to understand internal representations.

Usage:
    python scripts/sae_self_analysis.py --model "Qwen/Qwen2.5-1.5B-Instruct"
    python scripts/sae_self_analysis.py --model "path/to/merged_model" --output results.json
    python scripts/sae_self_analysis.py --compare "Qwen/Qwen2.5-1.5B-Instruct" "path/to/merged"
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent dirs to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from breeding_vat.modules.sae.scoped_analyzer import SAEScopedAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def analyze_model(model_id: str, num_samples: int = 50, output_path: str = None):
    """Run self-analysis on a model."""
    logger.info(f"Starting SAE self-analysis on {model_id}")
    logger.info(f"Samples: {num_samples}")
    
    analyzer = SAEScopedAnalyzer(model_id)
    
    try:
        results = analyzer.analyze_self(num_samples=num_samples)
        
        # Display results
        print("\n" + "="*70)
        print(f"SAE SELF-ANALYSIS RESULTS: {model_id}")
        print("="*70)
        
        print(f"\nEmergent Behaviors ({len(results['emergent_behaviors'])}):")
        for behavior in results["emergent_behaviors"]:
            print(f"  • Layer {behavior['layer']}: {behavior['type']}")
            print(f"    {behavior['description']}")
            print(f"    Strength: {behavior['strength']:.3f}")
        
        print(f"\nActivation Statistics:")
        stats = results["activation_statistics"]
        print(f"  Layers analyzed: {stats['num_layers_analyzed']}")
        print(f"  Average sparsity: {stats['avg_sparsity']:.3f}")
        print(f"  Specialized layers: {stats['specialized_layers']}")
        
        print(f"\nTop Important Dimensions by Layer:")
        for layer_idx, layer_result in results["layer_analysis"].items():
            if layer_idx < 5:  # Show first 5 layers
                if "feature_importance" in layer_result:
                    scores = layer_result["feature_importance"].get("top_importance_scores", [])
                    if scores:
                        print(f"  Layer {layer_idx}: {len(scores)} top dimensions (max importance: {max(scores):.3f})")
        
        print("\n" + "="*70)
        
        # Export if requested
        if output_path:
            import json
            with open(output_path, 'w') as f:
                # Convert numpy arrays to lists for JSON serialization
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results exported to {output_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def compare_models(model_id: str, base_model_id: str):
    """Compare a model with a base model."""
    logger.info(f"Starting comparison: {model_id} vs {base_model_id}")
    
    analyzer = SAEScopedAnalyzer(model_id)
    
    try:
        comparison = analyzer.compare_with_base(base_model_id)
        
        print("\n" + "="*70)
        print(f"SAE COMPARISON: {model_id} vs {base_model_id}")
        print("="*70)
        
        print(f"\nSparsity Change: {comparison['changes']['sparsity_change']:.3f}")
        
        print(f"\nCapability Indicators:")
        for indicator in comparison['changes']['capability_indicators']:
            print(f"  • {indicator}")
        
        print("\n" + "="*70)
        
        return comparison
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SAE Self-Analysis Tool - Introspect model internal representations"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Model ID or path to analyze"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of samples for analysis"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="Compare with base model (provide base model ID)"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        compare_models(args.model, args.compare)
    else:
        analyze_model(args.model, num_samples=args.samples, output_path=args.output)
