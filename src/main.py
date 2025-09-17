#!/usr/bin/env python3
"""
Robot AI - Main Entry Point
===========================

This is the main application entry point that initializes and coordinates
all robot systems including perception, cognition, memory, emotion and action.

Usage:
    python3 src/main.py [--config CONFIG_FILE] [--debug] [--no-hardware]
    
Author: Andrea Vavassori
"""

import argparse
import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import yaml
from colorama import Fore, Style, init as colorama_init

# Initialize colorama for colored terminal output
colorama_init()

class RobotAI:
    """Main Robot AI Controller Class"""
    
    def __init__(self, config_path: str, debug: bool = False, no_hardware: bool = False):
        self.config_path = config_path
        self.debug = debug
        self.no_hardware = no_hardware
        self.running = False
        
        # Load configuration
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize systems (will be implemented in phases)
        self.perception_system = None
        self.cognitive_system = None
        self.memory_system = None
        self.emotion_system = None
        self.action_system = None
        
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"{Fore.GREEN}✓ Configuration loaded from {self.config_path}{Style.RESET_ALL}")
            return config
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to load config: {e}{Style.RESET_ALL}")
            sys.exit(1)
            
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('system', {}).get('logging', {})
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_config.get('file', 'logs/robot.log')).parent
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        level = getattr(logging, log_config.get('level', 'INFO'))
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config.get('file', 'logs/robot.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    async def initialize_systems(self):
        """Initialize all robot systems"""
        self.logger.info("Initializing Robot AI Systems...")
        
        try:
            # Phase 1: Initialize hardware interfaces (if not in no-hardware mode)
            if not self.no_hardware:
                self.logger.info("Initializing hardware interfaces...")
                # TODO: Initialize hardware drivers
                
            # Phase 2: Initialize core systems
            self.logger.info("Initializing core AI systems...")
            
            # Initialize Memory System (database, SLAM, etc.)
            from memory import SLAMSystem, ExperienceDatabase
            self.slam_system = SLAMSystem(self.config, self.no_hardware)
            self.experience_db = ExperienceDatabase(self.config)
            await self.experience_db.initialize()
            
            # Initialize Perception System (camera, sensors, CV)
            from perception import CameraHandler, SensorManager  
            self.camera_handler = CameraHandler(self.config, self.no_hardware)
            await self.camera_handler.initialize()
            self.sensor_manager = SensorManager(self.config, self.no_hardware)
            await self.sensor_manager.initialize()
            
            # Initialize Emotion System (behavioral states)
            from emotion import BehavioralStates
            self.emotion_system = BehavioralStates(self.config, self.no_hardware)
            await self.emotion_system.initialize()
            
            # Initialize Cognitive System (decision making, AI)
            from cognitive import LearningAgent
            self.learning_agent = LearningAgent(self.config, self.experience_db)
            
            # Initialize Action System (motors, LED, expressions)
            # TODO: from action import ActionSystem
            # self.action_system = ActionSystem(self.config)
            
            self.logger.info(f"{Fore.GREEN}✓ All systems initialized successfully{Style.RESET_ALL}")
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Failed to initialize systems: {e}{Style.RESET_ALL}")
            raise
            
    async def main_loop(self):
        """Main robot control loop"""
        self.logger.info("Starting main robot control loop...")
        
        loop_frequency = self.config.get('system', {}).get('performance', {}).get('main_loop_frequency', 10)
        loop_period = 1.0 / loop_frequency
        
        while self.running:
            loop_start = time.time()
            
            try:
                # Phase 1: Perception - Gather sensor data (parallelizzato)
                camera_task = asyncio.create_task(self.camera_handler.capture_frame())
                sensor_task = asyncio.create_task(self.sensor_manager.get_sensor_summary())
                
                camera_frame, sensor_data = await asyncio.gather(camera_task, sensor_task)
                
                perception_data = {
                    "camera_frame": camera_frame is not None,
                    "distance_cm": sensor_data.get('distance_cm', 200),
                    "light_levels": sensor_data.get('light_levels', [500] * 4),
                    "objects_detected": [],  # TODO: Add when vision system ready
                    "motion_detected": False  # TODO: Add when motion detector ready
                }
                
                # Phase 2: Memory - Update spatial and experience memory
                slam_task = asyncio.create_task(self.slam_system.update_position(
                    perception_data['distance_cm'], 
                    perception_data['light_levels']
                ))
                
                # Phase 3: Emotion - Update emotional state (parallelizzato con SLAM)
                context = {
                    'battery_level': 80,  # TODO: Get real battery level
                    'simulation_mode': self.no_hardware
                }
                
                emotion_task = asyncio.create_task(self.emotion_system.update_from_sensors(
                    perception_data, context
                ))
                
                # Attendi completamento parallelo
                await slam_task
                behavioral_state = await emotion_task
                
                # Phase 4: Cognition - Make decisions
                behavior_params = await self.emotion_system.get_behavior_parameters()
                
                # Use current situation for learning
                situation = {
                    **perception_data,
                    **context,
                    **behavior_params
                }
                
                action, was_exploration = await self.learning_agent.choose_action(situation)
                
                # Calculate reward based on safety and exploration
                reward = 0.0
                if perception_data['distance_cm'] < 30 and action == 'stop':
                    reward = 1.0  # Good safety decision
                elif perception_data['distance_cm'] > 100 and action == 'move_forward':
                    reward = 0.8  # Good exploration
                
                # Learn from experience
                await self.learning_agent.learn_from_experience(
                    situation, action, reward, done=False
                )
                
                # Record experience in database
                await self.experience_db.record_experience(
                    situation, action, {}, 
                    'success' if reward > 0 else 'neutral', 
                    reward
                )
                
                decision = {"action": action, "parameters": behavior_params}
                
                # Phase 5: Action - Execute decisions (TODO: when action system ready)
                # if self.action_system:
                #     await self.action_system.execute(decision)
                
                # Debug output
                if self.debug:
                    current_emotion = behavioral_state.get('emotion', 'unknown')
                    self.logger.debug(f"Loop: emotion={current_emotion}, action={decision.get('action', 'none')}")
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                
            # Maintain loop frequency
            loop_time = time.time() - loop_start
            if loop_time < loop_period:
                await asyncio.sleep(loop_period - loop_time)
                
    async def start(self):
        """Start the robot AI system"""
        print(f"{Fore.CYAN}")
        print("=" * 60)
        print("🤖 ROBOT AI - Autonomous Caterpillar Tank")
        print("=" * 60)
        print(f"Version: 0.1.0")
        print(f"Hardware mode: {'Enabled' if not self.no_hardware else 'Simulation'}")
        print(f"Debug mode: {'Enabled' if self.debug else 'Disabled'}")
        print("=" * 60)
        print(f"{Style.RESET_ALL}")
        
        try:
            # Initialize all systems
            await self.initialize_systems()
            
            # Start main control loop
            self.running = True
            await self.main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
        except Exception as e:
            self.logger.error(f"Critical error: {e}")
            raise
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown all systems"""
        self.logger.info("Shutting down Robot AI...")
        self.running = False
        
        # Shutdown systems in reverse order
        # if self.action_system:
        #     await self.action_system.shutdown()
        
        if hasattr(self, 'learning_agent'):
            # Learning agent doesn't have shutdown method
            pass
            
        if hasattr(self, 'emotion_system'):
            await self.emotion_system.cleanup()
            
        if hasattr(self, 'sensor_manager'):
            await self.sensor_manager.cleanup()
            
        if hasattr(self, 'camera_handler'):
            await self.camera_handler.cleanup()
            
        if hasattr(self, 'slam_system'):
            await self.slam_system.cleanup()
            
        if hasattr(self, 'experience_db'):
            await self.experience_db.cleanup()
            
        self.logger.info(f"{Fore.GREEN}✓ Robot AI shutdown complete{Style.RESET_ALL}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n{Fore.YELLOW}Received signal {signum}, shutting down...{Style.RESET_ALL}")
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Robot AI - Autonomous Caterpillar Tank")
    parser.add_argument('--config', default='config/robot_config.yaml', 
                       help='Configuration file path')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--no-hardware', action='store_true',
                       help='Run in simulation mode (no hardware)')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start robot
    robot = RobotAI(
        config_path=args.config,
        debug=args.debug,
        no_hardware=args.no_hardware
    )
    
    # Run the robot
    try:
        asyncio.run(robot.start())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Robot AI stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Critical error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()