"""
Memory System - Robot AI  
=========================

The memory system handles persistent data storage including:
- SLAM (Simultaneous Localization and Mapping)
- Experience database for learning
- Object recognition cache
- Spatial memory and navigation history
- Long-term and short-term memory management

This module provides the robot's memory capabilities.
"""

from .slam_system import SLAMSystem
from .experience_db import ExperienceDatabase
# from .spatial_memory import SpatialMemory          # TODO: Implementare  
# from .memory_manager import MemoryManager          # TODO: Implementare

__all__ = [
    'SLAMSystem',
    'ExperienceDatabase'
    # 'SpatialMemory',         # TODO: Aggiungere quando implementato
    # 'MemoryManager'          # TODO: Aggiungere quando implementato
]