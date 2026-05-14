"""
Goal-to-Benchmark Mapper

Converts user evolution goals into appropriate benchmark tasks.
Ensures experiments are evaluated on tasks aligned with their objectives.

Example:
  goal="Improve reasoning at 3B scale"
  → tasks=["arc_challenge", "arc_easy", "hellaswag"]
  
  goal="Code generation for Python"
  → tasks=["humaneval", "mbpp"] (when available in lm-eval)
  
  goal="Retrieval-augmented generation"
  → tasks=["natural_questions", "trivia_qa"] (when available)
"""

import logging
from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

logger = logging.getLogger("GoalAdvisor")

# Goal → Task mappings (expanded as lm-eval adds tasks)
GOAL_TASK_MAPPINGS = {
    # Reasoning goals
    "reasoning": ["arc_challenge", "arc_easy", "hellaswag", "winogrande"],
    "logic": ["arc_challenge", "arc_easy"],
    "math": ["gsm8k", "arc_challenge"],
    "problem_solving": ["arc_challenge", "hellaswag", "winogrande"],
    
    # Knowledge goals
    "knowledge": ["arc_challenge", "mmlu", "truthfulqa_mc"],
    "facts": ["arc_challenge", "truthfulqa_mc"],
    "commonsense": ["winogrande", "arc_easy"],
    
    # Language & instruction following
    "instruction": ["hellaswag", "arc_easy"],
    "language": ["hellaswag", "arc_challenge"],
    "clarity": ["arc_challenge", "winogrande"],
    
    # Specialized
    "code": ["humaneval", "mbpp"],  # When available
    "retrieval": ["natural_questions", "trivia_qa"],  # When available
    "rag": ["natural_questions", "trivia_qa"],
    "summarization": ["cnn_dailymail"],  # When available
    "generation": ["hellaswag", "arc_challenge"],
}

# Available tasks (subset of lm-eval harness)
AVAILABLE_TASKS = [
    "arc_easy",
    "arc_challenge",
    "hellaswag",
    "winogrande",
    "truthfulqa_mc",
    "mmlu",
]

# Optional tasks (may or may not be available depending on lm-eval version)
OPTIONAL_TASKS = [
    "humaneval",
    "mbpp",
    "gsm8k",
    "natural_questions",
    "trivia_qa",
    "cnn_dailymail",
]

# Weights for aggregating benchmark scores
SCORE_AGGREGATION = {
    "weighted_mean": 0.7,  # Default: weighted average of task scores
    "min": 0.1,            # Penalize weak spots
    "max": 0.2,            # Credit strong performance
}


