#!/usr/bin/env python3
"""
Physical Movement Test - Robot AI
Test movimento fisico del robot con controlli di sicurezza graduali

Usage: python3 test_physical_movement.py
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_config():
    """Carica configurazione"""
    config_path = Path(__file__).parent / 'config' / 'robot_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

async def test_physical_movement():
    """Test movimento fisico con safety controls"""
    logger.info("🤖 ROBOT AI - PHYSICAL MOVEMENT TEST")
    logger.info("=" * 50)

    # Load config
    config = await load_config()
    config['simulation_mode'] = False  # Hardware mode

    # Initialize system
    sensor_manager = SensorManager(config, simulation_mode=False)
    await sensor_manager.initialize()

    hw_manager = HardwareIntegrationManager(config, sensor_manager)
    success = await hw_manager.initialize()

    if not success:
        logger.error("❌ Hardware initialization failed!")
        return

    logger.info("✅ Robot hardware initialized - Testing physical movement...")

    try:
        # 1. Resume from any emergency stops
        logger.info("🔓 Clearing emergency stops...")
        await hw_manager.motor_controller.resume_from_emergency()
        await asyncio.sleep(1.0)

        # 2. Test movimento graduale - Forward 2 secondi
        logger.info("🧪 TEST 1: Forward movement (2s)")

        # Read sensors first
        sensor_summary = await sensor_manager.get_sensor_summary()
        distance = sensor_summary.get('distance_cm', 400)
        logger.info(f"📡 Current distance: {distance:.1f}cm")

        if distance > 50.0:  # Safe distance per movimento
            await hw_manager.express_emotion("curious", 0.5)
            success = await hw_manager.move_forward("curious", 2.0)
            if success:
                logger.info("✅ Forward movement successful!")
            else:
                logger.warning("⚠️ Forward movement blocked")
        else:
            logger.warning(f"⚠️ Object too close ({distance:.1f}cm) - skipping forward test")

        await asyncio.sleep(1.0)

        # 3. Test rotazione - Turn right 1 secondo
        logger.info("🧪 TEST 2: Right turn (1s)")
        await hw_manager.express_emotion("playful", 0.5)
        success = await hw_manager.turn_right("playful", 1.0)
        if success:
            logger.info("✅ Right turn successful!")
        else:
            logger.warning("⚠️ Right turn blocked")

        await asyncio.sleep(1.0)

        # 4. Test backward - 1 secondo
        logger.info("🧪 TEST 3: Backward movement (1s)")
        await hw_manager.express_emotion("cautious", 0.5)
        success = await hw_manager.move_backward("cautious", 1.0)
        if success:
            logger.info("✅ Backward movement successful!")
        else:
            logger.warning("⚠️ Backward movement blocked")

        await asyncio.sleep(1.0)

        # 5. Final celebration
        logger.info("🎉 Physical movement tests completed!")
        await hw_manager.express_emotion("playful", 2.0)

    except KeyboardInterrupt:
        logger.info("⏸️ Test interrupted by user")

    except Exception as e:
        logger.error(f"❌ Error during movement test: {e}")

    finally:
        # Always stop and cleanup
        logger.info("🛑 Stopping robot...")
        await hw_manager.stop_all()
        await hw_manager.shutdown()

async def main():
    """Main function"""
    try:
        await test_physical_movement()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())