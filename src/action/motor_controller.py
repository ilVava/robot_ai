"""
Motor Controller - Hardware Interface per controllo motori via Arduino

Gestisce la comunicazione seriale con Arduino per controllo fisico del robot:
- Movimento direzionale (avanti, indietro, rotazioni)
- Controllo velocità adattiva basata su stati emotivi
- Safety monitoring e emergency stop
- Interfaccia con emotion system per comportamenti dinamici

Protocol: Seriale 115200 baud via /dev/ttyUSB0
Commands: MOVE_FORWARD, MOVE_BACKWARD, TURN_LEFT, TURN_RIGHT, STOP, SET_SPEED
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False

class MotorDirection(Enum):
    """Enum per direzioni di movimento"""
    FORWARD = "MOVE_FORWARD"
    BACKWARD = "MOVE_BACKWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STOP = "STOP"

@dataclass
class MotorState:
    """Stato corrente dei motori"""
    direction: MotorDirection
    speed: int  # 0-255 PWM
    is_moving: bool
    last_command_time: float

class MotorController:
    """Controllore hardware motori via comunicazione seriale Arduino"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Connessione seriale Arduino
        self.serial_port = "/dev/ttyUSB0"  # Arduino via USB
        self.baud_rate = 115200
        self.serial_connection: Optional[serial.Serial] = None

        # Stato motori
        self.motor_state = MotorState(
            direction=MotorDirection.STOP,
            speed=0,
            is_moving=False,
            last_command_time=0.0
        )

        # Safety parameters dal config
        self.max_speed = config.get('motors', {}).get('max_speed', 100)
        self.base_speed = config.get('motors', {}).get('base_speed', 40)
        self.min_obstacle_distance = config.get('safety', {}).get('min_distance_obstacles', 15.0)
        self.emergency_stop_distance = config.get('safety', {}).get('emergency_stop_distance', 10.0)

        # Connection management
        self._connection_lock = asyncio.Lock()
        self._command_queue = asyncio.Queue()
        self._is_emergency_stopped = False

        self.logger.info(f"MotorController initialized - Port: {self.serial_port}")

    async def initialize(self) -> bool:
        """Inizializza connessione seriale con Arduino"""
        try:
            if not SERIAL_AVAILABLE:
                self.logger.warning("⚠️ PySerial not available - motor controller in simulation mode")
                return True

            async with self._connection_lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.logger.info("Serial connection already open")
                    return True

                self.logger.info(f"Opening serial connection to {self.serial_port}")

                # Apri connessione seriale
                self.serial_connection = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.baud_rate,
                    timeout=1.0,
                    write_timeout=1.0
                )

                # Wait for Arduino ready signal
                await asyncio.sleep(2.0)  # Arduino boot time

                # Clear any buffered data
                self.serial_connection.flushInput()
                self.serial_connection.flushOutput()

                # Test connessione con PING
                response = await self._send_command("PING", expect_response=True, timeout=5.0)
                if response and "PONG" in response:
                    self.logger.info("✅ Arduino connection established - PING/PONG successful")

                    # Emergency stop per sicurezza
                    await self._send_command("STOP")
                    await self._send_command(f"SET_SPEED:{self.base_speed}")

                    return True
                else:
                    self.logger.error(f"❌ Arduino not responding to PING. Response: {response}")
                    return False

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize motor controller: {e}")
            return False

    async def _send_command(self, command: str, expect_response: bool = False, timeout: float = 2.0) -> Optional[str]:
        """Invia comando all'Arduino e legge risposta opzionale"""
        try:
            if not SERIAL_AVAILABLE:
                # Simulation mode - mock responses
                self.logger.debug(f"→ SIMULATION: {command}")
                if expect_response:
                    if "PING" in command:
                        return "PONG"
                    elif "MOVE" in command or "TURN" in command:
                        return f"ACTION:{command}:SPEED:50"
                    elif "STOP" in command:
                        return "ACTION:STOP"
                    elif "SET_SPEED" in command:
                        return "ACTION:SPEED_SET:50"
                    elif "STATUS" in command:
                        return 'STATUS:{"speed":50,"uptime":12345,"free_memory":1500}'
                return "OK"

            if not self.serial_connection or not self.serial_connection.is_open:
                self.logger.error("Serial connection not available")
                return None

            # Invia comando
            command_bytes = f"{command}\n".encode('utf-8')
            self.serial_connection.write(command_bytes)
            self.serial_connection.flush()

            self.logger.debug(f"→ Sent: {command}")

            if expect_response:
                # Leggi risposta con timeout - loop più veloce per Arduino
                start_time = asyncio.get_event_loop().time()
                response = ""

                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    if self.serial_connection.in_waiting > 0:
                        line = self.serial_connection.readline().decode('utf-8').strip()
                        if line:
                            response = line
                            self.logger.debug(f"← Received: {response}")
                            break
                    await asyncio.sleep(0.001)  # 1ms invece di 10ms per responsività

                return response if response else None

            return None

        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}")
            return None

    async def move_forward(self, speed: Optional[int] = None) -> bool:
        """Movimento in avanti"""
        if self._is_emergency_stopped:
            self.logger.warning("Cannot move - emergency stop active")
            return False

        effective_speed = speed or self.motor_state.speed or self.base_speed

        # Set velocità se diversa da corrente
        if effective_speed != self.motor_state.speed:
            await self._send_command(f"SET_SPEED:{effective_speed}")
            self.motor_state.speed = effective_speed

        # Comando movimento
        response = await self._send_command("MOVE_FORWARD", expect_response=True)

        if response and "ACTION:MOVE_FORWARD" in response:
            self.motor_state.direction = MotorDirection.FORWARD
            self.motor_state.is_moving = True
            self.motor_state.last_command_time = asyncio.get_event_loop().time()

            self.logger.info(f"✅ Moving forward at speed {effective_speed}")
            return True
        else:
            self.logger.error("❌ Forward movement command failed")
            return False

    async def move_backward(self, speed: Optional[int] = None) -> bool:
        """Movimento indietro"""
        if self._is_emergency_stopped:
            self.logger.warning("Cannot move - emergency stop active")
            return False

        effective_speed = speed or self.motor_state.speed or self.base_speed

        if effective_speed != self.motor_state.speed:
            await self._send_command(f"SET_SPEED:{effective_speed}")
            self.motor_state.speed = effective_speed

        response = await self._send_command("MOVE_BACKWARD", expect_response=True)

        if response and "ACTION:MOVE_BACKWARD" in response:
            self.motor_state.direction = MotorDirection.BACKWARD
            self.motor_state.is_moving = True
            self.motor_state.last_command_time = asyncio.get_event_loop().time()

            self.logger.info(f"✅ Moving backward at speed {effective_speed}")
            return True
        else:
            self.logger.error("❌ Backward movement command failed")
            return False

    async def turn_left(self, speed: Optional[int] = None) -> bool:
        """Rotazione sinistra"""
        if self._is_emergency_stopped:
            return False

        effective_speed = speed or self.motor_state.speed or self.base_speed

        if effective_speed != self.motor_state.speed:
            await self._send_command(f"SET_SPEED:{effective_speed}")
            self.motor_state.speed = effective_speed

        response = await self._send_command("TURN_LEFT", expect_response=True)

        if response and "ACTION:TURN_LEFT" in response:
            self.motor_state.direction = MotorDirection.TURN_LEFT
            self.motor_state.is_moving = True
            self.motor_state.last_command_time = asyncio.get_event_loop().time()

            self.logger.info(f"✅ Turning left at speed {effective_speed}")
            return True
        else:
            self.logger.error("❌ Left turn command failed")
            return False

    async def turn_right(self, speed: Optional[int] = None) -> bool:
        """Rotazione destra"""
        if self._is_emergency_stopped:
            return False

        effective_speed = speed or self.motor_state.speed or self.base_speed

        if effective_speed != self.motor_state.speed:
            await self._send_command(f"SET_SPEED:{effective_speed}")
            self.motor_state.speed = effective_speed

        response = await self._send_command("TURN_RIGHT", expect_response=True)

        if response and "ACTION:TURN_RIGHT" in response:
            self.motor_state.direction = MotorDirection.TURN_RIGHT
            self.motor_state.is_moving = True
            self.motor_state.last_command_time = asyncio.get_event_loop().time()

            self.logger.info(f"✅ Turning right at speed {effective_speed}")
            return True
        else:
            self.logger.error("❌ Right turn command failed")
            return False

    async def stop(self) -> bool:
        """Stop motori (comando prioritario)"""
        response = await self._send_command("STOP", expect_response=True)

        if response and "ACTION:STOP" in response:
            self.motor_state.direction = MotorDirection.STOP
            self.motor_state.is_moving = False
            self.motor_state.last_command_time = asyncio.get_event_loop().time()

            self.logger.info("✅ Motors stopped")
            return True
        else:
            self.logger.error("❌ Stop command failed")
            return False

    async def set_speed(self, speed: int) -> bool:
        """Imposta velocità motori (0-255)"""
        # Clamp speed nei limiti sicuri
        clamped_speed = max(0, min(speed, self.max_speed))

        response = await self._send_command(f"SET_SPEED:{clamped_speed}", expect_response=True)

        if response and "ACTION:SPEED_SET" in response:
            self.motor_state.speed = clamped_speed
            self.logger.info(f"✅ Speed set to {clamped_speed}")
            return True
        else:
            self.logger.error(f"❌ Set speed command failed")
            return False

    async def emergency_stop(self) -> bool:
        """Emergency stop - priorità massima"""
        self.logger.warning("🚨 EMERGENCY STOP ACTIVATED")
        self._is_emergency_stopped = True

        # Stop immediato
        success = await self.stop()

        if success:
            self.logger.info("✅ Emergency stop successful")
        else:
            self.logger.error("❌ Emergency stop failed")

        return success

    async def resume_from_emergency(self) -> bool:
        """Riprende da emergency stop"""
        self._is_emergency_stopped = False
        self.logger.info("✅ Resumed from emergency stop")
        return True

    async def move_with_emotion(self, direction: MotorDirection, emotion_state: str) -> bool:
        """Movimento adattato allo stato emotivo"""

        # CRITICO: Buffer flush prima del movimento per evitare collision con sensor readings
        if hasattr(self, 'serial_connection') and self.serial_connection:
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            await asyncio.sleep(0.1)  # Serial stability time

        # Modifica velocità basata su emozione (dal config YAML)
        emotion_config = self.config.get('behavior', {}).get('emotions', {}).get(emotion_state, {})
        speed_multiplier = emotion_config.get('speed_multiplier', 1.0)

        # Calcola velocità basata su emozione
        emotional_speed = int(self.base_speed * speed_multiplier)
        emotional_speed = max(10, min(emotional_speed, self.max_speed))  # Safety clamps

        self.logger.info(f"🎭 Moving with emotion '{emotion_state}' - Speed: {emotional_speed} (multiplier: {speed_multiplier})")

        # Esegui movimento con velocità emotiva
        if direction == MotorDirection.FORWARD:
            return await self.move_forward(emotional_speed)
        elif direction == MotorDirection.BACKWARD:
            return await self.move_backward(emotional_speed)
        elif direction == MotorDirection.TURN_LEFT:
            return await self.turn_left(emotional_speed)
        elif direction == MotorDirection.TURN_RIGHT:
            return await self.turn_right(emotional_speed)
        elif direction == MotorDirection.STOP:
            return await self.stop()
        else:
            return False

    def get_motor_state(self) -> MotorState:
        """Ritorna stato corrente motori"""
        return self.motor_state

    def is_moving(self) -> bool:
        """Check se robot è in movimento"""
        return self.motor_state.is_moving

    def is_emergency_stopped(self) -> bool:
        """Check se emergency stop è attivo"""
        return self._is_emergency_stopped

    async def get_status(self) -> Dict[str, Any]:
        """Ottiene status completo da Arduino"""
        response = await self._send_command("STATUS", expect_response=True, timeout=3.0)

        if response and "STATUS:" in response:
            try:
                # Parse JSON response
                json_part = response.split("STATUS:")[1]
                status_data = json.loads(json_part)

                # Aggiungi dati Python
                status_data.update({
                    'python_motor_state': {
                        'direction': self.motor_state.direction.value,
                        'speed': self.motor_state.speed,
                        'is_moving': self.motor_state.is_moving,
                        'is_emergency_stopped': self._is_emergency_stopped
                    }
                })

                return status_data

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse status JSON: {e}")
                return {'error': 'invalid_json'}
        else:
            return {'error': 'no_response'}

    async def shutdown(self):
        """Shutdown sicuro del controller"""
        self.logger.info("🔄 Shutting down motor controller...")

        # Stop motori prima di chiudere
        await self.stop()

        # Chiudi connessione seriale
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.logger.info("✅ Serial connection closed")

        self.logger.info("✅ Motor controller shutdown complete")