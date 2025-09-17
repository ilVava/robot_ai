#!/usr/bin/env python3
"""
Basic Autonomy Test - Robot AI First Steps

Test basico di autonomia del robot:
- Leggi ultrasonico
- Muovi se safe
- Ruota se ostacolo
- LED expressions
- Emergency stop

Usage: python3 test_basic_autonomy.py
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

async def basic_autonomy_test():
    """Test autonomia basilare del robot"""
    logger.info("🤖 ROBOT AI - BASIC AUTONOMY TEST")
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

    logger.info("✅ Robot hardware initialized - Starting basic autonomy...")

    try:
        # Basic autonomy loop
        for step in range(20):  # 20 decision cycles
            logger.info(f"\n--- Decision Step {step + 1}/20 ---")

            # 1. Read sensors
            sensor_summary = await sensor_manager.get_sensor_summary()
            distance = sensor_summary.get('distance_cm', 400)
            light_levels = sensor_summary.get('light_levels', [500, 500, 500, 500])

            logger.info(f"📡 Sensors: Distance={distance:.1f}cm, Light={[int(l) for l in light_levels]}")

            # 2. Decide action based on distance
            if distance < 15.0:
                # EMERGENCY - Too close!
                logger.warning("🚨 EMERGENCY: Object too close!")
                await hw_manager.express_emotion("alert", 1.0)
                await hw_manager.emergency_stop()
                await asyncio.sleep(2.0)

                # Backup and turn
                logger.info("🔙 Backing up...")
                await hw_manager.move_backward("cautious", 1.0)
                await asyncio.sleep(0.5)

                logger.info("↪️ Turning right...")
                await hw_manager.turn_right("cautious", 1.5)

            elif distance < 30.0:
                # Obstacle detected - turn
                logger.info("⚠️ Obstacle detected - turning right")
                await hw_manager.express_emotion("cautious", 0.5)
                await hw_manager.turn_right("cautious", 1.0)

            else:
                # Safe to move forward
                logger.info("✅ Path clear - moving forward")
                await hw_manager.express_emotion("curious", 0.5)
                await hw_manager.move_forward("curious", 1.2)

            # 3. Small pause between decisions
            await asyncio.sleep(0.5)

            # 4. Check if we should continue
            if not hw_manager.is_safe():
                logger.warning("⚠️ Safety system triggered - stopping test")
                break

        logger.info("🏁 Basic autonomy test completed!")

    except KeyboardInterrupt:
        logger.info("⏸️ Test interrupted by user")

    except Exception as e:
        logger.error(f"❌ Error during autonomy test: {e}")

    finally:
        # Cleanup
        logger.info("🛑 Stopping robot...")
        await hw_manager.stop_all()
        await hw_manager.shutdown()

async def main():
    """Main function"""
    try:
        await basic_autonomy_test()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())