"""
Task definitions for Disaster Response Environment
3 difficulty levels with custom graders
"""

from typing import Dict, Any, Tuple
from server.disaster_data import generator

class DisasterTask:
    def __init__(self, difficulty: str, description: str, time_limit_hours: int, 
                 expected_lives_saved: float, expected_response_time: float):
        self.difficulty = difficulty
        self.description = description
        self.time_limit_hours = time_limit_hours
        self.expected_lives_saved = expected_lives_saved
        self.expected_response_time = expected_response_time
        self.previous_score = None
    
    def grade(self, actual_lives_saved: int, actual_response_time: float, 
              actual_efficiency: float, actual_fairness: float) -> Tuple[float, Dict]:
        """
        Grade the agent's performance on this task
        Returns (total_score, breakdown)
        """
        scores = {}
        
        # Lives saved (40%) - compare to expected
        lives_score = min(1.0, actual_lives_saved / self.expected_lives_saved)
        scores['lives_saved'] = lives_score
        
        # Response time (25%) - faster is better
        time_score = max(0, 1.0 - (actual_response_time / self.time_limit_hours))
        scores['response_time'] = time_score
        
        # Resource efficiency (15%)
        efficiency_score = actual_efficiency
        scores['resource_efficiency'] = efficiency_score
        
        # Fairness (10%)
        fairness_score = actual_fairness
        scores['fairness'] = fairness_score
        
        # Planning bonus (10%)
        planning_score = 0.5  # Base score, increased by strategic decisions
        scores['planning_depth'] = planning_score
        
        # Calculate weighted total
        total = (
            lives_score * 0.40 +
            time_score * 0.25 +
            efficiency_score * 0.15 +
            fairness_score * 0.10 +
            planning_score * 0.10
        )
        
        # Improvement bonus (up to +5% for learning)
        improvement_bonus = 0.0
        if self.previous_score is not None and total > self.previous_score:
            improvement_bonus = min(0.05, (total - self.previous_score) * 0.5)
            total += improvement_bonus
        
        self.previous_score = total
        
        return total, scores

def get_easy_task() -> DisasterTask:
    """Easy: Localized flood, 15 victims, 24 hours"""
    return DisasterTask(
        difficulty="easy",
        description="River flood affecting a small town. 15 victims need rescue. 3 resources available. 24-hour window.",
        time_limit_hours=24,
        expected_lives_saved=13,  # Expect 13/15 lives saved
        expected_response_time=12  # Average response time target: 12 hours
    )

def get_medium_task() -> DisasterTask:
    """Medium: Earthquake, 35 victims, 48 hours, dynamic events"""
    return DisasterTask(
        difficulty="medium",
        description="Earthquake in urban center. 35 victims, aftershocks expected. 8 resources available. 48-hour window.",
        time_limit_hours=48,
        expected_lives_saved=28,  # Expect 28/35 lives saved
        expected_response_time=24  # Average response time target: 24 hours
    )

def get_hard_task() -> DisasterTask:
    """Hard: Hurricane, 75 victims, 72 hours, cascading failures"""
    return DisasterTask(
        difficulty="hard",
        description="Category 4 hurricane. 75 victims, multiple zones, cascading infrastructure failures. 15 resources. 72-hour window.",
        time_limit_hours=72,
        expected_lives_saved=52,  # Expect 52/75 lives saved
        expected_response_time=36  # Average response time target: 36 hours
    )

def get_task_by_difficulty(difficulty: str) -> DisasterTask:
    """Get task by difficulty string"""
    tasks = {
        "easy": get_easy_task(),
        "medium": get_medium_task(),
        "hard": get_hard_task()
    }
    return tasks.get(difficulty, get_easy_task())

def get_all_tasks() -> Dict[str, DisasterTask]:
    """Return all tasks for API endpoint"""
    return {
        "easy": get_easy_task(),
        "medium": get_medium_task(),
        "hard": get_hard_task()
    }