"""
Emotion System - Robot AI
=========================

The emotion system handles behavioral states and personality including:
- Emotional state management (curious, cautious, playful, etc.)
- Behavioral parameter modulation based on emotional state
- LED expression generation
- Personality trait simulation
- Emotional transitions and triggers

This module gives the robot its "personality" and emotional responses.
"""

from .emotion_engine import EmotionEngine
from .behavioral_states import BehavioralStates
from .expression_manager import ExpressionManager
# from .personality_traits import PersonalityTraits      # TODO: Implementare

__all__ = [
    'EmotionEngine',
    'BehavioralStates',
    'ExpressionManager'
    # 'PersonalityTraits'    # TODO: Aggiungere quando implementato
]