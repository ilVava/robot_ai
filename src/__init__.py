"""
Robot AI - Autonomous Caterpillar Tank
======================================

A sophisticated AI-driven robot built on Keyestudio Caterpillar V3 hardware
with Raspberry Pi 5, featuring autonomous behavior, learning capabilities,
and emotional states simulation.

Author: Andrea Vavassori
Version: 0.1.0
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Andrea Vavassori"
__email__ = "your-email@example.com"
__license__ = "MIT"

# Core modules
from . import perception
from . import cognitive  
from . import memory
from . import emotion
from . import action

__all__ = [
    "perception",
    "cognitive", 
    "memory",
    "emotion", 
    "action"
]