#!/usr/bin/env python3
"""
Expression Manager - Robot AI Emotion System  
============================================

Gestisce le espressioni LED del robot per mostrare visivamente le emozioni.
Come il "volto" del robot che cambia colore e pattern in base all'umore.

In parole semplici:
- LED Matrix 8x8 mostra "facce" ed espressioni
- Ogni emozione ha colori e pattern specifici
- Animazioni smooth tra le espressioni
- Feedback visivo per l'utente sullo stato del robot

Espressioni supportate:
- CURIOUS: Blu/Verde, pattern esplorativo, "occhi" che guardano
- CAUTIOUS: Giallo/Arancione, pattern lento, "occhi" attenti  
- PLAYFUL: Rosa/Viola, pattern dinamico, "sorriso"
- ALERT: Rosso, pattern rapido, "occhi" grandi
- FOCUSED: Verde, pattern concentrato, linea dritta
- RESTING: Blu scuro, pattern lento, "occhi" chiusi

Author: Andrea Vavassori
"""

import asyncio
import logging
import time
import random
import math
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from enum import Enum

# Import per hardware LED (solo se disponibile)
try:
    # Placeholder per librerie LED reali
    LED_HARDWARE_AVAILABLE = False
except ImportError:
    LED_HARDWARE_AVAILABLE = False

class ExpressionPattern(Enum):
    """Pattern di espressione LED."""
    STATIC = "static"           # Colore fisso
    PULSE = "pulse"            # Pulsazione lenta  
    BLINK = "blink"            # Lampeggiamento
    WAVE = "wave"              # Onda che attraversa
    SPIRAL = "spiral"          # Spirale rotante
    EYES = "eyes"              # Pattern "occhi"
    SMILE = "smile"            # Pattern "sorriso"
    ALERT_FLASH = "alert_flash" # Flash di allarme
    BREATHE = "breathe"        # Respirazione lenta

