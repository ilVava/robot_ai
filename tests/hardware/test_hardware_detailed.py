#!/usr/bin/env python3
"""
Detailed Hardware Test - Robot AI Phase 6B

Test dettagliato dell'hardware integration con analisi completa:
- Arduino communication protocol testing
- Motor control sequences
- LED expression coordination
- Safety monitoring in action
- Sensor data processing
- Performance metrics

Questo test simula tutti i protocolli che verranno usati sul RPi5 reale.
"""

import asyncio
import sys
import yaml
import logging
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from perception.sensor_manager import SensorManager
from action.hardware_integration import HardwareIntegrationManager

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Debug level per vedere tutti i comandi
    format='%(asctime)s - %(name)20s - %(levelname)8s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_config():
    """Carica configurazione"""
    config_path = Path(__file__).parent / 'config' / 'robot_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

async def test_arduino_protocol():
    """Test protocollo Arduino dettagliato"""
    logger.info("🔌 TESTING ARDUINO PROTOCOL")

    config = await load_config()

    # Create motor controller
    from action.motor_controller import MotorController
    motor_controller = MotorController(config)

    # Initialize (will use mock in MacBook)
    success = await motor_controller.initialize()
    logger.info(f"Arduino Connection: {'✅ SUCCESS' if success else '❌ FAILED'}")

    if success:
        logger.info("\n📡 Testing Arduino Commands:")

        # Test 1: PING/PONG
        logger.info("Testing PING/PONG...")
        response = await motor_controller._send_command("PING", expect_response=True)
        logger.info(f"  PING → {response}")

        # Test 2: Speed setting
        logger.info("Testing SET_SPEED...")
        response = await motor_controller._send_command("SET_SPEED:50", expect_response=True)
        logger.info(f"  SET_SPEED:50 → {response}")

        # Test 3: Movement commands
        movements = ["MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT", "STOP"]
        for move in movements:
            logger.info(f"Testing {move}...")
            response = await motor_controller._send_command(move, expect_response=True)
            logger.info(f"  {move} → {response}")

        # Test 4: Status query
        logger.info("Testing STATUS...")
        response = await motor_controller._send_command("STATUS", expect_response=True)
        logger.info(f"  STATUS → {response}")

        # Test 5: LED patterns
        logger.info("Testing LED patterns...")
        for pattern in range(4):
            cmd = f"LED_PATTERN:{pattern}"
            response = await motor_controller._send_command(cmd, expect_response=True)
            logger.info(f"  {cmd} → {response}")

    await motor_controller.shutdown()

async def test_coordinated_behavior():
    """Test comportamenti coordinati avanzati"""
    logger.info("🤖 TESTING COORDINATED ROBOT BEHAVIOR")

    config = await load_config()

    # Create full integration
    sensor_manager = SensorManager(config, simulation_mode=True)
    await sensor_manager.initialize()

    hw_manager = HardwareIntegrationManager(config, sensor_manager)
    success = await hw_manager.initialize()

    if success:
        logger.info("\n🎭 Testing Emotional Movement Sequences:")

        # Sequenza 1: Esplorazione curiosa
        logger.info("=== CURIOUS EXPLORATION ===")
        await hw_manager.move_forward("curious", 1.5)
        await asyncio.sleep(0.5)
        await hw_manager.turn_right("curious", 0.8)
        await asyncio.sleep(0.5)
        await hw_manager.move_forward("curious", 1.0)
        await asyncio.sleep(1.0)

        # Sequenza 2: Reazione cauta
        logger.info("=== CAUTIOUS REACTION ===")
        await hw_manager.express_emotion("alert", 1.0)
        await asyncio.sleep(0.5)
        await hw_manager.move_backward("cautious", 1.2)
        await asyncio.sleep(0.5)
        await hw_manager.turn_left("cautious", 0.6)
        await asyncio.sleep(1.0)

        # Sequenza 3: Gioco dinamico
        logger.info("=== PLAYFUL BEHAVIOR ===")
        await hw_manager.turn_left("playful", 0.4)
        await asyncio.sleep(0.2)
        await hw_manager.turn_right("playful", 0.4)
        await asyncio.sleep(0.2)
        await hw_manager.move_forward("playful", 0.8)
        await asyncio.sleep(0.5)
        await hw_manager.express_emotion("happy", 2.0)
        await asyncio.sleep(1.0)

        # Sequenza 4: Emergency stop test
        logger.info("=== EMERGENCY STOP TEST ===")
        # Start movimento
        logger.info("Starting movement...")
        move_task = asyncio.create_task(hw_manager.move_forward("focused", 3.0))

        # Emergency stop dopo 1 secondo
        await asyncio.sleep(1.0)
        logger.info("Triggering EMERGENCY STOP...")
        await hw_manager.emergency_stop()

        # Wait for movement task to complete
        try:
            await move_task
        except:
            pass

        await asyncio.sleep(1.0)

        # Test 5: Status monitoring
        logger.info("=== SYSTEM STATUS ANALYSIS ===")
        status = await hw_manager.get_system_status()

        logger.info("📊 Final System Status:")
        logger.info(f"  - Operational: {status.get('is_operational')}")
        logger.info(f"  - Safety Level: {status.get('safety', {}).get('level', 'unknown')}")
        logger.info(f"  - Total Movements: {status.get('stats', {}).get('total_movements', 0)}")
        logger.info(f"  - Total Expressions: {status.get('stats', {}).get('total_expressions', 0)}")
        logger.info(f"  - Safety Stops: {status.get('stats', {}).get('safety_stops', 0)}")

        # Motor details
        motor_status = status.get('motor', {})
        if motor_status:
            logger.info("🔧 Motor Status:")
            motor_state = motor_status.get('python_motor_state', {})
            logger.info(f"  - Current Direction: {motor_state.get('direction', 'unknown')}")
            logger.info(f"  - Speed: {motor_state.get('speed', 0)}")
            logger.info(f"  - Is Moving: {motor_state.get('is_moving', False)}")
            logger.info(f"  - Emergency Stopped: {motor_state.get('is_emergency_stopped', False)}")

        # LED details
        led_status = status.get('led', {})
        if led_status:
            logger.info("💡 LED Status:")
            logger.info(f"  - Current Expression: {led_status.get('current_expression', 'unknown')}")
            logger.info(f"  - Is Animating: {led_status.get('is_animating', False)}")

        # Safety details
        safety_status = status.get('safety', {})
        if safety_status:
            logger.info("🛡️ Safety Status:")
            logger.info(f"  - Active Alerts: {safety_status.get('active_alerts', [])}")
            logger.info(f"  - Is Monitoring: {safety_status.get('is_monitoring', False)}")

            safety_stats = safety_status.get('stats', {})
            if safety_stats:
                logger.info(f"  - Monitoring Loops: {safety_stats.get('monitoring_loops', 0)}")
                logger.info(f"  - Emergency Stops: {safety_stats.get('emergency_stops', 0)}")
                logger.info(f"  - Uptime: {safety_stats.get('uptime_seconds', 0):.1f}s")

        logger.info("✅ Detailed hardware test completed successfully!")

    await hw_manager.shutdown()