class GoalAdvisor:
    """
    Analyzes user goals and recommends benchmark tasks.
    Ensures experiments evaluate on metrics that matter for their objective.
    """
    
    def __init__(self, ai_model_id: Optional[str] = None):
        """
        Args:
            ai_model_id: Optional LLM for semantic goal interpretation
                        (e.g., "Qwen/Qwen2.5-0.5B-Instruct")
        """
        self.ai_model_id = ai_model_id
        self.tokenizer = None
        self.model = None
    
    def load_ai(self):
        """Lazy-load LLM for goal interpretation."""
        if self.model is None and self.ai_model_id:
            logger.info(f"Loading GoalAdvisor model: {self.ai_model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.ai_model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.ai_model_id,
                torch_dtype="auto",
                device_map="auto"
            )
    
    def get_tasks_for_goal(self, goal: str) -> Dict:
        """
        Map a user goal to benchmark tasks.
        
        Args:
            goal: User's evolution objective (e.g., "Improve reasoning at 3B scale")
        
        Returns:
            Dict with:
            - tasks: List of benchmark task names
            - rationale: Explanation of why these tasks
            - tier: Recommended evaluation tier (fast/standard/full)
            - weights: Optional per-task weights
        """
        
        goal_lower = goal.lower()
        
        logger.info(f"Analyzing goal: {goal}")
        
        # Step 1: Keyword matching
        matched_keywords = []
        for keyword, tasks in GOAL_TASK_MAPPINGS.items():
            if keyword in goal_lower:
                matched_keywords.append((keyword, tasks))
        
        if matched_keywords:
            # Use first match (most specific)
            keyword, tasks = matched_keywords[0]
            tasks = [t for t in tasks if t in AVAILABLE_TASKS]
            
            if not tasks:
                tasks = ["arc_challenge", "hellaswag"]  # Fallback
            
            logger.info(f"Matched keyword '{keyword}' → tasks: {tasks}")
            
            return {
                "tasks": tasks,
                "rationale": f"Goal mentions '{keyword}'; these tasks evaluate that capability.",
                "tier": self._select_tier(goal_lower),
                "weights": self._get_weights(tasks),
                "matching_method": "keyword"
            }
        
        # Step 2: LLM-based semantic interpretation (optional)
        if self.ai_model_id:
            try:
                self.load_ai()
                result = self._interpret_goal_with_llm(goal)
                if result:
                    logger.info(f"LLM interpretation → tasks: {result['tasks']}")
                    return result
            except Exception as e:
                logger.warning(f"LLM interpretation failed: {e}, using defaults")
        
        # Step 3: Fallback to balanced default
        logger.info("No keyword match; using balanced default tasks")
        return {
            "tasks": ["arc_challenge", "hellaswag"],
            "rationale": "Default balanced eval (reasoning + language understanding)",
            "tier": "standard",
            "weights": self._get_weights(["arc_challenge", "hellaswag"]),
            "matching_method": "default"
        }
    
    def _select_tier(self, goal_lower: str) -> str:
        """
        Select evaluation tier based on goal complexity.
        
        - fast: Quick experiments (single keyword, iteration-heavy goals)
        - standard: Default (most goals)
        - full: Comprehensive eval for production goals
        """
        
        # Fast tier triggers
        if any(w in goal_lower for w in ["quick", "rapid", "fast", "speed", "iteration"]):
            return "fast"
        
        # Full tier triggers
        if any(w in goal_lower for w in ["production", "final", "comprehensive", "robust", "complete"]):
            return "full"
        
        # Default
        return "standard"
    
    def _get_weights(self, tasks: List[str]) -> Dict[str, float]:
        """
        Get per-task weights for score aggregation.
        
        Equal weights by default; can be customized per task.
        """
        if not tasks:
            return {}
        
        weight = 1.0 / len(tasks)
        return {task: weight for task in tasks}
    
    def _interpret_goal_with_llm(self, goal: str) -> Optional[Dict]:
        """
        Use LLM to semantically interpret a goal and recommend tasks.
        
        Returns task recommendation or None if interpretation fails.
        """
        try:
            prompt = (
                f"You are an AI evaluator for language models. "
                f"A user wants to evolve their model with this goal:\n\n"
                f"Goal: {goal}\n\n"
                f"Available benchmark tasks: {', '.join(AVAILABLE_TASKS)}\n\n"
                f"Recommend 2-3 tasks from the available list that best measure progress "
                f"toward this goal. Output ONLY the task names, comma-separated, no explanation.\n\n"
                f"Tasks:"
            )
            
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                out_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.5,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id,
                )
            
            response = self.tokenizer.decode(
                out_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()
            
            # Parse response: extract task names
            tasks = [t.strip() for t in response.split(",")]
            tasks = [t for t in tasks if t in AVAILABLE_TASKS]
            
            if tasks:
                return {
                    "tasks": tasks,
                    "rationale": f"LLM recommended for this goal: {', '.join(tasks)}",
                    "tier": self._select_tier(goal.lower()),
                    "weights": self._get_weights(tasks),
                    "matching_method": "llm"
                }
        
        except Exception as e:
            logger.debug(f"LLM interpretation error: {e}")
        
        return None
    
    def get_score_aggregator(self, goal: str, task_scores: Dict[str, float]) -> float:
        """
        Aggregate individual task scores into a single fitness metric.
        
        Args:
            goal: User goal (for context)
            task_scores: Dict of {task_name: score}
        
        Returns:
            Aggregated score (0-1)
        """
        
        if not task_scores:
            return 0.0
        
        # Get weights for these tasks
        goal_info = self.get_tasks_for_goal(goal)
        weights = goal_info.get("weights", {})
        
        # Weighted mean
        weighted_sum = 0.0
        total_weight = 0.0
        for task, score in task_scores.items():
            w = weights.get(task, 1.0 / len(task_scores))
            weighted_sum += score * w
            total_weight += w
        
        weighted_mean = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Apply aggregation strategy
        if task_scores:
            min_score = min(task_scores.values())
            max_score = max(task_scores.values())
            
            final = (
                SCORE_AGGREGATION["weighted_mean"] * weighted_mean +
                SCORE_AGGREGATION["min"] * min_score +
                SCORE_AGGREGATION["max"] * max_score
            )
            
            logger.debug(
                f"Score aggregation: weighted={weighted_mean:.3f}, "
                f"min={min_score:.3f}, max={max_score:.3f} → final={final:.3f}"
            )
            
            return final
        
        return 0.0


# Example usage
if __name__ == "__main__":
    advisor = GoalAdvisor()
    
    # Test goals
    test_goals = [
        "Improve reasoning at 3B scale",
        "Better code generation for Python",
        "Fast question answering",
        "Production-grade reasoning model",
    ]
    
    for goal in test_goals:
        result = advisor.get_tasks_for_goal(goal)
        print(f"\nGoal: {goal}")
        print(f"Tasks: {result['tasks']}")
        print(f"Tier: {result['tier']}")
        print(f"Rationale: {result['rationale']}")
