"""
Safety Monitor - Sistema di sicurezza e monitoraggio per Robot AI

Gestisce la sicurezza del robot in tempo reale:
- Monitoraggio costante sensori per pericoli (ostacoli, cadute)
- Emergency stop automatico in situazioni critiche
- Safety thresholds configurabili
- Coordinamento con motor controller per stop immediati
- Alert via LED per segnalazione visiva problemi

Design: AsyncIO loop continuo con priorità massima per safety
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass

class SafetyLevel(Enum):
    """Livelli di sicurezza del robot"""
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    EMERGENCY = "emergency"

class SafetyAlert(Enum):
    """Tipi di alert sicurezza"""
    OBSTACLE_TOO_CLOSE = "obstacle_too_close"
    SENSOR_FAILURE = "sensor_failure"
    COMMUNICATION_LOST = "communication_lost"
    MANUAL_EMERGENCY = "manual_emergency"
    SYSTEM_ERROR = "system_error"

@dataclass
class SafetyStatus:
    """Stato sicurezza corrente"""
    level: SafetyLevel
    active_alerts: List[SafetyAlert]
    last_sensor_reading: float
    emergency_stops_count: int
    is_monitoring_active: bool

class SafetyMonitor:
    """Monitor di sicurezza in tempo reale per Robot AI"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Safety parameters dal config
        safety_config = config.get('behavior', {}).get('safety', {})
        self.min_obstacle_distance = safety_config.get('min_distance_obstacles', 15.0)  # cm
        self.emergency_stop_distance = safety_config.get('emergency_stop_distance', 10.0)  # cm
        self.recovery_timeout = safety_config.get('recovery_timeout', 5.0)  # seconds
        self.max_slope_angle = safety_config.get('max_slope_angle', 15.0)  # degrees

        # References ai componenti del robot (injected later)
        self.motor_controller = None
        self.sensor_manager = None
        self.led_controller = None

        # Safety state
        self.safety_status = SafetyStatus(
            level=SafetyLevel.SAFE,
            active_alerts=[],
            last_sensor_reading=0.0,
            emergency_stops_count=0,
            is_monitoring_active=False
        )

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_shutting_down = False

        # Callbacks per eventi safety
        self._safety_callbacks: List[Callable] = []

        # Statistics
        self.stats = {
            'monitoring_loops': 0,
            'warnings_triggered': 0,
            'emergency_stops': 0,
            'false_alarms': 0,
            'uptime_start': time.time()
        }

        self.logger.info("SafetyMonitor initialized with thresholds:")
        self.logger.info(f"  - Min obstacle distance: {self.min_obstacle_distance}cm")
        self.logger.info(f"  - Emergency stop distance: {self.emergency_stop_distance}cm")

    def set_robot_components(self, motor_controller, sensor_manager, led_controller):
        """Imposta riferimenti ai componenti del robot"""
        self.motor_controller = motor_controller
        self.sensor_manager = sensor_manager
        self.led_controller = led_controller
        self.logger.info("Robot components configured for safety monitoring")

    async def initialize(self) -> bool:
        """Inizializza safety monitor e avvia monitoraggio"""
        try:
            if not all([self.motor_controller, self.sensor_manager]):
                self.logger.error("❌ Missing required robot components for safety monitoring")
                return False

            # Avvia monitoring loop
            await self.start_monitoring()

            self.logger.info("✅ SafetyMonitor initialized and monitoring started")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error initializing safety monitor: {e}")
            return False

    async def start_monitoring(self):
        """Avvia il loop di monitoraggio sicurezza"""
        if self._monitoring_task and not self._monitoring_task.done():
            self.logger.warning("Safety monitoring already active")
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.safety_status.is_monitoring_active = True
        self.logger.info("🛡️ Safety monitoring started")

    async def stop_monitoring(self):
        """Ferma il loop di monitoraggio"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self.safety_status.is_monitoring_active = False
        self.logger.info("⏸️ Safety monitoring stopped")

    async def _monitoring_loop(self):
        """Loop principale monitoraggio sicurezza - 20Hz"""
        self.logger.info("🔄 Safety monitoring loop started")

        try:
            while not self._is_shutting_down:
                start_time = asyncio.get_event_loop().time()

                # Controlla sensori per pericoli
                await self._check_sensors()

                # Controlla comunicazione componenti
                await self._check_communication()

                # Aggiorna statistics
                self.stats['monitoring_loops'] += 1

                # Sleep per mantenere 20Hz (50ms cycle)
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0.05 - elapsed, 0.01)  # Min 10ms sleep
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            self.logger.info("Safety monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"❌ Fatal error in safety monitoring loop: {e}")
            await self.trigger_emergency_stop(SafetyAlert.SYSTEM_ERROR)

    async def _check_sensors(self):
        """Controlla sensori per situazioni pericolose"""
        try:
            # Leggi distanza ostacoli
            if self.sensor_manager:
                distance = await self.sensor_manager.read_distance()

                if distance is not None:
                    self.safety_status.last_sensor_reading = time.time()

                    # Check emergency stop distance
                    if distance <= self.emergency_stop_distance:
                        await self._handle_emergency_obstacle(distance)

                    # Check warning distance
                    elif distance <= self.min_obstacle_distance:
                        await self._handle_warning_obstacle(distance)

                    # Safe distance
                    else:
                        await self._clear_obstacle_alerts()

                else:
                    # Sensor failure
                    await self._handle_sensor_failure()

        except Exception as e:
            self.logger.error(f"Error checking sensors: {e}")

    async def _handle_emergency_obstacle(self, distance: float):
        """Gestisce ostacoli criticamente vicini - EMERGENCY STOP"""
        if SafetyAlert.OBSTACLE_TOO_CLOSE not in self.safety_status.active_alerts:
            self.logger.warning(f"🚨 EMERGENCY: Obstacle at {distance:.1f}cm (< {self.emergency_stop_distance}cm)")

            # Emergency stop immediato
            await self.trigger_emergency_stop(SafetyAlert.OBSTACLE_TOO_CLOSE)

            # LED emergency pattern
            if self.led_controller:
                asyncio.create_task(self.led_controller.emergency_pattern())

    async def _handle_warning_obstacle(self, distance: float):
        """Gestisce ostacoli vicini - WARNING"""
        if self.safety_status.level == SafetyLevel.SAFE:
            self.logger.warning(f"⚠️ WARNING: Obstacle at {distance:.1f}cm (< {self.min_obstacle_distance}cm)")

            self.safety_status.level = SafetyLevel.WARNING
            self.stats['warnings_triggered'] += 1

            # LED warning pattern
            if self.led_controller:
                asyncio.create_task(self.led_controller.attention_sequence())

            # Notifica callbacks
            await self._notify_callbacks("obstacle_warning", distance)

    async def _clear_obstacle_alerts(self):
        """Rimuove alert ostacoli quando situazione è sicura"""
        if SafetyAlert.OBSTACLE_TOO_CLOSE in self.safety_status.active_alerts:
            self.safety_status.active_alerts.remove(SafetyAlert.OBSTACLE_TOO_CLOSE)

        if self.safety_status.level in [SafetyLevel.WARNING, SafetyLevel.DANGER]:
            self.safety_status.level = SafetyLevel.SAFE
            self.logger.info("✅ Obstacle threat cleared - returning to SAFE level")

    async def _handle_sensor_failure(self):
        """Gestisce failure sensori"""
        if SafetyAlert.SENSOR_FAILURE not in self.safety_status.active_alerts:
            self.logger.error("❌ Sensor failure detected - no distance reading")

            self.safety_status.active_alerts.append(SafetyAlert.SENSOR_FAILURE)
            self.safety_status.level = SafetyLevel.DANGER

            # Stop motori per sicurezza
            if self.motor_controller and not self.motor_controller.is_emergency_stopped():
                await self.motor_controller.emergency_stop()

    async def _check_communication(self):
        """Controlla comunicazione con componenti critici"""
        try:
            # Check se ultima lettura sensori troppo vecchia (>2s)
            if (time.time() - self.safety_status.last_sensor_reading) > 2.0:
                if SafetyAlert.COMMUNICATION_LOST not in self.safety_status.active_alerts:
                    self.logger.error("❌ Communication lost with sensors")

                    self.safety_status.active_alerts.append(SafetyAlert.COMMUNICATION_LOST)
                    self.safety_status.level = SafetyLevel.DANGER

        except Exception as e:
            self.logger.error(f"Error checking communication: {e}")

    async def trigger_emergency_stop(self, alert: SafetyAlert) -> bool:
        """Trigger emergency stop per alert specifico"""
        try:
            self.logger.error(f"🚨 EMERGENCY STOP triggered: {alert.value}")

            # Aggiungi alert se non presente
            if alert not in self.safety_status.active_alerts:
                self.safety_status.active_alerts.append(alert)

            # Set emergency level
            self.safety_status.level = SafetyLevel.EMERGENCY
            self.safety_status.emergency_stops_count += 1
            self.stats['emergency_stops'] += 1

            # Stop motori immediato
            if self.motor_controller:
                success = await self.motor_controller.emergency_stop()

                if success:
                    self.logger.info("✅ Emergency stop executed successfully")
                else:
                    self.logger.error("❌ Emergency stop failed!")

            # LED emergency pattern
            if self.led_controller:
                asyncio.create_task(self.led_controller.emergency_pattern())

            # Notifica callbacks
            await self._notify_callbacks("emergency_stop", alert.value)

            return True

        except Exception as e:
            self.logger.error(f"❌ Error executing emergency stop: {e}")
            return False

    async def manual_emergency_stop(self) -> bool:
        """Emergency stop manuale (richiamabile dall'esterno)"""
        return await self.trigger_emergency_stop(SafetyAlert.MANUAL_EMERGENCY)

    async def resume_after_emergency(self) -> bool:
        """Riprende operazioni dopo emergency stop (solo se sicuro)"""
        try:
            # Check se situazione è davvero sicura
            if self.sensor_manager:
                distance = await self.sensor_manager.read_distance()

                if distance is None or distance <= self.min_obstacle_distance:
                    self.logger.warning("❌ Cannot resume - obstacles still detected")
                    return False

            # Clear alerts
            self.safety_status.active_alerts.clear()
            self.safety_status.level = SafetyLevel.SAFE

            # Resume motor controller
            if self.motor_controller:
                await self.motor_controller.resume_from_emergency()

            self.logger.info("✅ Resumed from emergency stop - robot operational")

            # LED feedback
            if self.led_controller:
                asyncio.create_task(self.led_controller.celebration_sequence())

            return True

        except Exception as e:
            self.logger.error(f"Error resuming from emergency: {e}")
            return False

    def add_safety_callback(self, callback: Callable):
        """Aggiungi callback per eventi safety"""
        self._safety_callbacks.append(callback)

    async def _notify_callbacks(self, event_type: str, data: Any):
        """Notifica callbacks registrati"""
        for callback in self._safety_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                self.logger.error(f"Error in safety callback: {e}")

    def get_safety_status(self) -> SafetyStatus:
        """Ottieni stato sicurezza corrente"""
        return self.safety_status

    def is_safe_to_move(self) -> bool:
        """Check se è sicuro muoversi"""
        return self.safety_status.level in [SafetyLevel.SAFE, SafetyLevel.WARNING]

    def get_safety_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche safety monitor"""
        uptime = time.time() - self.stats['uptime_start']

        return {
            **self.stats,
            'uptime_seconds': uptime,
            'current_level': self.safety_status.level.value,
            'active_alerts': [alert.value for alert in self.safety_status.active_alerts],
            'is_monitoring': self.safety_status.is_monitoring_active,
            'loops_per_second': self.stats['monitoring_loops'] / max(uptime, 1),
            'emergency_stop_rate': self.stats['emergency_stops'] / max(uptime / 3600, 0.1)  # per hour
        }

    async def shutdown(self):
        """Shutdown sicuro safety monitor"""
        self.logger.info("🔄 Shutting down safety monitor...")

        self._is_shutting_down = True

        # Stop monitoring
        await self.stop_monitoring()

        # Final safety check - ensure motors stopped
        if self.motor_controller and self.motor_controller.is_moving():
            await self.motor_controller.stop()

        self.logger.info("✅ Safety monitor shutdown complete")