class ExpressionManager:
    """
    Gestore espressioni LED per il robot.
    
    Traduce stati emotivi in pattern visivi comprensibili:
    - Colori associati a emozioni specifiche
    - Animazioni fluide tra stati
    - Pattern dinamici basati su intensità emotiva
    - Supporto sia simulation che hardware LED reale
    """
    
    def __init__(self, config: dict, simulation_mode: bool = True):
        self.config = config.get('hardware', {}).get('led_matrix', {})
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Configurazione LED Matrix
        self.matrix_size = (8, 8)  # 8x8 LED matrix
        self.brightness = self.config.get('brightness', 5)  # 0-15
        self.update_frequency = 30  # FPS per animazioni
        
        # Hardware interface (None in simulation)
        self.led_hardware = None
        self.is_initialized = False
        
        # Estado corrente
        self.current_expression = None
        self.current_pattern = ExpressionPattern.STATIC
        self.current_colors = {'primary': (0, 0, 255), 'secondary': (0, 255, 0)}  # RGB
        self.animation_frame = 0
        self.animation_speed = 1.0
        
        # Buffer LED matrix per rendering
        self.led_matrix = np.zeros((*self.matrix_size, 3), dtype=np.uint8)  # RGB per pixel
        
        # Definizione espressioni per ogni emozione
        self.emotion_expressions = self._define_emotion_expressions()
        
        # Animation loop control
        self.animation_running = False
        self.animation_task = None
        
        # Statistics
        self.stats = {
            'expressions_rendered': 0,
            'animation_frames': 0,
            'current_fps': 0.0,
            'last_expression_change': 0.0
        }
        
        self.logger.info(f"Expression Manager inizializzato - Simulation: {simulation_mode}")
    
    def _define_emotion_expressions(self) -> Dict[str, Dict[str, Any]]:
        """Definisce espressioni visive per ogni emozione."""
        
        return {
            'curious': {
                'primary_color': (0, 150, 255),    # Blu brillante
                'secondary_color': (0, 255, 150),  # Verde acqua
                'pattern': ExpressionPattern.WAVE,
                'animation_speed': 1.2,
                'brightness_modifier': 0.8,
                'description': 'Onda blu-verde che esplora la matrice'
            },
            
            'cautious': {
                'primary_color': (255, 200, 0),    # Giallo/Arancione
                'secondary_color': (255, 100, 0),  # Arancione
                'pattern': ExpressionPattern.PULSE,
                'animation_speed': 0.6,
                'brightness_modifier': 0.6,
                'description': 'Pulsazione lenta giallo-arancione'
            },
            
            'playful': {
                'primary_color': (255, 100, 200),  # Rosa
                'secondary_color': (150, 0, 255),  # Viola
                'pattern': ExpressionPattern.SPIRAL,
                'animation_speed': 1.8,
                'brightness_modifier': 0.9,
                'description': 'Spirale dinamica rosa-viola'
            },
            
            'alert': {
                'primary_color': (255, 0, 0),      # Rosso intenso
                'secondary_color': (255, 50, 0),   # Rosso-arancione
                'pattern': ExpressionPattern.ALERT_FLASH,
                'animation_speed': 3.0,
                'brightness_modifier': 1.0,
                'description': 'Flash rossi di allerta'
            },
            
            'focused': {
                'primary_color': (0, 255, 0),      # Verde
                'secondary_color': (50, 200, 50),  # Verde chiaro
                'pattern': ExpressionPattern.EYES,
                'animation_speed': 0.8,
                'brightness_modifier': 0.7,
                'description': 'Pattern occhi verdi concentrati'
            },
            
            'resting': {
                'primary_color': (0, 50, 100),     # Blu scuro
                'secondary_color': (0, 20, 80),    # Blu molto scuro
                'pattern': ExpressionPattern.BREATHE,
                'animation_speed': 0.3,
                'brightness_modifier': 0.3,
                'description': 'Respirazione lenta blu scura'
            }
        }
    
    async def initialize(self) -> bool:
        """Inizializza sistema LED."""
        try:
            if not self.simulation_mode and LED_HARDWARE_AVAILABLE:
                # Inizializza hardware LED reale
                # TODO: Implementare per deploy su hardware
                self.logger.info("Inizializzando LED Matrix hardware...")
                pass
            else:
                self.logger.info("Modalità simulation LED attivata")
            
            # Avvia animation loop
            await self.start_animation_loop()
            
            self.is_initialized = True
            self.logger.info("Expression Manager inizializzato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione LED: {e}")
            return False
    
    async def set_emotion_expression(self, emotion: str, intensity: float = 1.0):
        """
        Imposta espressione basata su emozione.
        
        Args:
            emotion: Nome emozione ('curious', 'alert', etc.)
            intensity: Intensità 0.0-1.0 che modula luminosità e velocità
        """
        if emotion not in self.emotion_expressions:
            self.logger.warning(f"Emozione sconosciuta: {emotion}")
            return
        
        expression_config = self.emotion_expressions[emotion]
        
        # Aggiorna configurazione corrente
        self.current_expression = emotion
        self.current_pattern = expression_config['pattern']
        self.current_colors['primary'] = expression_config['primary_color']
        self.current_colors['secondary'] = expression_config['secondary_color']
        
        # Modula velocità e luminosità con intensità
        base_speed = expression_config['animation_speed']
        self.animation_speed = base_speed * (0.5 + intensity * 0.5)  # 50%-100% velocità
        
        base_brightness = expression_config['brightness_modifier']
        effective_brightness = base_brightness * intensity
        
        # Log cambio espressione
        self.logger.info(f"Espressione: {emotion} → {expression_config['description']} "
                        f"(intensità: {intensity:.2f})")
        
        self.stats['last_expression_change'] = time.time()
        self.stats['expressions_rendered'] += 1
    
    async def start_animation_loop(self):
        """Avvia loop animazione LED."""
        if self.animation_running:
            return
        
        self.animation_running = True
        self.animation_task = asyncio.create_task(self._animation_loop())
        self.logger.debug("Animation loop avviato")
    
    async def stop_animation_loop(self):
        """Ferma loop animazione."""
        self.animation_running = False
        if self.animation_task:
            self.animation_task.cancel()
            try:
                await self.animation_task
            except asyncio.CancelledError:
                pass
        self.logger.debug("Animation loop fermato")
    
    async def _animation_loop(self):
        """Loop principale per animazioni LED."""
        frame_time = 1.0 / self.update_frequency
        last_frame_time = time.time()
        
        try:
            while self.animation_running:
                current_time = time.time()
                
                # Renderizza frame corrente
                await self._render_current_frame()
                
                # Aggiorna frame counter
                self.animation_frame += 1
                self.stats['animation_frames'] += 1
                
                # Calcola FPS effettivo
                time_delta = current_time - last_frame_time
                if time_delta > 0:
                    self.stats['current_fps'] = 1.0 / time_delta
                last_frame_time = current_time
                
                # Mantieni framerate
                elapsed = time.time() - current_time
                sleep_time = max(0, frame_time - elapsed)
                await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            self.logger.debug("Animation loop cancellato")
        except Exception as e:
            self.logger.error(f"Errore animation loop: {e}")
    
    async def _render_current_frame(self):
        """Renderizza frame corrente basato su pattern attivo."""
        if not self.current_pattern:
            return
        
        # Reset matrice
        self.led_matrix.fill(0)
        
        # Calcola time-based animation parameter
        animation_time = (self.animation_frame * self.animation_speed / self.update_frequency) % 1.0
        
        # Renderizza pattern specifico
        if self.current_pattern == ExpressionPattern.STATIC:
            await self._render_static(animation_time)
        elif self.current_pattern == ExpressionPattern.PULSE:
            await self._render_pulse(animation_time)
        elif self.current_pattern == ExpressionPattern.WAVE:
            await self._render_wave(animation_time)
        elif self.current_pattern == ExpressionPattern.SPIRAL:
            await self._render_spiral(animation_time)
        elif self.current_pattern == ExpressionPattern.EYES:
            await self._render_eyes(animation_time)
        elif self.current_pattern == ExpressionPattern.ALERT_FLASH:
            await self._render_alert_flash(animation_time)
        elif self.current_pattern == ExpressionPattern.BREATHE:
            await self._render_breathe(animation_time)
        
        # Applica a hardware (o simula)
        await self._update_hardware()
    
    async def _render_static(self, animation_time: float):
        """Renderizza pattern statico."""
        color = self.current_colors['primary']
        self.led_matrix[:, :] = color
    
    async def _render_pulse(self, animation_time: float):
        """Renderizza pulsazione."""
        # Pulsazione sinusoidale
        intensity = (math.sin(animation_time * 2 * math.pi) + 1) / 2
        
        primary = np.array(self.current_colors['primary'])
        secondary = np.array(self.current_colors['secondary'])
        
        # Interpola tra colori
        color = primary * intensity + secondary * (1 - intensity)
        self.led_matrix[:, :] = color.astype(np.uint8)
    
    async def _render_wave(self, animation_time: float):
        """Renderizza onda che attraversa la matrice."""
        primary = np.array(self.current_colors['primary'])
        secondary = np.array(self.current_colors['secondary'])
        
        for x in range(self.matrix_size[0]):
            for y in range(self.matrix_size[1]):
                # Calcola distanza dal centro
                center_x, center_y = self.matrix_size[0] // 2, self.matrix_size[1] // 2
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Onda radiale
                wave_value = math.sin(distance * 0.8 - animation_time * 4 * math.pi)
                intensity = (wave_value + 1) / 2
                
                color = primary * intensity + secondary * (1 - intensity)
                self.led_matrix[x, y] = color.astype(np.uint8)
    
    async def _render_spiral(self, animation_time: float):
        """Renderizza spirale rotante."""
        primary = np.array(self.current_colors['primary'])
        
        center_x, center_y = self.matrix_size[0] // 2, self.matrix_size[1] // 2
        
        for x in range(self.matrix_size[0]):
            for y in range(self.matrix_size[1]):
                # Coordinate polari
                dx, dy = x - center_x, y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                
                # Spirale
                spiral_value = math.sin(angle * 3 + distance * 0.5 - animation_time * 6 * math.pi)
                intensity = max(0, spiral_value)
                
                self.led_matrix[x, y] = (primary * intensity).astype(np.uint8)
    
    async def _render_eyes(self, animation_time: float):
        """Renderizza pattern occhi."""
        color = self.current_colors['primary']
        
        # Reset
        self.led_matrix.fill(0)
        
        # Occhio sinistro (3x2 pixel)
        eye_left = [(2, 2), (2, 3), (3, 2), (3, 3)]
        # Occhio destro  
        eye_right = [(5, 2), (5, 3), (6, 2), (6, 3)]
        
        # Blinking animation
        blink_phase = animation_time % 1.0
        if blink_phase > 0.1:  # Occhi aperti 90% del tempo
            for x, y in eye_left + eye_right:
                if 0 <= x < self.matrix_size[0] and 0 <= y < self.matrix_size[1]:
                    self.led_matrix[x, y] = color
    
    async def _render_alert_flash(self, animation_time: float):
        """Renderizza flash di allerta."""
        color = self.current_colors['primary']
        
        # Flash rapido
        flash_phase = animation_time % 0.2  # 5 flash al secondo
        if flash_phase < 0.1:
            self.led_matrix[:, :] = color
        else:
            self.led_matrix.fill(0)
    
    async def _render_breathe(self, animation_time: float):
        """Renderizza respirazione lenta."""
        # Respirazione sinusoidale molto lenta
        breath_intensity = (math.sin(animation_time * math.pi) + 1) / 4 + 0.1  # 0.1-0.6
        
        color = np.array(self.current_colors['primary']) * breath_intensity
        self.led_matrix[:, :] = color.astype(np.uint8)
    
    async def _update_hardware(self):
        """Aggiorna hardware LED o simula output."""
        if self.simulation_mode:
            # In simulation, non facciamo nulla (o potremmo salvare frame per debug)
            pass
        else:
            # TODO: Invia dati a LED matrix hardware
            # self.led_hardware.display(self.led_matrix)
            pass
    
    async def get_expression_status(self) -> Dict[str, Any]:
        """Ottieni stato corrente sistema espressioni."""
        
        available_emotions = list(self.emotion_expressions.keys())
        
        return {
            'timestamp': time.time(),
            'current_expression': self.current_expression,
            'current_pattern': self.current_pattern.value if self.current_pattern else None,
            'animation_frame': self.animation_frame,
            'animation_speed': self.animation_speed,
            'simulation_mode': self.simulation_mode,
            'is_initialized': self.is_initialized,
            'animation_running': self.animation_running,
            'available_emotions': available_emotions,
            'matrix_size': self.matrix_size,
            'statistics': self.stats.copy()
        }
    
    async def save_frame_preview(self, filename: str = None) -> bool:
        """Salva preview frame corrente (per debug)."""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"led_frame_{timestamp}.png"
            
            # Crea directory captures se non esiste
            import os
            os.makedirs("captures", exist_ok=True)
            
            # In implementazione reale si potrebbe usare PIL per salvare PNG
            # Per ora salviamo i dati raw
            filepath = f"captures/{filename}.txt"
            
            with open(filepath, 'w') as f:
                f.write(f"LED Frame Preview - {time.time()}\n")
                f.write(f"Expression: {self.current_expression}\n")
                f.write(f"Pattern: {self.current_pattern.value if self.current_pattern else 'None'}\n")
                f.write(f"Frame: {self.animation_frame}\n\n")
                
                # ASCII representation della matrice
                f.write("LED Matrix (brightness levels):\n")
                for x in range(self.matrix_size[0]):
                    row = ""
                    for y in range(self.matrix_size[1]):
                        # Calcola brightness come media RGB
                        pixel = self.led_matrix[x, y]
                        brightness = (int(pixel[0]) + int(pixel[1]) + int(pixel[2])) // 3
                        
                        if brightness > 200:
                            char = "█"
                        elif brightness > 150:
                            char = "▓"
                        elif brightness > 100:
                            char = "▒"
                        elif brightness > 50:
                            char = "░"
                        else:
                            char = " "
                        
                        row += char
                    f.write(f"{row}\n")
            
            self.logger.info(f"Frame preview salvato: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio frame preview: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup sistema espressioni."""
        await self.stop_animation_loop()
        
        if not self.simulation_mode and self.led_hardware:
            # Spegni tutti i LED
            self.led_matrix.fill(0)
            await self._update_hardware()
        
        self.logger.info("Expression Manager cleanup completato")


# Test functions
async def test_expression_manager():
    """Test del sistema di espressioni LED."""
    print("=== TESTING LED EXPRESSION MANAGER ===")
    
    # Config di test
    config = {
        'hardware': {
            'led_matrix': {
                'brightness': 8,
            }
        }
    }
    
    manager = ExpressionManager(config, simulation_mode=True)
    
    # Inizializza
    success = await manager.initialize()
    print(f"Inizializzazione: {'OK' if success else 'FAILED'}")
    
    if not success:
        return
    
    # Test diverse emozioni per 3 secondi ciascuna
    emotions_to_test = ['curious', 'cautious', 'playful', 'alert', 'focused', 'resting']
    
    for emotion in emotions_to_test:
        print(f"\n--- Testing emozione: {emotion.upper()} ---")
        
        # Imposta espressione
        await manager.set_emotion_expression(emotion, intensity=0.8)
        
        # Mostra per 3 secondi
        for second in range(3):
            await asyncio.sleep(1.0)
            
            if second == 1:  # Salva preview al secondo frame
                await manager.save_frame_preview(f"preview_{emotion}")
            
            status = await manager.get_expression_status()
            print(f"  {second+1}s: Frame {status['animation_frame']}, "
                  f"FPS: {status['statistics']['current_fps']:.1f}")
    
    # Test intensità diverse
    print(f"\n--- Testing intensità diverse ---")
    await manager.set_emotion_expression('playful', intensity=0.2)
    await asyncio.sleep(1)
    print("Intensità 0.2 (bassa)")
    
    await manager.set_emotion_expression('playful', intensity=1.0)
    await asyncio.sleep(1)
    print("Intensità 1.0 (massima)")
    
    # Statistiche finali
    print(f"\n=== STATISTICHE FINALI ===")
    final_status = await manager.get_expression_status()
    
    print(f"Espressioni renderizzate: {final_status['statistics']['expressions_rendered']}")
    print(f"Frame animazione totali: {final_status['statistics']['animation_frames']}")
    print(f"FPS corrente: {final_status['statistics']['current_fps']:.1f}")
    print(f"Emozioni disponibili: {', '.join(final_status['available_emotions'])}")
    
    await manager.cleanup()
    print("\nTest completato! Il robot ha mostrato espressioni LED emotive.")


if __name__ == "__main__":
    asyncio.run(test_expression_manager())