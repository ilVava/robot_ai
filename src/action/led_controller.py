"""
LED Controller - Hardware Interface per controllo LED Matrix

Gestisce le espressioni facciali del robot tramite LED matrix 8x8:
- Espressioni emotive (happy, sad, curious, alert, etc.)
- Animazioni dinamiche per stati comportamentali
- Sincronizzazione con sistema emotivo del robot
- Comunicazione via Arduino seriale per controllo hardware

Protocol: Seriale 115200 baud, comando LED_PATTERN:N
Pattern: 0-10 pattern predefiniti Arduino, extensible
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from enum import Enum

class LEDExpression(Enum):
    """Espressioni LED disponibili"""
    OFF = 0
    BLINK = 1
    PULSE = 2
    SLOW_PULSE = 3
    HAPPY = 4
    SAD = 5
    CURIOUS = 6
    ALERT = 7
    FOCUSED = 8
    PLAYFUL = 9
    RESTING = 10

class LEDController:
    """Controllore hardware LED Matrix via comunicazione seriale Arduino"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # LED Matrix config
        self.led_config = config.get('hardware', {}).get('led_matrix', {})
        self.brightness = self.led_config.get('brightness', 5)  # 0-15

        # Current state
        self.current_expression = LEDExpression.OFF
        self.is_animating = False
        self.animation_task: Optional[asyncio.Task] = None

        # Arduino serial interface (injected later)
        self.arduino_serial = None

        # Emotional mappings (stato emotivo → espressione LED)
        self.emotion_to_expression = {
            'curious': LEDExpression.CURIOUS,
            'cautious': LEDExpression.ALERT,
            'playful': LEDExpression.PLAYFUL,
            'alert': LEDExpression.ALERT,
            'focused': LEDExpression.FOCUSED,
            'resting': LEDExpression.RESTING,
            # Default expressions
            'happy': LEDExpression.HAPPY,
            'sad': LEDExpression.SAD,
        }

        self.logger.info("LEDController initialized")

    def set_arduino_serial(self, arduino_serial):
        """Imposta riferimento alla connessione seriale Arduino per controllo LED."""
        self.arduino_serial = arduino_serial
        self.logger.info("Arduino serial connection configured for LED control")

    async def initialize(self) -> bool:
        """Inizializza LED controller"""
        try:
            # Clear Arduino serial buffer per evitare comandi precedenti
            if hasattr(self.arduino_serial, 'serial_connection') and self.arduino_serial.serial_connection:
                self.arduino_serial.serial_connection.flushInput()
                self.arduino_serial.serial_connection.flushOutput()
                await asyncio.sleep(0.2)  # Extended processing time per buffer stability

            # Test iniziale - spegni tutto
            success = await self.set_expression(LEDExpression.OFF)

            if success:
                self.logger.info("✅ LED Controller initialized successfully")
                return True
            else:
                self.logger.error("❌ LED Controller initialization failed")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error initializing LED controller: {e}")
            return False

    async def set_expression(self, expression: LEDExpression) -> bool:
        """Imposta espressione LED specifica"""
        try:
            if not self.arduino_serial:
                self.logger.warning("Arduino serial not available - LED expression ignored")
                return False

            # Stop animazione corrente se attiva
            await self._stop_animation()

            # Small delay per evitare sovrapposizione comandi Arduino
            await asyncio.sleep(0.1)

            # Invia comando LED_PATTERN:N ad Arduino
            command = f"LED_PATTERN:{expression.value}"
            response = await self.arduino_serial._send_command(command, expect_response=True, timeout=3.0)

            if response and "ACTION:LED_PATTERN" in response:
                self.current_expression = expression
                self.logger.info(f"✅ LED expression set to {expression.name}")
                return True
            else:
                self.logger.error(f"❌ LED expression command failed: {command} | Response: {response}")
                return False

        except Exception as e:
            self.logger.error(f"Error setting LED expression {expression.name}: {e}")
            return False

    async def show_emotion(self, emotion_state: str, duration: Optional[float] = None) -> bool:
        """Mostra espressione basata su stato emotivo"""
        try:
            # Mappa emozione a espressione LED
            expression = self.emotion_to_expression.get(emotion_state.lower(), LEDExpression.BLINK)

            self.logger.info(f"🎭 Showing emotion '{emotion_state}' → LED expression '{expression.name}'")

            success = await self.set_expression(expression)

            # Se specificata durata, torna a OFF dopo timeout
            if success and duration:
                self.animation_task = asyncio.create_task(self._timed_expression(duration))

            return success

        except Exception as e:
            self.logger.error(f"Error showing emotion {emotion_state}: {e}")
            return False

    async def blink_pattern(self, count: int = 3, interval: float = 0.5) -> bool:
        """Pattern di blink personalizzato"""
        try:
            self.is_animating = True

            for i in range(count):
                # On
                await self.set_expression(LEDExpression.BLINK)
                await asyncio.sleep(interval)

                # Off
                await self.set_expression(LEDExpression.OFF)
                await asyncio.sleep(interval * 0.5)  # Off più breve

            self.is_animating = False
            self.logger.info(f"✅ Blink pattern completed ({count} blinks)")
            return True

        except Exception as e:
            self.logger.error(f"Error in blink pattern: {e}")
            self.is_animating = False
            return False

    async def pulse_emotion(self, emotion_state: str, pulses: int = 2, interval: float = 1.0) -> bool:
        """Pulsa un'emozione specifica per enfasi"""
        try:
            expression = self.emotion_to_expression.get(emotion_state.lower(), LEDExpression.PULSE)
            self.is_animating = True

            for i in range(pulses):
                await self.set_expression(expression)
                await asyncio.sleep(interval)

                await self.set_expression(LEDExpression.OFF)
                await asyncio.sleep(interval * 0.3)

            self.is_animating = False
            self.logger.info(f"✅ Emotion pulse completed: {emotion_state} x{pulses}")
            return True

        except Exception as e:
            self.logger.error(f"Error in pulse emotion: {e}")
            self.is_animating = False
            return False

    async def celebration_sequence(self) -> bool:
        """Sequenza celebrazione per successi/traguardi"""
        try:
            self.is_animating = True

            # Happy → Pulse → Blink rapidamente
            expressions = [LEDExpression.HAPPY, LEDExpression.PULSE, LEDExpression.BLINK]

            for expr in expressions:
                await self.set_expression(expr)
                await asyncio.sleep(0.8)

            # Finale con blink veloce
            for _ in range(5):
                await self.set_expression(LEDExpression.BLINK)
                await asyncio.sleep(0.2)
                await self.set_expression(LEDExpression.OFF)
                await asyncio.sleep(0.1)

            await self.set_expression(LEDExpression.OFF)

            self.is_animating = False
            self.logger.info("✅ Celebration sequence completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in celebration sequence: {e}")
            self.is_animating = False
            return False

    async def attention_sequence(self) -> bool:
        """Sequenza per attirare attenzione (ostacoli, situazioni critiche)"""
        try:
            self.is_animating = True

            # Alert pattern veloce
            for _ in range(6):
                await self.set_expression(LEDExpression.ALERT)
                await asyncio.sleep(0.3)
                await self.set_expression(LEDExpression.OFF)
                await asyncio.sleep(0.2)

            self.is_animating = False
            self.logger.info("✅ Attention sequence completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in attention sequence: {e}")
            self.is_animating = False
            return False

    async def _timed_expression(self, duration: float):
        """Helper per espressioni temporizzate"""
        try:
            await asyncio.sleep(duration)
            await self.set_expression(LEDExpression.OFF)
            self.logger.debug(f"Timed expression ended after {duration}s")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in timed expression: {e}")

    async def _stop_animation(self):
        """Stop animazione corrente se attiva"""
        if self.animation_task and not self.animation_task.done():
            self.animation_task.cancel()
            try:
                await self.animation_task
            except asyncio.CancelledError:
                pass
            self.animation_task = None

        self.is_animating = False

    def get_current_expression(self) -> LEDExpression:
        """Ottieni espressione corrente"""
        return self.current_expression

    def is_animation_active(self) -> bool:
        """Check se animazione in corso"""
        return self.is_animating

    async def emergency_pattern(self) -> bool:
        """Pattern LED per emergenza - priorità massima"""
        try:
            self.logger.warning("🚨 LED Emergency pattern activated")

            # Stop tutto
            await self._stop_animation()

            # Pattern emergenza veloce e visibile
            self.is_animating = True
            for _ in range(10):
                await self.set_expression(LEDExpression.ALERT)
                await asyncio.sleep(0.1)
                await self.set_expression(LEDExpression.OFF)
                await asyncio.sleep(0.1)

            self.is_animating = False
            self.logger.info("✅ Emergency LED pattern completed")
            return True

        except Exception as e:
            self.logger.error(f"Error in emergency LED pattern: {e}")
            self.is_animating = False
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Ottieni status completo LED controller"""
        return {
            'current_expression': self.current_expression.name,
            'is_animating': self.is_animating,
            'has_arduino_serial': self.arduino_serial is not None,
            'brightness': self.brightness,
            'available_expressions': [expr.name for expr in LEDExpression],
            'emotion_mappings': {k: v.name for k, v in self.emotion_to_expression.items()}
        }

    async def shutdown(self):
        """Shutdown sicuro LED controller"""
        self.logger.info("🔄 Shutting down LED controller...")

        # Stop animazioni
        await self._stop_animation()

        # Spegni LEDs
        await self.set_expression(LEDExpression.OFF)

        self.logger.info("✅ LED controller shutdown complete")