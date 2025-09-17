#!/usr/bin/env python3
"""
SLAM System - Robot AI Memory System
====================================

Sistema di localizzazione e mappatura simultanea (SLAM).
Crea e mantiene una mappa 2D dell'ambiente mentre traccia la posizione del robot.

In parole semplici:
- Il robot "disegna" una mappa di dove si trova
- Ricorda gli ostacoli (muri, mobili) e spazi liberi  
- Sa sempre dove si trova nella mappa (X,Y coordinate)
- Funziona sia con dati simulati che sensori reali

Author: Andrea Vavassori
"""

import asyncio
import logging
import json
import time
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

class SLAMSystem:
    """
    Sistema SLAM per mappatura e localizzazione.
    
    Mantiene una griglia 2D dell'ambiente:
    - 0 = spazio libero (robot può passare)
    - 1 = ostacolo (muro, mobile, etc.)
    - -1 = sconosciuto (non ancora esplorato)
    """
    
    def __init__(self, config: dict, simulation_mode: bool = True):
        self.config = config.get('ai', {}).get('slam', {})
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Configurazione mappa
        self.map_resolution = self.config.get('map_resolution', 0.05)  # metri per pixel
        self.map_size = tuple(self.config.get('map_size', [400, 400]))  # pixels (20x20 metri)
        self.laser_range = self.config.get('laser_range', 4.0)  # metri max distanza sensori
        
        # Mappa 2D: -1=sconosciuto, 0=libero, 1=ostacolo
        self.grid_map = np.full(self.map_size, -1, dtype=np.int8)
        
        # Posizione robot nella mappa (pixel coordinates)
        self.robot_position = [self.map_size[0]//2, self.map_size[1]//2]  # Centro mappa
        self.robot_orientation = 0.0  # radianti, 0=nord
        
        # Cache trigonometriche per performance
        self._cos_orientation = 1.0
        self._sin_orientation = 0.0
        self._last_orientation_update = 0.0
        
        # Storico posizioni per path tracking
        self.position_history = []
        self.max_history = 1000  # Tieni ultime 1000 posizioni
        
        # Statistics
        self.stats = {
            'explored_area_percent': 0.0,
            'total_obstacles': 0,
            'total_free_space': 0,
            'distance_traveled': 0.0,
            'last_update_time': 0.0
        }
        
        # Simulation: ambiente virtuale con ostacoli
        if simulation_mode:
            self._create_simulation_environment()
            
        self.logger.info(f"SLAM System inizializzato - Map: {self.map_size[0]}x{self.map_size[1]}")
    
    def _create_simulation_environment(self):
        """Crea un ambiente virtuale con ostacoli per testing."""
        # Simula una stanza con mobili
        # Muri perimetrali
        self.grid_map[0, :] = 1     # Muro nord
        self.grid_map[-1, :] = 1    # Muro sud  
        self.grid_map[:, 0] = 1     # Muro ovest
        self.grid_map[:, -1] = 1    # Muro est
        
        # Aggiungi alcuni "mobili" simulati
        # Tavolo (rettangolo)
        self.grid_map[100:120, 150:200] = 1
        
        # Divano (L-shape)
        self.grid_map[250:270, 100:150] = 1
        self.grid_map[250:300, 140:150] = 1
        
        # Sedia (piccolo quadrato)
        self.grid_map[180:190, 80:90] = 1
        
        self.logger.info("Ambiente simulato creato con ostacoli")
    
    async def update_position(self, distance_reading: float, light_levels: List[float] = None) -> bool:
        """
        Aggiorna posizione robot e mappa basandosi su lettura sensore distanza.
        
        Args:
            distance_reading: Distanza ostacolo in cm dal sensore ultrasonico
            light_levels: Valori fotoresistori (opzionale)
            
        Returns:
            bool: True se update riuscito
        """
        try:
            # Converte distanza da cm a pixels nella mappa
            distance_pixels = distance_reading / 100.0 / self.map_resolution
            
            # Simula movimento del robot (in modalità simulation)
            if self.simulation_mode:
                await self._simulate_robot_movement()
            
            # Aggiorna mappa con nuove informazioni
            self._update_map_with_sensor_data(distance_reading)
            
            # Salva posizione corrente nello storico
            current_pos = self.robot_position.copy()
            current_pos.append(time.time())  # Aggiungi timestamp
            self.position_history.append(current_pos)
            
            # Mantieni storico limitato per memoria
            if len(self.position_history) > self.max_history:
                self.position_history.pop(0)
            
            # Aggiorna statistics
            self._update_statistics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore update posizione: {e}")
            return False
    
    async def _simulate_robot_movement(self):
        """Simula movimento casuale del robot per testing."""
        # Movimento simulato: piccoli step casuali
        import random
        
        # Cambio direzione occasionale
        if random.random() < 0.1:  # 10% probabilità cambio direzione
            self.robot_orientation += random.uniform(-0.5, 0.5)  # ±30 gradi
        
        # Movimento in avanti nella direzione corrente
        step_size = 2  # 2 pixels per step (10cm reali)
        
        # Aggiorna cache trigonometriche se necessario
        if abs(self.robot_orientation - self._last_orientation_update) > 0.01:
            self._cos_orientation = math.cos(self.robot_orientation)
            self._sin_orientation = math.sin(self.robot_orientation)
            self._last_orientation_update = self.robot_orientation
        
        new_x = self.robot_position[0] + step_size * self._cos_orientation
        new_y = self.robot_position[1] + step_size * self._sin_orientation
        
        # Controlla se nuova posizione è valida (non negli ostacoli)
        new_x = max(5, min(self.map_size[0] - 5, int(new_x)))
        new_y = max(5, min(self.map_size[1] - 5, int(new_y)))
        
        # Se c'è un ostacolo nella nuova posizione, gira
        if self.grid_map[new_x, new_y] == 1:
            self.robot_orientation += random.uniform(1.0, 2.0)  # Gira 60-120 gradi
        else:
            # Aggiorna posizione
            old_pos = self.robot_position.copy()
            self.robot_position = [new_x, new_y]
            
            # Calcola distanza percorsa
            distance_moved = math.sqrt((new_x - old_pos[0])**2 + (new_y - old_pos[1])**2)
            self.stats['distance_traveled'] += distance_moved * self.map_resolution
    
    def _update_map_with_sensor_data(self, distance_cm: float):
        """Aggiorna mappa con dati del sensore ultrasonico."""
        # Converte distanza in pixels
        distance_pixels = int(distance_cm / 100.0 / self.map_resolution)
        
        # Calcola punto dove è l'ostacolo (usa cache trigonometriche)
        obstacle_x = self.robot_position[0] + distance_pixels * self._cos_orientation
        obstacle_y = self.robot_position[1] + distance_pixels * self._sin_orientation
        
        # Assicura che sia dentro la mappa
        obstacle_x = max(0, min(self.map_size[0] - 1, int(obstacle_x)))
        obstacle_y = max(0, min(self.map_size[1] - 1, int(obstacle_y)))
        
        # Marca spazio libero tra robot e ostacolo
        steps = max(1, distance_pixels)
        for i in range(steps):
            if i == steps - 1:
                # Ultimo punto = ostacolo
                if distance_cm < 300:  # Solo se ostacolo abbastanza vicino
                    self.grid_map[obstacle_x, obstacle_y] = 1
            else:
                # Punti intermedi = spazio libero (usa cache trigonometriche)
                free_x = self.robot_position[0] + i * self._cos_orientation
                free_y = self.robot_position[1] + i * self._sin_orientation
                
                free_x = max(0, min(self.map_size[0] - 1, int(free_x)))
                free_y = max(0, min(self.map_size[1] - 1, int(free_y)))
                
                self.grid_map[free_x, free_y] = 0  # Spazio libero
    
    def _update_statistics(self):
        """Aggiorna statistiche della mappa."""
        # Conta celle esplorate
        unknown_cells = np.sum(self.grid_map == -1)
        total_cells = self.map_size[0] * self.map_size[1]
        explored_cells = total_cells - unknown_cells
        
        self.stats['explored_area_percent'] = (explored_cells / total_cells) * 100
        self.stats['total_obstacles'] = np.sum(self.grid_map == 1)
        self.stats['total_free_space'] = np.sum(self.grid_map == 0)
        self.stats['last_update_time'] = time.time()
    
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Ottieni stato completo del sistema SLAM.
        
        Returns:
            dict: Posizione, orientamento, statistiche mappa
        """
        # Converti posizione da pixels a coordinate reali (metri)
        real_position = [
            self.robot_position[0] * self.map_resolution,
            self.robot_position[1] * self.map_resolution
        ]
        
        return {
            'timestamp': time.time(),
            'robot_position_pixels': self.robot_position.copy(),
            'robot_position_meters': real_position,
            'robot_orientation_degrees': math.degrees(self.robot_orientation),
            'map_size': self.map_size,
            'map_resolution': self.map_resolution,
            'simulation_mode': self.simulation_mode,
            'statistics': self.stats.copy(),
            'position_history_length': len(self.position_history)
        }
    
    async def save_map(self, filename: str = None) -> bool:
        """
        Salva mappa corrente su file per analisi.
        
        Args:
            filename: Nome file (default: timestamp automatico)
            
        Returns:
            bool: True se salvato con successo
        """
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"slam_map_{timestamp}.npz"
            
            # Crea directory se non esiste
            maps_dir = Path("data/maps")
            maps_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = maps_dir / filename
            
            # Salva mappa e metadata
            np.savez_compressed(
                filepath,
                grid_map=self.grid_map,
                robot_position=self.robot_position,
                robot_orientation=self.robot_orientation,
                position_history=np.array(self.position_history) if self.position_history else np.array([]),
                map_resolution=self.map_resolution,
                statistics=self.stats
            )
            
            self.logger.info(f"Mappa salvata: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio mappa: {e}")
            return False
    
    async def load_map(self, filename: str) -> bool:
        """
        Carica mappa precedente da file.
        
        Args:
            filename: Nome file da caricare
            
        Returns:
            bool: True se caricato con successo
        """
        try:
            filepath = Path("data/maps") / filename
            
            if not filepath.exists():
                self.logger.error(f"File mappa non trovato: {filepath}")
                return False
            
            # Carica dati
            data = np.load(filepath)
            
            self.grid_map = data['grid_map']
            self.robot_position = data['robot_position'].tolist()
            self.robot_orientation = float(data['robot_orientation'])
            
            if 'position_history' in data and data['position_history'].size > 0:
                self.position_history = data['position_history'].tolist()
            
            if 'statistics' in data:
                self.stats = data['statistics'].item()
            
            self.logger.info(f"Mappa caricata: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore caricamento mappa: {e}")
            return False
    
    def get_map_area_around_robot(self, radius_pixels: int = 50) -> np.ndarray:
        """
        Ottieni area della mappa intorno al robot per visualizzazione.
        
        Args:
            radius_pixels: Raggio in pixels intorno al robot
            
        Returns:
            numpy.ndarray: Sottomappa intorno al robot
        """
        x, y = self.robot_position
        
        # Calcola bounds
        x_min = max(0, x - radius_pixels)
        x_max = min(self.map_size[0], x + radius_pixels)
        y_min = max(0, y - radius_pixels)
        y_max = min(self.map_size[1], y + radius_pixels)
        
        return self.grid_map[x_min:x_max, y_min:y_max]
    
    async def cleanup(self):
        """Cleanup finale del sistema SLAM."""
        # Salva mappa finale
        await self.save_map("final_map.npz")
        self.logger.info("SLAM System cleanup completato")


# Testing functions
async def test_slam_system(duration_seconds: int = 30):
    """Test del sistema SLAM per X secondi."""
    import random
    
    # Config base per test
    test_config = {
        'ai': {
            'slam': {
                'map_resolution': 0.05,
                'map_size': [400, 400], 
                'laser_range': 4.0
            }
        }
    }
    
    slam = SLAMSystem(test_config, simulation_mode=True)
    
    print(f"Testing SLAM System per {duration_seconds} secondi...")
    print("Il robot simulato esplorerà l'ambiente virtuale")
    
    start_time = time.time()
    updates = 0
    
    # Loop di esplorazione simulata
    while time.time() - start_time < duration_seconds:
        # Simula lettura sensore (distanza casuale realistica)
        distance = random.uniform(10, 200)  # 10cm - 2m
        
        # Aggiorna SLAM
        await slam.update_position(distance)
        updates += 1
        
        # Mostra progresso ogni 5 secondi
        elapsed = time.time() - start_time
        if updates % 50 == 0:  # Ogni ~2.5 sec se loop a 20Hz
            state = await slam.get_current_state()
            print(f"  {elapsed:.1f}s - Pos: [{state['robot_position_pixels'][0]:.0f}, {state['robot_position_pixels'][1]:.0f}] - "
                  f"Esplorato: {state['statistics']['explored_area_percent']:.1f}%")
        
        await asyncio.sleep(0.05)  # 20Hz
    
    # Risultati finali
    final_state = await slam.get_current_state()
    print(f"\n=== RISULTATI SLAM TEST ===")
    print(f"Updates totali: {updates}")
    print(f"Distanza percorsa: {final_state['statistics']['distance_traveled']:.2f}m")
    print(f"Area esplorata: {final_state['statistics']['explored_area_percent']:.1f}%")
    print(f"Ostacoli trovati: {final_state['statistics']['total_obstacles']}")
    print(f"Spazio libero mappato: {final_state['statistics']['total_free_space']}")
    
    # Salva mappa finale
    await slam.save_map("test_slam_map.npz")
    print("Mappa salvata in data/maps/test_slam_map.npz")
    
    await slam.cleanup()
    print("Test completato!")


if __name__ == "__main__":
    # Test SLAM per 30 secondi
    asyncio.run(test_slam_system(30))