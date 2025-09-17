"""
Cognitive System - Robot AI
===========================

The cognitive system handles high-level decision making including:
- Behavioral trees for decision logic
- Reinforcement learning for adaptive behavior
- Path planning and navigation
- Risk assessment and safety evaluation
- Goal setting and task management

This module represents the "brain" of the robot.
"""

from .learning_agent import LearningAgent
# from .decision_engine import DecisionEngine     # TODO: Implementare
# from .behavior_tree import BehaviorTree         # TODO: Implementare
# from .path_planner import PathPlanner           # TODO: Implementare

__all__ = [
    'LearningAgent'
    # 'DecisionEngine',    # TODO: Aggiungere quando implementato
    # 'BehaviorTree',      # TODO: Aggiungere quando implementato  
    # 'PathPlanner'        # TODO: Aggiungere quando implementato
]