import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger("MethodPredictor")

class ExperimentDatabase:
    """
    Track all merge experiments for learning which methods work best.
    Enables predicting optimal merge methods for new goals.
    """
    
    def __init__(self, db_path="breeding_vat/data/experiments.db"):
        self.db_path = db_path
        self._init_schema()
    
    def _init_schema(self):
        """Initialize experiment tracking schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                base_models TEXT NOT NULL,  -- JSON array
                merge_method TEXT NOT NULL,
                parameters TEXT,  -- JSON
                output_model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration_seconds FLOAT,
                success BOOLEAN DEFAULT 1
            )
        """)
        
        # Evaluation scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eval_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                score FLOAT,
                metric_name TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
        """)
        
        # Method recommendations cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS method_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_hash TEXT UNIQUE,
                recommended_methods TEXT,  -- JSON array of methods + confidence
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Experiment database initialized: {self.db_path}")
    
    def log_experiment(self, goal: str, base_models: List[str], 
                      method: str, params: Optional[Dict] = None,
                      output_model: Optional[str] = None,
                      duration: Optional[float] = None,
                      success: bool = True) -> int:
        """
        Log a merge experiment to database.
        
        Returns:
            Experiment ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO experiments 
            (goal, base_models, merge_method, parameters, output_model, duration_seconds, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            goal,
            json.dumps(base_models),
            method,
            json.dumps(params or {}),
            output_model,
            duration,
            success
        ))
        
        exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Logged experiment {exp_id}: {method} for goal '{goal}'")
        return exp_id
    
    def log_scores(self, experiment_id: int, scores: Dict[str, float]):
        """
        Log evaluation scores for an experiment.
        
        Args:
            experiment_id: ID from log_experiment()
            scores: Dict of {task_name: score}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for task_name, score in scores.items():
            cursor.execute("""
                INSERT INTO eval_scores (experiment_id, task_name, score)
                VALUES (?, ?, ?)
            """, (experiment_id, task_name, score))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged {len(scores)} scores for experiment {experiment_id}")
    
    def get_experiments_for_goal(self, goal: str, limit: int = 20) -> List[Dict]:
        """
        Retrieve past experiments for a similar goal.
        
        Args:
            goal: Goal description (uses fuzzy matching)
            limit: Max results
            
        Returns:
            List of experiment records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple substring matching (can be upgraded to fuzzy)
        query = "%{}%".format(goal.lower())
        
        cursor.execute("""
            SELECT id, goal, base_models, merge_method, parameters, 
                   timestamp, success
            FROM experiments
            WHERE LOWER(goal) LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "goal": row[1],
                "base_models": json.loads(row[2]),
                "method": row[3],
                "parameters": json.loads(row[4]),
                "timestamp": row[5],
                "success": row[6]
            })
        
        conn.close()
        return results
    
    def get_method_success_rate(self, method: str, goal_keyword: Optional[str] = None) -> float:
        """
        Get success rate for a method overall or for a goal type.
        
        Args:
            method: Merge method name
            goal_keyword: Optional goal keyword to filter
            
        Returns:
            Success rate (0-1)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if goal_keyword:
            query = "%{}%".format(goal_keyword.lower())
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)
                FROM experiments
                WHERE merge_method=? AND LOWER(goal) LIKE ?
            """, (method, query))
        else:
            cursor.execute("""
                SELECT COUNT(*), SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)
                FROM experiments
                WHERE merge_method=?
            """, (method,))
        
        total, successes = cursor.fetchone()
        conn.close()
        
        if total == 0:
            return 0.0
        
        return float(successes or 0) / total
    
    def get_top_methods_for_goal(self, goal: str, limit: int = 5) -> List[Tuple[str, float, float]]:
        """
        Get top merge methods for a goal based on historical performance.
        
        Returns:
            List of (method, avg_score, success_rate)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "%{}%".format(goal.lower())
        
        cursor.execute("""
            SELECT e.merge_method, AVG(es.score), COUNT(*), 
                   SUM(CASE WHEN e.success=1 THEN 1 ELSE 0 END)
            FROM experiments e
            LEFT JOIN eval_scores es ON e.id = es.experiment_id
            WHERE LOWER(e.goal) LIKE ?
            GROUP BY e.merge_method
            ORDER BY AVG(es.score) DESC
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            method, avg_score, total, successes = row
            success_rate = (float(successes or 0) / total) if total > 0 else 0.0
            results.append((
                method,
                float(avg_score or 0),
                success_rate
            ))
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM experiments")
        total_exps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT merge_method) FROM experiments")
        unique_methods = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT goal) FROM experiments")
        unique_goals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM experiments WHERE success=1")
        successful = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_experiments": total_exps,
            "unique_methods": unique_methods,
            "unique_goals": unique_goals,
            "success_rate": float(successful / total_exps) if total_exps > 0 else 0
        }


class MethodPredictor:
    """
    Predict optimal merge methods for a given goal using historical data.
    """
    
    def __init__(self, db_path="breeding_vat/data/experiments.db"):
        self.db = ExperimentDatabase(db_path)
    
    def predict_methods(self, goal: str, base_models: List[str],
                       top_n: int = 5) -> List[Dict]:
        """
        Predict best merge methods for a goal.
        
        Args:
            goal: Goal description (e.g., "code generation on 3B models")
            base_models: List of models to merge
            top_n: Number of recommendations
            
        Returns:
            List of recommendations: [
                {
                    "method": "ties",
                    "confidence": 0.92,
                    "avg_score": 0.78,
                    "success_rate": 0.95,
                    "num_past_uses": 23,
                    "reasoning": "TIES worked well for code tasks before"
                },
                ...
            ]
        """
        logger.info(f"Predicting methods for goal: {goal}")
        
        # Get past experiments for similar goals
        past_exps = self.db.get_experiments_for_goal(goal, limit=100)
        
        if not past_exps:
            logger.warning(f"No past experiments found for goal: {goal}")
            return self._get_default_recommendations()
        
        # Analyze methods
        method_stats = {}
        for exp in past_exps:
            method = exp["method"]
            if method not in method_stats:
                method_stats[method] = {
                    "total": 0,
                    "successes": 0,
                    "scores": []
                }
            
            method_stats[method]["total"] += 1
            if exp["success"]:
                method_stats[method]["successes"] += 1
        
        # Get scores for each method
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for method in method_stats:
            cursor.execute("""
                SELECT AVG(es.score)
                FROM experiments e
                JOIN eval_scores es ON e.id = es.experiment_id
                WHERE e.merge_method = ? AND LOWER(e.goal) LIKE ?
            """, (method, "%{}%".format(goal.lower())))
            
            avg_score = cursor.fetchone()[0] or 0
            method_stats[method]["avg_score"] = float(avg_score)
        
        conn.close()
        
        # Rank methods
        recommendations = []
        for method, stats in sorted(
            method_stats.items(),
            key=lambda x: x[1]["avg_score"],
            reverse=True
        )[:top_n]:
            
            success_rate = stats["successes"] / stats["total"] if stats["total"] > 0 else 0
            
            # Confidence: based on frequency, success rate, and performance
            confidence = (
                0.3 * (stats["total"] / 100) +  # Frequency
                0.5 * success_rate +            # Success rate
                0.2 * (stats["avg_score"] / 1.0)  # Performance
            )
            confidence = min(1.0, confidence)
            
            recommendations.append({
                "method": method,
                "confidence": round(confidence, 3),
                "avg_score": round(stats["avg_score"], 4),
                "success_rate": round(success_rate, 3),
                "num_past_uses": stats["total"],
                "reasoning": self._generate_reasoning(method, stats, goal)
            })
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _generate_reasoning(self, method: str, stats: Dict, goal: str) -> str:
        """Generate human-readable reasoning for a recommendation."""
        success_pct = stats["successes"] / stats["total"] * 100 if stats["total"] > 0 else 0
        
        if success_pct > 90:
            confidence_desc = "very reliable"
        elif success_pct > 75:
            confidence_desc = "reliable"
        elif success_pct > 50:
            confidence_desc = "moderately reliable"
        else:
            confidence_desc = "less reliable"
        
        if stats["total"] > 20:
            frequency_desc = "extensively tested"
        elif stats["total"] > 10:
            frequency_desc = "well-tested"
        else:
            frequency_desc = "tested"
        
        return (
            f"{method.upper()} is {confidence_desc} ({success_pct:.0f}% success rate) "
            f"and has been {frequency_desc} ({stats['total']} times) for {goal.lower()}"
        )
    
    def _get_default_recommendations(self) -> List[Dict]:
        """Return default recommendations when no historical data exists."""
        return [
            {
                "method": "ties",
                "confidence": 0.8,
                "avg_score": 0.0,
                "success_rate": 0.85,
                "num_past_uses": 0,
                "reasoning": "TIES is a reliable baseline method for model merging"
            },
            {
                "method": "dare",
                "confidence": 0.75,
                "avg_score": 0.0,
                "success_rate": 0.80,
                "num_past_uses": 0,
                "reasoning": "DARE (Drop And Rescale) works well for multi-task scenarios"
            },
            {
                "method": "task_arithmetic",
                "confidence": 0.7,
                "avg_score": 0.0,
                "success_rate": 0.75,
                "num_past_uses": 0,
                "reasoning": "Task Arithmetic is foundational and generally effective"
            }
        ]
