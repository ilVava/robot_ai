#!/usr/bin/env python3
"""
Test Script - Hardware Integration Phase 6B

Test completo dell'integrazione hardware Robot AI:
- Motor Controller + Arduino communication
- LED Controller expressions
- Safety Monitor real-time monitoring
- Sensor Manager hardware integration
- Coordinated operations

Usage:
  python3 test_hardware_integration.py --simulation  # Test simulation mode
  python3 test_hardware_integration.py --hardware    # Test with real hardware
"""

import asyncio
import sys
import yaml
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from perception.sensor_manager import SensorManager
from action.hardware_integration import HardwareIntegrationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_config():
    """Carica configurazione dal file YAML"""
    config_path = Path(__file__).parent / 'config' / 'robot_config.yaml'

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config

async def test_simulation_mode():
    """Test in modalità simulation"""
    logger.info("🎮 Testing Hardware Integration - SIMULATION MODE")

    config = await load_config()
    config['simulation_mode'] = True

    # Create sensor manager
    sensor_manager = SensorManager(config, simulation_mode=True)
    await sensor_manager.initialize()

    # Create hardware integration manager
    hw_manager = HardwareIntegrationManager(config, sensor_manager)

    # Initialize
    success = await hw_manager.initialize()
    logger.info(f"Initialization: {'✅ SUCCESS' if success else '❌ FAILED'}")

    if success:
        # Test sequence
        logger.info("🧪 Running test sequence...")

        # Test 1: Express emotions
        await hw_manager.express_emotion("curious", 1.0)
        await asyncio.sleep(0.5)

        await hw_manager.express_emotion("playful", 1.0)
        await asyncio.sleep(0.5)

        # Test 2: Coordinated movements (simulation)
        await hw_manager.move_forward("curious", 1.0)
        await asyncio.sleep(0.5)

        await hw_manager.turn_left("playful", 0.5)
        await asyncio.sleep(0.5)

        await hw_manager.move_backward("cautious", 0.8)
        await asyncio.sleep(0.5)

        await hw_manager.turn_right("focused", 0.5)
        await asyncio.sleep(0.5)

        # Test 3: Safety system
        logger.info("Testing emergency stop...")
        await hw_manager.emergency_stop()
        await asyncio.sleep(1.0)

        # Test 4: System status
        status = await hw_manager.get_system_status()
        logger.info("System Status:")
        logger.info(f"  - Operational: {status.get('is_operational')}")
        logger.info(f"  - Safety Level: {status.get('safety', {}).get('level', 'unknown')}")
        logger.info(f"  - Total Movements: {status.get('stats', {}).get('total_movements', 0)}")
        logger.info(f"  - Total Expressions: {status.get('stats', {}).get('total_expressions', 0)}")

        logger.info("✅ Simulation test completed successfully!")

    # Cleanup
    await hw_manager.shutdown()

async def test_hardware_mode():
    """Test con hardware reale"""
    logger.info("🤖 Testing Hardware Integration - HARDWARE MODE")

    config = await load_config()
    config['simulation_mode'] = False

    # Create sensor manager
    sensor_manager = SensorManager(config, simulation_mode=False)
    await sensor_manager.initialize()

    # Create hardware integration manager
    hw_manager = HardwareIntegrationManager(config, sensor_manager)

    # Initialize (this will connect to Arduino)
    logger.info("Connecting to Arduino...")
    success = await hw_manager.initialize()
    logger.info(f"Hardware Initialization: {'✅ SUCCESS' if success else '❌ FAILED'}")

    if success:
        # Test sequence con hardware reale
        logger.info("🧪 Running hardware test sequence...")

        # Test 1: LED expressions
        logger.info("Testing LED expressions...")
        await hw_manager.express_emotion("curious", 2.0)
        await asyncio.sleep(1.0)

        await hw_manager.express_emotion("alert", 1.5)
        await asyncio.sleep(1.0)

        # Test 2: Safe movement test (short duration)
        if hw_manager.is_safe():
            logger.info("Testing safe movement...")
            await hw_manager.move_forward("curious", 0.5)  # 0.5s forward
            await asyncio.sleep(1.0)

            await hw_manager.turn_left("playful", 0.3)  # 0.3s turn
            await asyncio.sleep(1.0)

            await hw_manager.stop_all()
        else:
            logger.warning("⚠️ Movement skipped - safety system not ready")

        # Test 3: Sensor readings
        logger.info("Testing sensor readings...")
        for i in range(5):
            if sensor_manager:
                sensor_summary = await sensor_manager.get_sensor_summary()
                distance = sensor_summary.get('distance_cm')
                light_levels = sensor_summary.get('light_levels')

                logger.info(f"  Reading {i+1}: Distance={distance:.1f}cm, Light={light_levels}")
            await asyncio.sleep(0.5)

        # Test 4: System status
        status = await hw_manager.get_system_status()
        logger.info("Hardware System Status:")
        logger.info(f"  - Motor Status: {status.get('motor', {}).get('python_motor_state', {})}")
        logger.info(f"  - LED Status: {status.get('led', {}).get('current_expression', 'unknown')}")
        logger.info(f"  - Safety Level: {status.get('safety', {}).get('level', 'unknown')}")
        logger.info(f"  - Sensor Distance: {status.get('sensors', {}).get('distance_cm', 'N/A')}cm")

        logger.info("✅ Hardware test completed successfully!")

    # Cleanup
    await hw_manager.shutdown()

async def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python3 test_hardware_integration.py [--simulation|--hardware]")
        sys.exit(1)

    mode = sys.argv[1]

    try:
        if mode == '--simulation':
            await test_simulation_mode()
        elif mode == '--hardware':
            await test_hardware_mode()
        else:
            print("Invalid mode. Use --simulation or --hardware")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())