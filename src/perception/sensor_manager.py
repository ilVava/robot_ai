#!/usr/bin/env python3
"""
Sensor Manager - Robot AI Perception System
===========================================

Gestisce tutti i sensori fisici del robot: ultrasonico, fotoresistori.
Supporta simulation mode con dati realistici per sviluppo senza hardware.

Design:
- AsyncIO per letture non bloccanti
- Smoothing e filtering dei dati grezzi
- Safety thresholds e allarmi
- Mock data realistici in simulation

Author: Andrea Vavassori  
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Any
import statistics

class SensorManager:
    """
    Gestisce lettura e processing di tutti i sensori del robot.
    
    Sensori supportati:
    - HC-SR04 Ultrasonico (distanza ostacoli)
    - Fotoresistori x4 (livelli luce ambientale)
    """
    
    def __init__(self, config: dict, simulation_mode: bool = True):
        self.config = config.get('hardware', {})
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Configurazione sensori dal config
        self.ultrasonic_config = self.config.get('ultrasonic', {})
        self.light_config = self.config.get('light_sensors', {})
        
        # Pin GPIO (solo per hardware mode)
        self.trigger_pin = self.ultrasonic_config.get('trigger_pin', 18)
        self.echo_pin = self.ultrasonic_config.get('echo_pin', 24)
        self.light_pins = self.light_config.get('pins', [23, 25, 8, 7])
        
        # Parametri sensori
        self.max_distance = self.ultrasonic_config.get('max_distance', 400)  # cm
        self.timeout = self.ultrasonic_config.get('timeout', 1.0)  # secondi
        self.light_threshold_dark = self.light_config.get('threshold_dark', 300)
        self.light_threshold_bright = self.light_config.get('threshold_bright', 700)
        
        # Hardware interfaces (None in simulation)
        self.gpio = None
        self.adc = None
        
        # Buffers per smoothing (ultimi N valori)
        self.distance_buffer = []
        self.light_buffers = [[] for _ in range(4)]
        self.buffer_size = 5  # Media mobile su 5 campioni
        
        # Statistics e monitoring
        self.stats = {
            'distance_readings': 0,
            'light_readings': 0,
            'avg_distance': 0.0,
            'avg_light_levels': [0.0] * 4,
            'last_update_time': 0.0
        }
        
        # Simulation data per mock realistico
        self.sim_distance_base = 150.0  # cm - distanza base simulata
        self.sim_light_base = [500, 480, 520, 490]  # Valori base fotoresistori
        
        # Arduino serial interface (injected later)
        self.arduino_serial = None

        self.logger.info(f"SensorManager inizializzato - Simulation: {simulation_mode}")

    def set_arduino_serial(self, arduino_serial):
        """Imposta riferimento alla connessione seriale Arduino per letture hardware."""
        self.arduino_serial = arduino_serial
        self.logger.info("Arduino serial connection configured for hardware sensors")

    async def initialize(self) -> bool:
        """
        Inizializza interfacce hardware sensori.
        
        Returns:
            bool: True se inizializzazione ok
        """
        try:
            if not self.simulation_mode:
                # Inizializza GPIO per RPi
                self.logger.info("Inizializzando GPIO per sensori...")
                import RPi.GPIO as GPIO
                self.gpio = GPIO
                
                # Setup pins ultrasonico
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.trigger_pin, GPIO.OUT)
                GPIO.setup(self.echo_pin, GPIO.IN)
                GPIO.output(self.trigger_pin, False)
                
                # Setup ADC per fotoresistori (via Arduino)
                # In realtà leggeremo via seriale da Arduino
                self.logger.info("GPIO configurato per sensori hardware")
                
            else:
                self.logger.info("Modalità simulation - mock data attivato")
                
            self.logger.info("SensorManager inizializzato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione sensori: {e}")
            return False
    
    async def read_distance(self) -> Optional[float]:
        """
        Legge distanza da sensore ultrasonico HC-SR04.
        
        Returns:
            float: Distanza in cm, None se errore
        """
        try:
            if self.simulation_mode:
                # Mock data realistico per sviluppo
                distance = self._generate_mock_distance()
            else:
                # Lettura hardware reale
                distance = await self._read_ultrasonic_hardware()
                
            if distance is not None:
                # Applica smoothing
                distance = self._smooth_distance(distance)
                
                # Aggiorna statistics (ottimizzato con moving average)
                self.stats['distance_readings'] += 1
                if self.stats['distance_readings'] == 1:
                    self.stats['avg_distance'] = distance
                else:
                    # Exponential moving average più efficiente
                    alpha = 0.1  # Fattore di smoothing
                    self.stats['avg_distance'] = (1 - alpha) * self.stats['avg_distance'] + alpha * distance
                
                self.logger.debug(f"Distanza letta: {distance:.1f}cm")
                
            return distance
            
        except Exception as e:
            self.logger.error(f"Errore lettura distanza: {e}")
            return None
    
    async def read_light_sensors(self) -> Optional[List[float]]:
        """
        Legge valori da tutti i fotoresistori.
        
        Returns:
            List[float]: Valori 0-1000 per ogni sensore, None se errore
        """
        try:
            if self.simulation_mode:
                # Mock data con variazioni realistiche
                light_values = self._generate_mock_light()
            else:
                # Lettura hardware (via Arduino seriale)
                light_values = await self._read_light_hardware()
                
            if light_values is not None:
                # Applica smoothing per ogni sensore
                light_values = self._smooth_light_values(light_values)
                
                # Aggiorna statistics (ottimizzato)
                self.stats['light_readings'] += 1
                alpha = 0.1  # Exponential moving average
                for i, value in enumerate(light_values):
                    if self.stats['light_readings'] == 1:
                        self.stats['avg_light_levels'][i] = value
                    else:
                        self.stats['avg_light_levels'][i] = (
                            (1 - alpha) * self.stats['avg_light_levels'][i] + alpha * value
                        )
                
                self.logger.debug(f"Light levels: {[f'{v:.0f}' for v in light_values]}")
                
            return light_values
            
        except Exception as e:
            self.logger.error(f"Errore lettura fotoresistori: {e}")
            return None
    
    def _generate_mock_distance(self) -> float:
        """Genera distanza mock realistica per simulation."""
        # Simula movimento in ambiente con ostacoli
        variation = random.gauss(0, 20)  # Variazione ±20cm
        noise = random.gauss(0, 2)       # Noise sensore ±2cm
        
        distance = max(10, min(self.max_distance, 
                              self.sim_distance_base + variation + noise))
        
        # Occasionalmente simula ostacoli vicini
        if random.random() < 0.05:  # 5% probabilità ostacolo vicino
            distance = random.uniform(5, 30)
            
        return round(distance, 1)
    
    def _generate_mock_light(self) -> List[float]:
        """Genera valori fotoresistori mock realistici."""
        light_values = []
        
        for i, base_value in enumerate(self.sim_light_base):
            # Variazione graduale per simolare cambi luce ambiente
            variation = random.gauss(0, 50)  # ±50 variazione normale
            noise = random.gauss(0, 10)      # Noise sensore ±10
            
            value = max(0, min(1000, base_value + variation + noise))
            light_values.append(round(value, 1))
        
        return light_values
    
    async def _read_ultrasonic_hardware(self) -> Optional[float]:
        """Lettura hardware reale ultrasonico (via Arduino seriale)."""
        try:
            # Usa Arduino seriale per leggere ultrasonico (se disponibile)
            if hasattr(self, 'arduino_serial') and self.arduino_serial:
                response = await self.arduino_serial._send_command("READ_SENSORS", expect_response=True, timeout=2.0)

                if response and "SENSORS:" in response:
                    import json
                    # Parse JSON response: SENSORS:{"distance":150,"light":[500,480,520,490],...}
                    json_part = response.split("SENSORS:")[1]
                    sensor_data = json.loads(json_part)
                    distance = sensor_data.get('distance')

                    if distance is not None:
                        return float(distance)
                    else:
                        self.logger.error("No distance data in Arduino response")
                        return None
                else:
                    self.logger.error("No valid sensor response from Arduino")
                    return None
            else:
                self.logger.warning("Arduino serial connection not available - using GPIO fallback")
                return await self._read_ultrasonic_gpio()

        except Exception as e:
            self.logger.error(f"Errore lettura ultrasonico hardware: {e}")
            return None

    async def _read_ultrasonic_gpio(self) -> Optional[float]:
        """Lettura GPIO diretta ultrasonico (fallback)."""
        try:
            if not self.gpio:
                return None

            # Trigger pulse
            self.gpio.output(self.trigger_pin, True)
            await asyncio.sleep(0.00001)  # 10μs pulse
            self.gpio.output(self.trigger_pin, False)

            # Attendi echo start
            start_time = time.time()
            while self.gpio.input(self.echo_pin) == 0:
                if time.time() - start_time > self.timeout:
                    return None
                await asyncio.sleep(0.0001)
            pulse_start = time.time()

            # Attendi echo end
            while self.gpio.input(self.echo_pin) == 1:
                if time.time() - pulse_start > self.timeout:
                    return None
                await asyncio.sleep(0.0001)
            pulse_end = time.time()

            # Calcola distanza (velocità suono = 34300 cm/s)
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * 34300) / 2

            # Valida range
            if 2 <= distance <= self.max_distance:
                return distance
            else:
                return None

        except Exception as e:
            self.logger.error(f"Errore lettura ultrasonico GPIO: {e}")
            return None
    
    async def _read_light_hardware(self) -> Optional[List[float]]:
        """Lettura hardware fotoresistori (via Arduino seriale)."""
        try:
            # Usa Arduino seriale per leggere sensori (se disponibile)
            if hasattr(self, 'arduino_serial') and self.arduino_serial:
                response = await self.arduino_serial._send_command("READ_SENSORS", expect_response=True, timeout=2.0)

                if response and "SENSORS:" in response:
                    import json
                    # Parse JSON response: SENSORS:{"distance":150,"light":[500,480,520,490],...}
                    json_part = response.split("SENSORS:")[1]
                    sensor_data = json.loads(json_part)
                    light_values = sensor_data.get('light', [])

                    if len(light_values) == 4:
                        return [float(v) for v in light_values]
                    else:
                        self.logger.error(f"Invalid light sensor count: {len(light_values)}")
                        return None
                else:
                    self.logger.error("No valid sensor response from Arduino")
                    return None
            else:
                self.logger.warning("Arduino serial connection not available for hardware sensors")
                return None

        except Exception as e:
            self.logger.error(f"Errore lettura fotoresistori hardware: {e}")
            return None
    
    def _smooth_distance(self, new_distance: float) -> float:
        """Applica media mobile alla distanza per ridurre noise."""
        self.distance_buffer.append(new_distance)
        if len(self.distance_buffer) > self.buffer_size:
            self.distance_buffer.pop(0)
            
        # Media mobile
        return statistics.mean(self.distance_buffer)
    
    def _smooth_light_values(self, new_values: List[float]) -> List[float]:
        """Applica smoothing ai valori fotoresistori."""
        smoothed = []
        
        for i, value in enumerate(new_values):
            self.light_buffers[i].append(value)
            if len(self.light_buffers[i]) > self.buffer_size:
                self.light_buffers[i].pop(0)
                
            smoothed.append(statistics.mean(self.light_buffers[i]))
            
        return smoothed
    
    async def get_sensor_summary(self) -> Dict[str, Any]:
        """
        Ottieni riassunto completo stato sensori.
        
        Returns:
            dict: Informazioni complete sensori
        """
        distance = await self.read_distance()
        light_levels = await self.read_light_sensors()
        
        summary = {
            'timestamp': time.time(),
            'simulation_mode': self.simulation_mode,
            'distance_cm': distance,
            'light_levels': light_levels,
            'stats': self.stats.copy(),
            'status': {
                'obstacle_detected': distance is not None and distance < 30,  # <30cm = ostacolo
                'lighting_conditions': self._analyze_lighting(light_levels) if light_levels else 'unknown'
            }
        }
        
        self.stats['last_update_time'] = time.time()
        
        return summary
    
    def _analyze_lighting(self, light_levels: List[float]) -> str:
        """Analizza condizioni di illuminazione."""
        if not light_levels:
            return 'unknown'
            
        avg_light = statistics.mean(light_levels)
        
        if avg_light < self.light_threshold_dark:
            return 'dark'
        elif avg_light > self.light_threshold_bright:
            return 'bright'
        else:
            return 'normal'
    
    async def cleanup(self):
        """Rilascia risorse GPIO."""
        try:
            if self.gpio is not None:
                self.gpio.cleanup()
                self.logger.info("GPIO cleanup completato")
                
        except Exception as e:
            self.logger.error(f"Errore cleanup sensori: {e}")
        finally:
            self.gpio = None


# Test functions
async def test_sensor_manager(simulation: bool = True):
    """Test rapido del sensor manager."""
    import yaml
    
    # Config minimo per test
    test_config = {
        'hardware': {
            'ultrasonic': {
                'trigger_pin': 18,
                'echo_pin': 24,
                'max_distance': 400,
                'timeout': 1.0
            },
            'light_sensors': {
                'pins': [23, 25, 8, 7],
                'threshold_dark': 300,
                'threshold_bright': 700
            }
        }
    }
    
    sensors = SensorManager(test_config, simulation_mode=simulation)
    
    print(f"Testing Sensor Manager (simulation={simulation})...")
    
    # Inizializza
    success = await sensors.initialize()
    print(f"Inizializzazione: {'OK' if success else 'FAILED'}")
    
    if success:
        # Test letture per 10 volte
        for i in range(10):
            summary = await sensors.get_sensor_summary()
            
            distance = summary.get('distance_cm')
            light_levels = summary.get('light_levels')
            
            print(f"Reading {i+1}:")
            print(f"  Distanza: {distance:.1f}cm" if distance else "  Distanza: ERROR")
            print(f"  Light: {[f'{v:.0f}' for v in light_levels]}" if light_levels else "  Light: ERROR")
            print(f"  Status: {summary['status']}")
            
            await asyncio.sleep(0.2)  # 5Hz
            
        # Mostra statistics finali
        print(f"\nStatistics: {sensors.stats}")
        
    await sensors.cleanup()
    print("Test completato")


if __name__ == "__main__":
    # Test in modalità simulation
    asyncio.run(test_sensor_manager(simulation=True))