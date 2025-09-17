#!/usr/bin/env python3
"""
Camera Handler - Robot AI Perception System
===========================================

Gestisce la cattura e preprocessing delle immagini dalla camera.
Supporta sia modalità simulation (webcam MacBook) che hardware reale (RPi Camera).

Design:
- AsyncIO per non bloccare il main loop
- Caching frame per evitare riprocessing
- Auto-switch simulation/hardware mode
- Lightweight processing per RPi5

Author: Andrea Vavassori
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np

class CameraHandler:
    """
    Gestisce cattura video e preprocessing immagini.
    
    Funziona sia in simulation mode (webcam) che hardware mode (RPi Camera).
    """
    
    def __init__(self, config: dict, simulation_mode: bool = True):
        self.config = config.get('hardware', {}).get('camera', {})
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Configurazione camera
        self.resolution = tuple(self.config.get('resolution', [640, 480]))
        self.framerate = self.config.get('framerate', 30)
        self.rotation = self.config.get('rotation', 0)
        
        # Stato interno
        self.camera = None
        self.current_frame = None
        self.frame_timestamp = 0
        self.frame_cache_duration = 0.05  # Cache frame per 50ms (20 FPS max)
        self.is_initialized = False
        
        # Statistics per monitoring
        self.stats = {
            'frames_captured': 0,
            'frames_cached': 0,
            'avg_capture_time': 0.0,
            'last_fps': 0.0
        }
        
        self.logger.info(f"CameraHandler inizializzato - Simulation: {simulation_mode}")
        
    async def initialize(self) -> bool:
        """
        Inizializza la camera (webcam o RPi camera module).
        
        Returns:
            bool: True se inizializzazione ok, False altrimenti
        """
        try:
            if self.simulation_mode:
                # Usa webcam MacBook per sviluppo
                self.logger.info("Inizializzando webcam per simulation mode...")
                self.camera = cv2.VideoCapture(0)  # Default webcam
                
                if not self.camera.isOpened():
                    self.logger.error("Impossibile aprire webcam")
                    return False
                    
                # Configura webcam
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.camera.set(cv2.CAP_PROP_FPS, self.framerate)
                
            else:
                # RPi Camera Module (implementazione per deployment)
                self.logger.info("Inizializzando RPi Camera Module...")
                try:
                    # Import solo su RPi per evitare errori su MacBook
                    from picamera2 import Picamera2
                    self.camera = Picamera2()
                    
                    # Configurazione RPi camera
                    config = self.camera.create_still_configuration(
                        main={"size": self.resolution}
                    )
                    self.camera.configure(config)
                    self.camera.start()
                    
                except ImportError:
                    self.logger.error("picamera2 non disponibile - usa simulation mode")
                    return False
                    
            self.is_initialized = True
            self.logger.info(f"Camera inizializzata: {self.resolution[0]}x{self.resolution[1]}@{self.framerate}fps")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione camera: {e}")
            return False
    
    async def capture_frame(self, force_new: bool = False) -> Optional[np.ndarray]:
        """
        Cattura un nuovo frame dalla camera.
        
        Args:
            force_new: Se True, cattura sempre nuovo frame (ignora cache)
            
        Returns:
            numpy.ndarray: Frame catturato o None se errore
        """
        if not self.is_initialized:
            self.logger.warning("Camera non inizializzata")
            return None
            
        current_time = time.time()
        
        # Usa frame cached se ancora valido (ottimizzazione performance)
        if (not force_new and 
            self.current_frame is not None and 
            (current_time - self.frame_timestamp) < self.frame_cache_duration):
            
            self.stats['frames_cached'] += 1
            return self.current_frame.copy()
        
        # Cattura nuovo frame
        capture_start = time.time()
        
        try:
            if self.simulation_mode:
                # Webcam capture
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Impossibile catturare frame da webcam")
                    return None
                    
            else:
                # RPi camera capture
                frame = self.camera.capture_array()
                # Converte da RGB a BGR per compatibilità OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Applica rotazione se necessaria
            if self.rotation != 0:
                frame = self._rotate_frame(frame, self.rotation)
                
            # Aggiorna cache
            self.current_frame = frame.copy()
            self.frame_timestamp = current_time
            
            # Aggiorna statistics
            capture_time = time.time() - capture_start
            self.stats['frames_captured'] += 1
            self.stats['avg_capture_time'] = (
                (self.stats['avg_capture_time'] * (self.stats['frames_captured'] - 1) + 
                 capture_time) / self.stats['frames_captured']
            )
            self.stats['last_fps'] = 1.0 / capture_time if capture_time > 0 else 0
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Errore cattura frame: {e}")
            return None
    
    def _rotate_frame(self, frame: np.ndarray, angle: int) -> np.ndarray:
        """
        Ruota il frame dell'angolo specificato.
        
        Args:
            frame: Frame da ruotare
            angle: Angoli di rotazione (90, 180, 270)
            
        Returns:
            numpy.ndarray: Frame ruotato
        """
        if angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return frame
    
    async def get_frame_info(self) -> Dict[str, Any]:
        """
        Ottieni informazioni sul frame corrente.
        
        Returns:
            dict: Informazioni frame e performance
        """
        info = {
            'resolution': self.resolution,
            'simulation_mode': self.simulation_mode,
            'is_initialized': self.is_initialized,
            'has_current_frame': self.current_frame is not None,
            'frame_age_ms': (time.time() - self.frame_timestamp) * 1000 if self.current_frame is not None else None,
            'stats': self.stats.copy()
        }
        
        if self.current_frame is not None:
            info['frame_shape'] = self.current_frame.shape
            info['frame_dtype'] = str(self.current_frame.dtype)
            
        return info
    
    async def save_frame(self, filename: str, frame: Optional[np.ndarray] = None) -> bool:
        """
        Salva frame su disco (per debugging).
        
        Args:
            filename: Nome file (path relativo a captures/)
            frame: Frame da salvare (usa current_frame se None)
            
        Returns:
            bool: True se salvato con successo
        """
        try:
            if frame is None:
                frame = self.current_frame
                
            if frame is None:
                self.logger.warning("Nessun frame da salvare")
                return False
                
            # Crea directory captures se non esiste
            capture_dir = Path("captures")
            capture_dir.mkdir(exist_ok=True)
            
            filepath = capture_dir / filename
            success = cv2.imwrite(str(filepath), frame)
            
            if success:
                self.logger.info(f"Frame salvato: {filepath}")
            else:
                self.logger.error(f"Errore salvataggio frame: {filepath}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Errore save_frame: {e}")
            return False
    
    async def cleanup(self):
        """Rilascia risorse camera."""
        try:
            if self.camera is not None:
                if self.simulation_mode:
                    self.camera.release()
                else:
                    self.camera.stop()
                    self.camera.close()
                    
                self.logger.info("Camera cleanup completato")
                
        except Exception as e:
            self.logger.error(f"Errore cleanup camera: {e}")
        finally:
            self.camera = None
            self.is_initialized = False


# Funzioni utility per testing
async def test_camera_handler(simulation: bool = True):
    """Test rapido del camera handler."""
    import yaml
    
    # Config minimo per test
    test_config = {
        'hardware': {
            'camera': {
                'resolution': [320, 240],  # Risoluzione bassa per test
                'framerate': 15,
                'rotation': 0
            }
        }
    }
    
    camera = CameraHandler(test_config, simulation_mode=simulation)
    
    print(f"Testing Camera Handler (simulation={simulation})...")
    
    # Test inizializzazione
    success = await camera.initialize()
    print(f"Inizializzazione: {'OK' if success else 'FAILED'}")
    
    if success:
        # Test cattura frame
        for i in range(5):
            frame = await camera.capture_frame()
            if frame is not None:
                print(f"Frame {i+1}: {frame.shape}")
                # Salva primo frame
                if i == 0:
                    await camera.save_frame(f"test_frame_{int(time.time())}.jpg", frame)
            else:
                print(f"Frame {i+1}: FAILED")
                
            await asyncio.sleep(0.1)
        
        # Mostra info
        info = await camera.get_frame_info()
        print(f"Info camera: {info}")
        
    await camera.cleanup()
    print("Test completato")


if __name__ == "__main__":
    # Test in modalità simulation
    asyncio.run(test_camera_handler(simulation=True))