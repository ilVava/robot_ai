"""
Hardware Integration Manager - Robot AI Phase 6B

Coordina tutti i componenti hardware del robot:
- Motor Controller (movimento fisico)
- LED Controller (espressioni facciali)
- Safety Monitor (sicurezza in tempo reale)
- Sensor Manager (integrazione sensori)
- Arduino Serial Communication (protocollo unificato)

Fornisce interfaccia unificata per il sistema AI high-level.
Design: Async coordination con safety-first approach.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

# Import dei nostri nuovi moduli hardware
from .motor_controller import MotorController, MotorDirection
from .led_controller import LEDController, LEDExpression
from .safety_monitor import SafetyMonitor, SafetyLevel


class HardwareIntegrationManager:
    """Manager principale per integrazione hardware Robot AI"""

    def __init__(self, config: Dict[str, Any], sensor_manager=None):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Hardware components
        self.motor_controller = MotorController(config)
        self.led_controller = LEDController(config)
        self.safety_monitor = SafetyMonitor(config)

        # Sensor manager (from perception system)
        self.sensor_manager = sensor_manager

        # Integration state
        self.is_initialized = False
        self.is_operational = False
        self.simulation_mode = config.get('simulation_mode', False)

        # Stats
        self.stats = {
            'initialization_time': 0.0,
            'total_movements': 0,
            'total_expressions': 0,
            'safety_stops': 0
        }

        self.logger.info(f"HardwareIntegrationManager created - Simulation: {self.simulation_mode}")

    async def initialize(self) -> bool:
        """Inizializza tutti i componenti hardware in sequenza sicura"""
        try:
            import time
            start_time = time.time()

            self.logger.info("🚀 Starting hardware integration initialization...")

            if self.simulation_mode:
                self.logger.info("📱 Simulation mode - skipping hardware initialization")
                self.is_initialized = True
                self.is_operational = True
                return True

            # Step 1: Initialize Motor Controller (Arduino communication)
            self.logger.info("🔧 Step 1: Initializing Motor Controller...")
            motor_success = await self.motor_controller.initialize()
            if not motor_success:
                self.logger.error("❌ Motor Controller initialization failed")
                return False

            # Step 2: Connect LED Controller to same Arduino serial
            self.logger.info("💡 Step 2: Connecting LED Controller...")

            # Give Arduino time to finish motor controller commands
            await asyncio.sleep(1.0)

            self.led_controller.set_arduino_serial(self.motor_controller)
            led_success = await self.led_controller.initialize()
            if not led_success:
                self.logger.error("❌ LED Controller initialization failed")
                return False

            # Step 3: Connect Sensor Manager to Arduino serial
            if self.sensor_manager:
                self.logger.info("📡 Step 3: Connecting Sensor Manager...")
                self.sensor_manager.set_arduino_serial(self.motor_controller)
                sensor_success = await self.sensor_manager.initialize()
                if not sensor_success:
                    self.logger.error("❌ Sensor Manager initialization failed")
                    return False
            else:
                self.logger.warning("⚠️ No Sensor Manager provided - continuing without sensors")

            # Step 4: Initialize Safety Monitor (deve essere ultimo!)
            self.logger.info("🛡️ Step 4: Initializing Safety Monitor...")
            self.safety_monitor.set_robot_components(
                self.motor_controller,
                self.sensor_manager,
                self.led_controller
            )
            safety_success = await self.safety_monitor.initialize()
            if not safety_success:
                self.logger.error("❌ Safety Monitor initialization failed")
                return False

            # Step 5: Integration test
            self.logger.info("🧪 Step 5: Integration test...")
            test_success = await self._run_integration_test()
            if not test_success:
                self.logger.error("❌ Integration test failed")
                return False

            # Success!
            self.stats['initialization_time'] = time.time() - start_time
            self.is_initialized = True
            self.is_operational = True

            self.logger.info(f"✅ Hardware Integration completed successfully in {self.stats['initialization_time']:.1f}s")
            return True

        except Exception as e:
            self.logger.error(f"❌ Fatal error during hardware initialization: {e}")
            return False

    async def _run_integration_test(self) -> bool:
        """Test integrazione di tutti i sistemi"""
        try:
            self.logger.info("Running integration test sequence...")

            # Test 1: LED expression
            await self.led_controller.show_emotion("curious", duration=1.0)
            await asyncio.sleep(0.5)

            # Test 2: Motor status check (senza movimento)
            # CRITICO: Buffer flush prima del motor status check
            if hasattr(self.motor_controller, 'serial_connection'):
                self.motor_controller.serial_connection.flushInput()
                self.motor_controller.serial_connection.flushOutput()
                await asyncio.sleep(0.1)  # Arduino processing time

            motor_status = await self.motor_controller.get_status()
            # motor_status può essere dict o string - gestisci entrambi
            if isinstance(motor_status, dict):
                if any('error' in str(v).lower() for v in motor_status.values()):
                    self.logger.error(f"❌ Motor status error: {motor_status}")
                    return False
            else:
                if 'error' in str(motor_status).lower():
                    self.logger.error(f"❌ Motor status error: {motor_status}")
                    return False

            # Test 3: Sensor reading (se disponibili)
            if self.sensor_manager:
                sensor_summary = await self.sensor_manager.get_sensor_summary()
                if not sensor_summary.get('distance_cm') and not self.simulation_mode:
                    self.logger.warning("⚠️ Sensors not responding - continuing anyway")

            # Test 4: Safety monitor status
            safety_status = self.safety_monitor.get_safety_status()
            if safety_status.level not in [SafetyLevel.SAFE, SafetyLevel.WARNING]:
                self.logger.warning(f"⚠️ Safety level: {safety_status.level}")

            self.logger.info("✅ Integration test passed")
            return True

        except Exception as e:
            self.logger.error(f"Integration test failed: {e}")
            return False

    async def move_with_emotion(self, direction: str, emotion_state: str, duration: float = 1.0) -> bool:
        """Movimento coordinato con espressione emotiva"""
        try:
            if not self.is_operational:
                self.logger.error("Hardware not operational")
                return False

            # Safety check
            if not self.safety_monitor.is_safe_to_move():
                self.logger.warning("Movement blocked by safety monitor")
                return False

            # Map direction string to enum
            direction_map = {
                'forward': MotorDirection.FORWARD,
                'backward': MotorDirection.BACKWARD,
                'left': MotorDirection.TURN_LEFT,
                'right': MotorDirection.TURN_RIGHT,
                'stop': MotorDirection.STOP
            }

            motor_direction = direction_map.get(direction.lower())
            if not motor_direction:
                self.logger.error(f"Invalid direction: {direction}")
                return False

            self.logger.info(f"🤖 Moving {direction} with emotion '{emotion_state}' for {duration}s")

            # Start LED expression
            led_task = asyncio.create_task(
                self.led_controller.show_emotion(emotion_state, duration + 0.5)
            )

            # Execute movement
            if motor_direction != MotorDirection.STOP:
                success = await self.motor_controller.move_with_emotion(motor_direction, emotion_state)
                if success:
                    # Movement duration
                    await asyncio.sleep(duration)

                    # Stop movement
                    await self.motor_controller.stop()

                    self.stats['total_movements'] += 1
                    self.stats['total_expressions'] += 1

                    self.logger.info(f"✅ Movement completed: {direction} with {emotion_state}")
                    return True
                else:
                    await led_task  # Wait for LED to finish
                    return False
            else:
                # Just stop
                success = await self.motor_controller.stop()
                await led_task
                return success

        except Exception as e:
            self.logger.error(f"Error in coordinated movement: {e}")
            return False

    async def express_emotion(self, emotion_state: str, duration: Optional[float] = None) -> bool:
        """Espressione emotiva pura (solo LED)"""
        try:
            if not self.is_operational:
                return False

            success = await self.led_controller.show_emotion(emotion_state, duration)
            if success:
                self.stats['total_expressions'] += 1

            return success

        except Exception as e:
            self.logger.error(f"Error expressing emotion {emotion_state}: {e}")
            return False

    async def emergency_stop(self) -> bool:
        """Emergency stop coordinato di tutti i sistemi"""
        try:
            self.logger.warning("🚨 COORDINATED EMERGENCY STOP")

            # Trigger safety monitor emergency
            success = await self.safety_monitor.manual_emergency_stop()

            if success:
                self.stats['safety_stops'] += 1
                self.logger.info("✅ Emergency stop completed")
            else:
                self.logger.error("❌ Emergency stop failed")

            return success

        except Exception as e:
            self.logger.error(f"Error in emergency stop: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Status completo di tutto il sistema hardware"""
        try:
            status = {
                'timestamp': asyncio.get_event_loop().time(),
                'is_initialized': self.is_initialized,
                'is_operational': self.is_operational,
                'simulation_mode': self.simulation_mode,
                'stats': self.stats
            }

            if self.is_initialized:
                # Motor status
                status['motor'] = await self.motor_controller.get_status()

                # LED status
                status['led'] = await self.led_controller.get_status()

                # Safety status
                safety_status = self.safety_monitor.get_safety_status()
                status['safety'] = {
                    'level': safety_status.level.value,
                    'active_alerts': [alert.value for alert in safety_status.active_alerts],
                    'is_monitoring': safety_status.is_monitoring_active,
                    'stats': self.safety_monitor.get_safety_stats()
                }

                # Sensor status (se disponibili)
                if self.sensor_manager:
                    status['sensors'] = await self.sensor_manager.get_sensor_summary()

            return status

        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

    def is_ready(self) -> bool:
        """Check se il sistema è pronto per operazioni"""
        return self.is_initialized and self.is_operational

    def is_safe(self) -> bool:
        """Check se è sicuro operare"""
        if not self.is_operational:
            return False
        return self.safety_monitor.is_safe_to_move()

    async def shutdown(self):
        """Shutdown coordinato di tutti i componenti hardware"""
        try:
            self.logger.info("🔄 Starting coordinated hardware shutdown...")

            self.is_operational = False

            # Shutdown in ordine inverso dell'inizializzazione
            if self.safety_monitor:
                await self.safety_monitor.shutdown()

            if self.led_controller:
                await self.led_controller.shutdown()

            if self.motor_controller:
                await self.motor_controller.shutdown()

            if self.sensor_manager:
                await self.sensor_manager.cleanup()

            self.is_initialized = False

            self.logger.info("✅ Hardware integration shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    # Convenience methods for external use

    async def move_forward(self, emotion: str = "curious", duration: float = 1.0) -> bool:
        """Shortcut per movimento in avanti"""
        return await self.move_with_emotion("forward", emotion, duration)

    async def move_backward(self, emotion: str = "cautious", duration: float = 1.0) -> bool:
        """Shortcut per movimento indietro"""
        return await self.move_with_emotion("backward", emotion, duration)

    async def turn_left(self, emotion: str = "curious", duration: float = 0.5) -> bool:
        """Shortcut per rotazione sinistra"""
        return await self.move_with_emotion("left", emotion, duration)

    async def turn_right(self, emotion: str = "curious", duration: float = 0.5) -> bool:
        """Shortcut per rotazione destra"""
        return await self.move_with_emotion("right", emotion, duration)

    async def stop_all(self) -> bool:
        """Shortcut per stop totale"""
        return await self.move_with_emotion("stop", "focused", 0)