async def test_sensor_integration():
    """Test integrazione sensori dettagliata"""
    logger.info("📡 TESTING SENSOR INTEGRATION")

    config = await load_config()
    sensor_manager = SensorManager(config, simulation_mode=True)

    await sensor_manager.initialize()

    logger.info("\n📊 Sensor Data Simulation (10 readings):")
    for i in range(10):
        summary = await sensor_manager.get_sensor_summary()

        distance = summary.get('distance_cm')
        light_levels = summary.get('light_levels', [])
        lighting = summary.get('status', {}).get('lighting_conditions', 'unknown')
        obstacle = summary.get('status', {}).get('obstacle_detected', False)

        logger.info(f"  Reading {i+1:2d}: Distance={distance:6.1f}cm | " +
                   f"Light=[{','.join([f'{l:3.0f}' for l in light_levels])}] | " +
                   f"Lighting={lighting:8s} | Obstacle={'YES' if obstacle else 'NO '}")

        await asyncio.sleep(0.2)  # 5Hz readings

    # Statistics
    stats = sensor_manager.stats
    logger.info(f"\n📈 Sensor Statistics:")
    logger.info(f"  - Distance readings: {stats['distance_readings']}")
    logger.info(f"  - Light readings: {stats['light_readings']}")
    logger.info(f"  - Avg distance: {stats['avg_distance']:.1f}cm")
    logger.info(f"  - Avg light levels: {[f'{l:.0f}' for l in stats['avg_light_levels']]}")

    await sensor_manager.cleanup()

async def performance_benchmark():
    """Benchmark performance del sistema"""
    logger.info("⚡ PERFORMANCE BENCHMARK")

    config = await load_config()
    sensor_manager = SensorManager(config, simulation_mode=True)
    await sensor_manager.initialize()

    hw_manager = HardwareIntegrationManager(config, sensor_manager)
    await hw_manager.initialize()

    # Test performance movimento + lettura sensori
    logger.info("Testing movement + sensor reading performance...")

    start_time = time.time()
    operations = 0

    for cycle in range(20):  # 20 cicli
        # Movimento breve
        await hw_manager.move_forward("focused", 0.1)
        operations += 1

        # Lettura sensori
        await sensor_manager.get_sensor_summary()
        operations += 1

        # LED expression
        await hw_manager.express_emotion("curious", 0.1)
        operations += 1

    end_time = time.time()
    total_time = end_time - start_time

    logger.info(f"📊 Performance Results:")
    logger.info(f"  - Total operations: {operations}")
    logger.info(f"  - Total time: {total_time:.2f}s")
    logger.info(f"  - Operations/second: {operations/total_time:.1f}")
    logger.info(f"  - Average operation time: {(total_time/operations)*1000:.1f}ms")

    # System status finale
    status = await hw_manager.get_system_status()
    logger.info(f"  - Total movements: {status.get('stats', {}).get('total_movements', 0)}")
    logger.info(f"  - Total expressions: {status.get('stats', {}).get('total_expressions', 0)}")

    await hw_manager.shutdown()

async def main():
    """Main test suite"""
    logger.info("🚀 DETAILED HARDWARE INTEGRATION TEST SUITE")
    logger.info("=" * 60)

    try:
        # Test 1: Arduino Protocol
        await test_arduino_protocol()
        logger.info("\n" + "=" * 60)

        # Test 2: Sensor Integration
        await test_sensor_integration()
        logger.info("\n" + "=" * 60)

        # Test 3: Coordinated Behavior
        await test_coordinated_behavior()
        logger.info("\n" + "=" * 60)

        # Test 4: Performance Benchmark
        await performance_benchmark()
        logger.info("\n" + "=" * 60)

        logger.info("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("🤖 Robot AI hardware integration is READY!")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())