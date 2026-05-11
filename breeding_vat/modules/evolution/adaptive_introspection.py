"""
Adaptive Evolution with Self-Introspection via Scoped Model

The Scoped Model (SAE-analyzed Qwen) acts as an introspection engine,
analyzing what changed during merges and guiding future mutations.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("AdaptiveEvolution")


class ScopedModelIntrospection:
    """
    Use a SAE-scoped model to introspect merged models.
    
    The Scoped Model can "read its own state" via SAE analysis,
    telling evolution what worked, what broke, and what to try next.
    """
    
    def __init__(self, scoped_model_id: str = "local/scoped-qwen-1.5b",
                 sae_analyzer=None):
        """
        Args:
            scoped_model_id: Path to SAE-scoped model (smaller, interpretable)
            sae_analyzer: SAE analyzer instance for layer introspection
        """
        self.scoped_model_id = scoped_model_id
        self.sae_analyzer = sae_analyzer
        self.baseline_activations = {}
        logger.info(f"ScopedModelIntrospection initialized with {scoped_model_id}")
    
    def establish_baseline(self, baseline_model_id: str):
        """
        Establish parent model's SAE representation as baseline.
        All future analyses compare against this.
        """
        logger.info(f"Establishing baseline from {baseline_model_id}")
        
        try:
            self.baseline_activations = self.sae_analyzer.analyze(baseline_model_id)
            logger.info(f"Baseline established: {len(self.baseline_activations)} layers")
        except Exception as e:
            logger.error(f"Failed to establish baseline: {e}")
            return False
        
        return True
    
    def analyze_merge(self, merged_model_path: str, goal_metric_score: float,
                     baseline_score: float) -> Dict:
        """
        Introspect a merged model: what changed and why?
        
        Returns interpretable analysis for evolution to use.
        """
        logger.info(f"Introspecting merge: score={goal_metric_score:.3f}, baseline={baseline_score:.3f}")
        
        try:
            merged_activations = self.sae_analyzer.analyze(merged_model_path)
        except Exception as e:
            logger.error(f"Failed to analyze merged model: {e}")
            return self._empty_introspection()
        
        analysis = {
            "layer_changes": self._analyze_layer_changes(merged_activations),
            "capability_indicators": self._infer_capability_changes(merged_activations),
            "stability_metrics": self._measure_stability(merged_activations),
            "novel_patterns": self._detect_novel_patterns(merged_activations),
            "recommendations": {},
            "summary": ""
        }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis, goal_metric_score, baseline_score)
        analysis["summary"] = self._generate_summary(analysis)
        
        return analysis
    
    def _analyze_layer_changes(self, merged_activations: Dict) -> Dict:
        """Compare layer-by-layer activation patterns."""
        changes = {}
        
        for layer_idx, baseline_data in self.baseline_activations.items():
            if layer_idx not in merged_activations:
                continue
            
            merged_data = merged_activations[layer_idx]
            
            # Calculate divergence
            baseline_mean = np.array(baseline_data.get("mean", []))
            merged_mean = np.array(merged_data.get("mean", []))
            
            if len(baseline_mean) == 0 or len(merged_mean) == 0:
                continue
            
            # Normalize for comparison
            baseline_mean = baseline_mean / (np.linalg.norm(baseline_mean) + 1e-8)
            merged_mean = merged_mean / (np.linalg.norm(merged_mean) + 1e-8)
            
            divergence = float(np.linalg.norm(baseline_mean - merged_mean))
            
            changes[layer_idx] = {
                "divergence": divergence,  # 0 = identical, 1 = completely different
                "sparsity_baseline": baseline_data.get("sparsity", 0),
                "sparsity_merged": merged_data.get("sparsity", 0),
                "sparsity_change": merged_data.get("sparsity", 0) - baseline_data.get("sparsity", 0),
                "num_active_features": merged_data.get("num_active_features", 0),
                "stability": self._calculate_layer_stability(merged_data)
            }
        
        return changes
    
    def _calculate_layer_stability(self, layer_data: Dict) -> float:
        """
        Measure layer stability (0 = unstable, 1 = very stable).
        Based on variance of activations and weight distribution.
        """
        try:
            variance = layer_data.get("activation_variance", 0)
            # Normalized variance-based stability
            stability = 1.0 / (1.0 + variance)
            return float(np.clip(stability, 0, 1))
        except:
            return 0.5
    
    def _infer_capability_changes(self, merged_activations: Dict) -> Dict:
        """
        Infer capability-level changes from activation patterns.
        
        Different capabilities typically activate different layer patterns:
        - Code reasoning: heavy layer 8-12 activity
        - Math: consistent layer 5-10 activity
        - Language fluency: broad activation pattern
        """
        capabilities = {
            "code_reasoning": self._capability_indicator(merged_activations, layers=[8, 9, 10, 11, 12]),
            "mathematical": self._capability_indicator(merged_activations, layers=[5, 6, 7, 8, 9]),
            "language_coherence": self._capability_indicator(merged_activations, layers=[0, 1, 2, 3, 4]),
            "contextual_awareness": self._capability_indicator(merged_activations, layers=[15, 16, 17, 18, 19])
        }
        
        return capabilities
    
    def _capability_indicator(self, activations: Dict, layers: List[int]) -> Dict:
        """Estimate capability strength from layer activation patterns."""
        scores = []
        
        for layer in layers:
            if layer in activations:
                # Higher active feature count suggests stronger capability
                num_active = activations[layer].get("num_active_features", 0)
                stability = self._calculate_layer_stability(activations[layer])
                scores.append(num_active * stability)
        
        if not scores:
            return {"indicator": 0.0, "layers_involved": [], "active_features": 0}
        
        avg_score = float(np.mean(scores))
        
        return {
            "indicator": avg_score,  # 0-1 scale
            "layers_involved": layers,
            "active_features": int(np.sum(scores)),
            "stability": float(np.mean([self._calculate_layer_stability(activations[l]) for l in layers if l in activations]))
        }
    
    def _measure_stability(self, merged_activations: Dict) -> Dict:
        """
        Measure overall stability of the merged model.
        Stable = consistent activation patterns across layers.
        """
        stability_scores = []
        
        for layer_data in merged_activations.values():
            stability_scores.append(self._calculate_layer_stability(layer_data))
        
        if not stability_scores:
            return {"overall_stability": 0.5, "unstable_layers": [], "variance": 0}
        
        overall = float(np.mean(stability_scores))
        variance = float(np.var(stability_scores))
        
        # Layers with very low stability
        unstable = [
            idx for idx, score in enumerate(stability_scores)
            if score < 0.4
        ]
        
        return {
            "overall_stability": overall,
            "variance": variance,
            "unstable_layers": unstable,
            "consistency": 1.0 - variance  # High consistency = good
        }
    
    def _detect_novel_patterns(self, merged_activations: Dict) -> List[Dict]:
        """
        Detect novel activation patterns not present in baseline.
        These are the "creative" discoveries from evolution.
        """
        novel_patterns = []
        
        for layer_idx, merged_data in merged_activations.items():
            if layer_idx not in self.baseline_activations:
                continue
            
            baseline_data = self.baseline_activations[layer_idx]
            
            # Check for novel feature combinations
            baseline_features = set(baseline_data.get("active_features", []))
            merged_features = set(merged_data.get("active_features", []))
            
            # New features that weren't active before
            new_features = merged_features - baseline_features
            
            if len(new_features) > 0:
                effectiveness = len(new_features) / max(len(merged_features), 1)
                
                novel_patterns.append({
                    "layer": layer_idx,
                    "num_new_features": len(new_features),
                    "effectiveness": float(np.clip(effectiveness, 0, 1)),
                    "description": f"Layer {layer_idx}: {len(new_features)} novel feature activations"
                })
        
        return novel_patterns
    
    def _generate_recommendations(self, analysis: Dict, goal_score: float,
                                 baseline_score: float) -> Dict:
        """
        Generate specific recommendations for next generation mutations.
        """
        recommendations = {
            "preserve": [],
            "protect_with_cwp": [],
            "amplify": [],
            "investigate": [],
            "cautions": []
        }
        
        improvement = (goal_score - baseline_score) / (baseline_score + 1e-8)
        
        # If this merge beat baseline significantly
        if improvement > 0.05:  # 5% improvement
            recommendations["preserve"].append(
                "This merge approach works - preserve the general strategy"
            )
            
            # Identify what made it work
            for layer, changes in analysis["layer_changes"].items():
                if 0.3 < changes["divergence"] < 0.6:  # Moderate change
                    recommendations["preserve"].append(
                        f"Layer {layer}: Moderate changes helped (divergence={changes['divergence']:.2f})"
                    )
        
        # Protect unstable layers
        for layer in analysis["stability_metrics"]["unstable_layers"]:
            recommendations["protect_with_cwp"].append(
                f"Layer {layer}: Apply CWP to preserve stability"
            )
        
        # Amplify novel patterns
        for pattern in analysis["novel_patterns"]:
            if pattern["effectiveness"] > 0.15:
                recommendations["amplify"].append(pattern["description"])
        
        # Investigate interesting changes
        for layer, changes in analysis["layer_changes"].items():
            if changes["sparsity_change"] > 0.1:  # Higher sparsity
                recommendations["investigate"].append(
                    f"Layer {layer}: Increased sparsity by {changes['sparsity_change']:.2f} - try again with more aggression"
                )
        
        # Cautions
        if analysis["stability_metrics"]["overall_stability"] < 0.6:
            recommendations["cautions"].append(
                "Merge is relatively unstable - use CWP extensively in next iteration"
            )
        
        return recommendations
    
    def _generate_summary(self, analysis: Dict) -> str:
        """Human-readable introspection summary."""
        parts = []
        
        # Layer changes
        high_divergence_layers = [
            l for l, c in analysis["layer_changes"].items()
            if c["divergence"] > 0.5
        ]
        if high_divergence_layers:
            parts.append(f"Layers {high_divergence_layers} changed significantly")
        
        # Stability
        if analysis["stability_metrics"]["overall_stability"] > 0.75:
            parts.append("HIGH stability")
        elif analysis["stability_metrics"]["overall_stability"] < 0.5:
            parts.append("LOW stability")
        
        # Novel patterns
        if analysis["novel_patterns"]:
            effective_patterns = [p for p in analysis["novel_patterns"] if p["effectiveness"] > 0.15]
            if effective_patterns:
                parts.append(f"Found {len(effective_patterns)} effective novel patterns")
        
        return " | ".join(parts) if parts else "Standard merge"
    
    def _empty_introspection(self) -> Dict:
        """Return empty introspection when analysis fails."""
        return {
            "layer_changes": {},
            "capability_indicators": {},
            "stability_metrics": {"overall_stability": 0.5},
            "novel_patterns": [],
            "recommendations": {},
            "summary": "Analysis unavailable"
        }


class EvolutionWithIntrospection:
    """
    Evolution engine that learns from Scoped Model introspection.
    """
    
    def __init__(self, runner, scoped_introspector: ScopedModelIntrospection):
        self.runner = runner
        self.introspector = scoped_introspector
        self.generation_insights = []
        self.mutation_preferences = {}
    
    def run_generation(self, goal: str, base_models: List[str],
                      methods: List[str], cycle_num: int,
                      baseline_score: float) -> List[Dict]:
        """
        Execute one generation with adaptive guidance.
        """
        logger.info(f"Generation {cycle_num}: {len(methods)} methods, {len(base_models)} base models")
        
        # Determine randomness level based on cycle
        # Early cycles: guided (exploit), later cycles: more exploration
        randomness = 0.2 + (cycle_num * 0.08)
        randomness = min(randomness, 0.8)  # Cap at 80%
        
        logger.info(f"Randomness level: {randomness:.2f}")
        
        # Generate recipes with current guidance
        recipes = self.advisor.generate_recipes(
            goal=goal,
            base_models=base_models,
            methods=methods,
            num_variants=3,
            randomness=randomness,
            mutation_guidance=self.mutation_preferences  # Use prior introspection
        )
        
        results = []
        
        for recipe in recipes:
            try:
                # Execute merge
                merged_model_path = self.fusion_engine.run(recipe)
                
                # Evaluate
                goal_score = self.evaluate(merged_model_path, goal)
                
                # INTROSPECT with Scoped Model
                introspection = self.introspector.analyze_merge(
                    merged_model_path=merged_model_path,
                    goal_metric_score=goal_score,
                    baseline_score=baseline_score
                )
                
                result = {
                    "recipe": recipe,
                    "goal_score": goal_score,
                    "improvement": (goal_score - baseline_score) / (baseline_score + 1e-8),
                    "introspection": introspection,
                    "cycle": cycle_num
                }
                results.append(result)
                
                # Log with introspection
                self.db.log_experiment(
                    goal=goal,
                    method=recipe["method"],
                    score=goal_score,
                    introspection_data={
                        "summary": introspection["summary"],
                        "novel_patterns": len(introspection["novel_patterns"]),
                        "stability": introspection["stability_metrics"]["overall_stability"]
                    }
                )
                
                logger.info(f"  Recipe {recipe['method']} (var {recipe.get('variant_id', 1)}): score={goal_score:.3f} | {introspection['summary']}")
            
            except Exception as e:
                logger.error(f"Failed to execute recipe: {e}")
        
        # Extract guidance for next generation
        self.mutation_preferences = self._extract_guidance(results)
        self.generation_insights.append({
            "cycle": cycle_num,
            "num_successful": len([r for r in results if r["improvement"] > 0.05]),
            "best_score": max([r["goal_score"] for r in results]),
            "guidance": self.mutation_preferences
        })
        
        return results
    
    def _extract_guidance(self, results: List[Dict]) -> Dict:
        """Learn from this generation for next iteration."""
        successful = [r for r in results if r["improvement"] > 0.05]
        
        if not successful:
            logger.warning("No successful mutations this generation - increasing randomness")
            return {"strategy": "increase_randomness"}
        
        guidance = {
            "preserve_patterns": [],
            "novel_directions": [],
            "protect_layers": set(),
            "focus_capabilities": []
        }
        
        for result in successful:
            intro = result["introspection"]
            
            # Preserve what worked
            guidance["preserve_patterns"].append(result["recipe"]["method"])
            
            # Explore novel patterns
            for pattern in intro["novel_patterns"]:
                if pattern["effectiveness"] > 0.1:
                    guidance["novel_directions"].append(pattern)
            
            # Protect unstable layers
            for layer in intro["stability_metrics"]["unstable_layers"]:
                guidance["protect_layers"].add(layer)
        
        guidance["protect_layers"] = list(guidance["protect_layers"])
        
        logger.info(f"Extracted guidance: {len(guidance['preserve_patterns'])} pattern types to preserve")
        
        return guidance
