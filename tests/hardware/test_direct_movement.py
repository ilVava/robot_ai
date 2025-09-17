#!/usr/bin/env python3
"""
Direct Movement Test - Robot AI
Test movimento diretto senza safety monitor interference

Usage: python3 test_direct_movement.py
"""

import asyncio
import sys
import yaml
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from perception.sensor_manager import SensorManager
from action.motor_controller import MotorController, MotorDirection
from action.led_controller import LEDController, LEDExpression

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

async def test_direct_movement():
    """Test movimento diretto senza safety monitor"""
    logger.info("🤖 ROBOT AI - DIRECT MOVEMENT TEST")
    logger.info("=" * 50)

    # Load config
    config = await load_config()
    config['simulation_mode'] = False  # Hardware mode

    # Initialize solo i componenti necessari
    motor_controller = MotorController(config)
    led_controller = LEDController(config)
    sensor_manager = SensorManager(config, simulation_mode=False)

    try:
        # 1. Initialize motor controller
        logger.info("🔧 Initializing motor controller...")
        success = await motor_controller.initialize()
        if not success:
            logger.error("❌ Motor controller initialization failed!")
            return

        await asyncio.sleep(1.0)

        # 2. Initialize LED controller
        logger.info("💡 Initializing LED controller...")
        led_controller.set_arduino_serial(motor_controller)
        success = await led_controller.initialize()
        if not success:
            logger.error("❌ LED controller initialization failed!")
            return

        await asyncio.sleep(1.0)

        # 3. Initialize sensors
        logger.info("📡 Initializing sensors...")
        sensor_manager.set_arduino_serial(motor_controller)
        await sensor_manager.initialize()

        logger.info("✅ All components initialized - Testing direct movement...")

        # 4. Resume from any emergency stops
        await motor_controller.resume_from_emergency()
        logger.info("🔓 Emergency stop cleared")

        # 5. Read distance for safety check
        sensor_summary = await sensor_manager.get_sensor_summary()
        distance = sensor_summary.get('distance_cm', 400)
        logger.info(f"📡 Current distance: {distance:.1f}cm")

        if distance < 30.0:
            logger.warning(f"⚠️ Object detected at {distance:.1f}cm - manual safety check needed")
            logger.info("Press Ctrl+C to abort if robot is near obstacles")
            await asyncio.sleep(3.0)

        # 6. TEST SEQUENCE - Movimenti graduali

        # Test 1: Forward movement
        logger.info("🧪 TEST 1: Forward movement (1.5s)")
        await led_controller.set_expression(LEDExpression.CURIOUS)
        success = await motor_controller.move_forward(speed=25)  # Slow speed
        if success:
            logger.info("✅ Forward command sent")
            await asyncio.sleep(1.5)  # Movement duration

            # Stop movement
            await motor_controller.stop()
            logger.info("🛑 Forward movement stopped")
        else:
            logger.warning("⚠️ Forward movement failed")

        await asyncio.sleep(1.0)

        # Test 2: Turn right
        logger.info("🧪 TEST 2: Turn right (1s)")
        await led_controller.set_expression(LEDExpression.PLAYFUL)
        success = await motor_controller.turn_right(speed=30)
        if success:
            logger.info("✅ Turn right command sent")
            await asyncio.sleep(1.0)  # Turn duration

            await motor_controller.stop()
            logger.info("🛑 Turn right stopped")
        else:
            logger.warning("⚠️ Turn right failed")

        await asyncio.sleep(1.0)

        # Test 3: Backward movement
        logger.info("🧪 TEST 3: Backward movement (1s)")
        await led_controller.set_expression(LEDExpression.ALERT)
        success = await motor_controller.move_backward(speed=20)  # Very slow
        if success:
            logger.info("✅ Backward command sent")
            await asyncio.sleep(1.0)  # Movement duration

            await motor_controller.stop()
            logger.info("🛑 Backward movement stopped")
        else:
            logger.warning("⚠️ Backward movement failed")

        await asyncio.sleep(1.0)

        # Test 4: Turn left
        logger.info("🧪 TEST 4: Turn left (1s)")
        await led_controller.set_expression(LEDExpression.HAPPY)
        success = await motor_controller.turn_left(speed=30)
        if success:
            logger.info("✅ Turn left command sent")
            await asyncio.sleep(1.0)

            await motor_controller.stop()
            logger.info("🛑 Turn left stopped")
        else:
            logger.warning("⚠️ Turn left failed")

        # Final celebration
        logger.info("🎉 DIRECT MOVEMENT TESTS COMPLETED!")
        await led_controller.set_expression(LEDExpression.HAPPY)
        await asyncio.sleep(2.0)

    except KeyboardInterrupt:
        logger.info("⏸️ Test interrupted by user")

    except Exception as e:
        logger.error(f"❌ Error during direct movement test: {e}")

    finally:
        # Cleanup
        logger.info("🛑 Stopping all movement...")
        await motor_controller.stop()
        await led_controller.set_expression(LEDExpression.OFF)
        await motor_controller.shutdown()
        logger.info("✅ Cleanup completed")

async def main():
    """Main function"""
    try:
        await test_direct_movement()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())