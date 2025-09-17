"""
Perception System - Robot AI
============================

The perception system handles all sensory input processing including:
- Computer vision and camera processing
- Ultrasonic sensor data
- Light sensor readings  
- Motion detection
- Object recognition
- Sensor fusion

This module provides a unified interface for all perception capabilities.
"""

from .camera_handler import CameraHandler
from .sensor_manager import SensorManager  
# from .vision_processor import VisionProcessor  # TODO: Implementare
# from .motion_detector import MotionDetector    # TODO: Implementare

__all__ = [
    'CameraHandler',
    'SensorManager'
    # 'VisionProcessor',  # TODO: Aggiungere quando implementato
    # 'MotionDetector'    # TODO: Aggiungere quando implementato
]