import logging
import os
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger("PipelineMerger")

class PipelineStage:
    """Single stage in a merge pipeline."""
    
    def __init__(self, stage_id: int, models: List[str], method: str, 
                 params: Optional[Dict] = None, output_name: Optional[str] = None):
        """
        Args:
            stage_id: Stage number (0-indexed)
            models: List of model paths/names to merge
            method: Merge method (slerp, ties, dare, task_arithmetic)
            params: Method-specific parameters
            output_name: Name for output (auto-generated if None)
        """
        self.stage_id = stage_id
        self.models = models
        self.method = method
        self.params = params or {}
        self.output_name = output_name or f"pipeline_stage_{stage_id}"
        self.result = None
        self.status = "pending"
        self.error = None
    
    def to_dict(self):
        return {
            "stage_id": self.stage_id,
            "models": self.models,
            "method": self.method,
            "params": self.params,
            "output_name": self.output_name,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }


class PipelineMerger:
    """
    Multi-stage merge pipelines (merge-of-merges).
    
    Enables:
    - Sequential merging: A+B → C, then C+D → E
    - Parallel branches: A+B → C, A+D → E, then C+E → F
    - Complex architectures: Design deep merge trees
    - Iterative refinement: Evaluate after each stage
    
    Example:
        stages = [
            PipelineStage(0, ["model_a", "model_b"], "slerp", {"alpha": 0.5}),
            PipelineStage(1, ["$0", "model_c"], "ties"),  # $0 = output of stage 0
            PipelineStage(2, ["$1", "model_d"], "dare")
        ]
        pipeline = PipelineMerger(stages)
        result = pipeline.execute(merger, runner)
    """
    
    def __init__(self, stages: List[PipelineStage], name: str = "default"):
        """
        Args:
            stages: List of PipelineStage objects
            name: Pipeline name
        """
        self.stages = stages
        self.name = name
        self.results = {}  # {stage_id: output_path}
        self.log = []
        self.created_at = datetime.now()
    
    def resolve_model_reference(self, ref: str) -> str:
        """
        Resolve model reference.
        - If starts with $, it's a stage reference: $0 = output of stage 0
        - Otherwise, it's a model path
        """
        if ref.startswith("$"):
            stage_id = int(ref[1:])
            if stage_id not in self.results:
                raise ValueError(f"Stage {stage_id} not executed yet")
            return self.results[stage_id]
        return ref
    
    def execute(self, merger, runner, evaluate_fn=None):
        """
        Execute the pipeline sequentially.
        
        Args:
            merger: MergeKitWrapper instance
            runner: TaskRunner instance
            evaluate_fn: Optional evaluation function to run after each stage
                        signature: evaluate_fn(model_path) -> score
                        
        Returns:
            Final output path, or None if failed
        """
        logger.info(f"Executing pipeline '{self.name}' with {len(self.stages)} stages")
        
        try:
            for stage in self.stages:
                logger.info(f"Stage {stage.stage_id}: {stage.method} merging")
                logger.info(f"  Models: {stage.models}")
                
                # Resolve model references
                resolved_models = [self.resolve_model_reference(m) for m in stage.models]
                logger.info(f"  Resolved: {resolved_models}")
                
                # Execute merge based on method
                try:
                    if stage.method == "task_arithmetic":
                        result = self._merge_task_arithmetic(resolved_models, stage.params)
                    else:
                        # Use mergekit wrapper
                        result = self._merge_mergekit(merger, resolved_models, stage, runner)
                    
                    if result is None:
                        raise Exception(f"Merge failed for stage {stage.stage_id}")
                    
                    # Store result
                    self.results[stage.stage_id] = result
                    stage.result = result
                    stage.status = "complete"
                    
                    # Optional evaluation
                    if evaluate_fn:
                        logger.info(f"Evaluating stage {stage.stage_id} output...")
                        score = evaluate_fn(result)
                        self.log.append({
                            "stage": stage.stage_id,
                            "method": stage.method,
                            "status": "complete",
                            "output": result,
                            "score": score
                        })
                        logger.info(f"  Score: {score:.4f}")
                    else:
                        self.log.append({
                            "stage": stage.stage_id,
                            "method": stage.method,
                            "status": "complete",
                            "output": result
                        })
                    
                except Exception as e:
                    logger.error(f"Stage {stage.stage_id} failed: {e}")
                    stage.status = "failed"
                    stage.error = str(e)
                    self.log.append({
                        "stage": stage.stage_id,
                        "method": stage.method,
                        "status": "failed",
                        "error": str(e)
                    })
                    return None
            
            final_output = self.results[len(self.stages) - 1]
            logger.info(f"Pipeline complete! Final output: {final_output}")
            return final_output
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _merge_task_arithmetic(self, models: List[str], params: Dict):
        """Execute task arithmetic merge."""
        logger.info(f"Executing task arithmetic merge...")
        
        try:
            from breeding_vat.modules.merge.task_arithmetic import TaskArithmeticMerger
        except ImportError:
            logger.error("TaskArithmeticMerger not available")
            return None
        
        try:
            ta_merger = TaskArithmeticMerger()
            
            if len(models) < 2:
                raise ValueError("Task arithmetic needs at least 2 models")
            
            base_model = models[0]
            task_models = {}
            
            # Use provided weights or default to equal
            if "weights" in params:
                weights = params["weights"]
                task_models = {models[i+1]: weights[i] for i in range(len(models)-1)}
            else:
                default_weight = 1.0 / (len(models) - 1)
                task_models = {models[i+1]: default_weight for i in range(len(models)-1)}
            
            output_path = f"breeding_vat/data/merged_models/ta_{int(datetime.now().timestamp())}"
            result = ta_merger.merge(base_model, task_models, output_path)
            return result
            
        except Exception as e:
            logger.error(f"Task arithmetic merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _merge_mergekit(self, merger, models: List[str], stage: PipelineStage, runner):
        """Execute mergekit-based merge (SLERP/TIES/DARE)."""
        logger.info(f"Executing mergekit merge ({stage.method})...")
        
        try:
            if len(models) < 2:
                raise ValueError("Merge needs at least 2 models")
            
            base_model = models[0]
            merge_models = models[1:]
            
            # Prepare parameters
            params = stage.params.copy()
            if "base_weight" in params:
                params[base_model] = {"weight": params.pop("base_weight")}
            
            # Set default weights if not provided
            if not params:
                default_weight = 1.0 / len(merge_models)
                for m in merge_models:
                    params[m] = {"weight": default_weight}
            
            output_name = stage.output_name
            
            # Create merge config
            config_path = merger.create_config(
                stage.method.lower(),
                base_model,
                [base_model] + merge_models,
                params
            )
            
            # Run merge
            result = merger.run_merge(config_path, output_name)
            return result
            
        except Exception as e:
            logger.error(f"Mergekit merge failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_config(self, output_path: str):
        """Save pipeline configuration to JSON."""
        config = {
            "name": self.name,
            "created_at": str(self.created_at),
            "stages": [s.to_dict() for s in self.stages],
            "log": self.log
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Pipeline config saved: {output_path}")
    
    @staticmethod
    def load_config(config_path: str) -> 'PipelineMerger':
        """Load pipeline configuration from JSON."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        stages = [
            PipelineStage(
                s['stage_id'],
                s['models'],
                s['method'],
                s.get('params'),
                s.get('output_name')
            )
            for s in config['stages']
        ]
        
        pipeline = PipelineMerger(stages, config['name'])
        pipeline.log = config.get('log', [])
        logger.info(f"Loaded pipeline: {config_path}")
        return pipeline
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "created_at": str(self.created_at),
            "num_stages": len(self.stages),
            "stages": [s.to_dict() for s in self.stages],
            "results": self.results,
            "log": self.log
        }


# Preset pipeline examples

def create_reasoning_pipeline():
    """Create a pipeline optimized for reasoning."""
    stages = [
        PipelineStage(
            0,
            ["Qwen/Qwen2.5-0.5B-Instruct", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"],
            "slerp",
            {"alpha": 0.6},
            "reasoning_stage1"
        ),
        PipelineStage(
            1,
            ["$0", "Jackrong/Qwen3.5-4B-Claude-4.6-Opus-Reasoning-Distilled"],
            "task_arithmetic",
            {"weights": [0.5]},
            "reasoning_final"
        )
    ]
    return PipelineMerger(stages, "reasoning_pipeline")


def create_code_pipeline():
    """Create a pipeline optimized for code generation."""
    stages = [
        PipelineStage(
            0,
            ["Qwen/Qwen2.5-1.5B-Instruct", "bigatuna/Qwen3-1.7B-Sushi-Coder"],
            "ties",
            {},
            "code_stage1"
        ),
        PipelineStage(
            1,
            ["$0", "Qwen/Qwen2.5-0.5B-Instruct"],
            "slerp",
            {"alpha": 0.7},
            "code_final"
        )
    ]
    return PipelineMerger(stages, "code_pipeline")


def create_balanced_pipeline():
    """Create a balanced multi-expert pipeline."""
    stages = [
        # Stage 0: Merge baseline + reasoning
        PipelineStage(
            0,
            ["Qwen/Qwen2.5-0.5B-Instruct", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"],
            "slerp",
            {"alpha": 0.5},
            "balanced_reasoning"
        ),
        # Stage 1: Merge baseline + code
        PipelineStage(
            1,
            ["Qwen/Qwen2.5-1.5B-Instruct", "bigatuna/Qwen3-1.7B-Sushi-Coder"],
            "ties",
            {},
            "balanced_code"
        ),
        # Stage 2: Combine reasoning + code results
        PipelineStage(
            2,
            ["$0", "$1"],
            "task_arithmetic",
            {"weights": [0.5]},
            "balanced_final"
        )
    ]
    return PipelineMerger(stages, "balanced_pipeline")
