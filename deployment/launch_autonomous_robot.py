#!/usr/bin/env python3
"""
Autonomous Robot Launch - Robot AI
Avvia il robot in modalità completamente autonoma

Usage: python3 launch_autonomous_robot.py
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

async def autonomous_robot_life():
    """Ciclo di vita autonomo del robot"""
    logger.info("🤖 ROBOT AI - AUTONOMOUS LIFE BEGINS!")
    logger.info("=" * 60)

    # Load config
    config = await load_config()
    config['simulation_mode'] = False

    # Initialize components
    motor_controller = MotorController(config)
    led_controller = LEDController(config)
    sensor_manager = SensorManager(config, simulation_mode=False)

    try:
        # Initialize all systems
        logger.info("🔧 Initializing robot consciousness...")

        success = await motor_controller.initialize()
        if not success:
            logger.error("❌ Motor system failed to initialize!")
            return

        await asyncio.sleep(1.0)

        led_controller.set_arduino_serial(motor_controller)
        success = await led_controller.initialize()
        if not success:
            logger.error("❌ LED expression system failed!")
            return

        await asyncio.sleep(1.0)

        sensor_manager.set_arduino_serial(motor_controller)
        await sensor_manager.initialize()

        # Clear any emergency stops
        await motor_controller.resume_from_emergency()

        logger.info("✅ Robot AI is ALIVE and AUTONOMOUS!")
        logger.info("🧠 Beginning intelligent exploration...")

        # Express awakening
        await led_controller.set_expression(LEDExpression.CURIOUS)

        # MAIN AUTONOMOUS LOOP
        exploration_step = 1
        total_distance_traveled = 0.0

        while True:  # Infinite autonomous loop
            logger.info(f"\n🔍 --- EXPLORATION STEP {exploration_step} ---")

            # 1. Perceive environment
            sensor_summary = await sensor_manager.get_sensor_summary()
            distance = sensor_summary.get('distance_cm', 400)
            light_levels = sensor_summary.get('light_levels', [500, 500, 500, 500])

            logger.info(f"👁️ Perception: Distance={distance:.1f}cm, Light={[int(l) for l in light_levels]}")

            # 2. Decide behavior based on environment
            if distance < 15.0:
                # EMERGENCY - Too close to obstacle!
                logger.warning("🚨 DANGER: Object very close - emergency maneuvers!")
                await led_controller.set_expression(LEDExpression.ALERT)

                # Back up
                logger.info("⬅️ Emergency backup...")
                await motor_controller.move_backward(speed=20)
                await asyncio.sleep(1.0)
                await motor_controller.stop()

                # Turn away from obstacle
                logger.info("↪️ Emergency turn...")
                await motor_controller.turn_right(speed=25)
                await asyncio.sleep(1.5)
                await motor_controller.stop()

                total_distance_traveled += 0.5  # Estimate backup distance

            elif distance < 40.0:
                # Obstacle detected - cautious navigation
                logger.info("⚠️ Obstacle detected - intelligent navigation")
                await led_controller.set_expression(LEDExpression.ALERT)

                # Decide turn direction based on light levels (basic intelligence)
                left_light = sum(light_levels[:2]) / 2
                right_light = sum(light_levels[2:]) / 2

                if left_light > right_light:
                    logger.info("💡 Brighter on left - turning left toward light")
                    await motor_controller.turn_left(speed=25)
                else:
                    logger.info("💡 Brighter on right - turning right toward light")
                    await motor_controller.turn_right(speed=25)

                await asyncio.sleep(1.2)
                await motor_controller.stop()

            else:
                # Path clear - explore forward!
                logger.info("✅ Path clear - curious exploration forward")
                await led_controller.set_expression(LEDExpression.CURIOUS)

                # Vary speed based on confidence (distance)
                if distance > 200:
                    speed = 35  # Confident speed
                    duration = 2.0
                    logger.info("🚀 High confidence - fast exploration")
                else:
                    speed = 25  # Cautious speed
                    duration = 1.5
                    logger.info("🐾 Moderate confidence - careful advance")

                await motor_controller.move_forward(speed=speed)
                await asyncio.sleep(duration)
                await motor_controller.stop()

                # Estimate distance traveled
                estimated_distance = (speed / 40.0) * duration * 10  # Rough estimate
                total_distance_traveled += estimated_distance

            # 3. Brief pause for sensor stabilization
            await asyncio.sleep(0.5)

            # 4. Periodic status update
            if exploration_step % 10 == 0:
                logger.info(f"📊 STATUS: Step {exploration_step}, Estimated distance: {total_distance_traveled:.1f}cm")

                # Express satisfaction
                await led_controller.set_expression(LEDExpression.HAPPY)
                await asyncio.sleep(1.0)

            # 5. Occasional random exploration to avoid loops
            if exploration_step % 25 == 0:
                logger.info("🎲 Random exploration to discover new areas")
                await led_controller.set_expression(LEDExpression.PLAYFUL)

                # Random turn direction
                import random
                if random.choice([True, False]):
                    await motor_controller.turn_left(speed=30)
                else:
                    await motor_controller.turn_right(speed=30)

                await asyncio.sleep(1.0)
                await motor_controller.stop()

            exploration_step += 1

            # Safety check - if too many steps, take a rest
            if exploration_step > 200:
                logger.info("😴 Robot is tired - taking a rest")
                await led_controller.set_expression(LEDExpression.RESTING)
                await asyncio.sleep(10.0)
                exploration_step = 1  # Reset counter
                total_distance_traveled = 0.0

    except KeyboardInterrupt:
        logger.info("\n⏸️ Human intervention - robot stopping autonomous exploration")

    except Exception as e:
        logger.error(f"❌ Autonomous system error: {e}")

    finally:
        # Safe shutdown
        logger.info("🛑 Stopping autonomous exploration...")
        await motor_controller.stop()
        await led_controller.set_expression(LEDExpression.RESTING)
        await asyncio.sleep(2.0)
        await led_controller.set_expression(LEDExpression.OFF)
        await motor_controller.shutdown()
        logger.info("😴 Robot AI going to sleep... Goodbye!")

async def main():
    """Main function"""
    try:
        await autonomous_robot_life()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🤖 ROBOT AI - AUTONOMOUS EXPLORATION")
    print("Press Ctrl+C to stop the robot safely")
    print("=" * 50)
    asyncio.run(main())