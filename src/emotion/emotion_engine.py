#!/usr/bin/env python3
"""
Emotion Engine - Robot AI Emotion System
========================================

Sistema che gestisce gli stati emotivi del robot come un essere vivente.
Le emozioni influenzano velocità, curiosità, cautela e reazioni del robot.

In parole semplici:
- Il robot ha "umori" come un animale domestico
- Situazioni diverse causano emozioni diverse
- Ogni emozione cambia come il robot si comporta
- LED e movimenti riflettono lo stato emotivo

Stati emotivi disponibili:
- CURIOUS: Esplora attivamente, veloce, attratto da novità
- CAUTIOUS: Lento, attento, evita rischi
- PLAYFUL: Movimenti dinamici, interagisce con oggetti  
- ALERT: Massima attenzione, pronto a reagire
- FOCUSED: Concentrato su task specifico
- RESTING: Modalità risparmio energetico, movimenti minimi

Author: Andrea Vavassori
"""

import asyncio
import logging
import time
import random
import math
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import json

class EmotionState(Enum):
    """Enum per gli stati emotivi del robot."""
    CURIOUS = "curious"
    CAUTIOUS = "cautious" 
    PLAYFUL = "playful"
    ALERT = "alert"
    FOCUSED = "focused"
    RESTING = "resting"

class EmotionEngine:
    """
    Motore principale per gestione stati emotivi del robot.
    
    Simula un sistema emotivo realistico:
    - Transizioni graduali tra stati (non cambio istantaneo)
    - Influenza di sensori esterni su emozioni
    - Personalità che modifica soglie emotive
    - Storico emotivo per pattern analysis
    """
    
    def __init__(self, config: dict, personality_traits: Dict[str, float] = None):
        self.config = config.get('behavior', {})
        self.emotions_config = self.config.get('emotions', {})
        self.logger = logging.getLogger(__name__)
        
        # Stato emotivo corrente
        self.current_emotion = EmotionState.CURIOUS  # Inizia curioso
        self.emotion_intensity = 0.7  # Intensità 0.0-1.0
        self.emotion_duration = 0.0   # Secondi nello stato corrente
        
        # Personality traits influenzano facilità transizioni
        self.personality = personality_traits or {
            'curiosity_base': 0.7,      # Quanto è curioso di natura (0-1)
            'caution_threshold': 0.5,   # Soglia per diventare cauto  
            'energy_level': 0.8,        # Livello energia generale
            'social_attraction': 0.6,   # Attrazione verso persone
            'exploration_drive': 0.8,   # Spinta ad esplorare
            'risk_tolerance': 0.4       # Tolleranza al rischio (basso = più cauto)
        }
        
        # Buffer per smooth transitions
        self.emotion_momentum = {}  # Traccia "spinta" verso ogni emozione
        for emotion in EmotionState:
            self.emotion_momentum[emotion] = 0.0
            
        # Storico emotivo per analysis
        self.emotion_history = []
        self.max_history = 1000
        
        # Triggers emotivi basati su sensori
        self.emotion_triggers = {
            'low_battery': {'target': EmotionState.RESTING, 'strength': 0.8},
            'obstacle_close': {'target': EmotionState.CAUTIOUS, 'strength': 0.6},
            'person_detected': {'target': EmotionState.PLAYFUL, 'strength': 0.4},
            'motion_detected': {'target': EmotionState.ALERT, 'strength': 0.7},
            'dark_environment': {'target': EmotionState.CAUTIOUS, 'strength': 0.5},
            'bright_environment': {'target': EmotionState.CURIOUS, 'strength': 0.3},
            'new_area': {'target': EmotionState.CURIOUS, 'strength': 0.6},
            'familiar_area': {'target': EmotionState.RESTING, 'strength': 0.2}
        }
        
        # Parametri comportamentali per ogni emozione
        self.behavior_modifiers = self._load_behavior_modifiers()
        
        # Statistics
        self.stats = {
            'total_transitions': 0,
            'time_in_emotions': {emotion.value: 0.0 for emotion in EmotionState},
            'most_frequent_emotion': EmotionState.CURIOUS.value,
            'avg_transition_time': 0.0,
            'last_update': 0.0
        }
        
        self.last_update_time = time.time()
        self.logger.info(f"Emotion Engine inizializzato - Stato: {self.current_emotion.value}")
    
    def _load_behavior_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Carica modificatori comportamentali per ogni stato emotivo."""
        
        # Default modifiers, possono essere sovrascritti da config
        default_modifiers = {
            EmotionState.CURIOUS.value: {
                'speed_multiplier': 0.8,      # Velocità moderata per esplorare
                'exploration_bias': 0.9,      # Alta spinta ad esplorare
                'caution_level': 0.3,         # Bassa cautela
                'interaction_probability': 0.7, # Probabilità interagire con oggetti
                'attention_radius': 1.5,      # Raggio attenzione in metri
                'decision_time_ms': 150       # Tempo decisioni rapide
            },
            
            EmotionState.CAUTIOUS.value: {
                'speed_multiplier': 0.4,      # Velocità molto ridotta
                'exploration_bias': 0.2,      # Bassa esplorazione
                'caution_level': 0.9,         # Alta cautela
                'interaction_probability': 0.1, # Evita interazioni
                'attention_radius': 2.5,      # Attenzione aumentata
                'decision_time_ms': 300       # Decisioni ponderate
            },
            
            EmotionState.PLAYFUL.value: {
                'speed_multiplier': 1.0,      # Velocità piena
                'exploration_bias': 0.7,      # Media esplorazione
                'caution_level': 0.4,         # Media cautela
                'interaction_probability': 0.9, # Alta interazione
                'attention_radius': 1.0,      # Focus su oggetti vicini
                'decision_time_ms': 100       # Reazioni veloci e spontanee
            },
            
            EmotionState.ALERT.value: {
                'speed_multiplier': 0.6,      # Velocità moderata per controllo
                'exploration_bias': 0.1,      # Minima esplorazione
                'caution_level': 0.8,         # Alta cautela
                'interaction_probability': 0.2, # Bassa interazione
                'attention_radius': 3.0,      # Massima attenzione ambiente
                'decision_time_ms': 50        # Reazioni istantanee
            },
            
            EmotionState.FOCUSED.value: {
                'speed_multiplier': 0.7,      # Velocità ottimale per task
                'exploration_bias': 0.3,      # Bassa esplorazione
                'caution_level': 0.6,         # Media cautela
                'interaction_probability': 0.5, # Interazione selettiva
                'attention_radius': 0.8,      # Focus ristretto
                'decision_time_ms': 200       # Decisioni ponderate ma non lente
            },
            
            EmotionState.RESTING.value: {
                'speed_multiplier': 0.1,      # Velocità minima
                'exploration_bias': 0.0,      # Nessuna esplorazione
                'caution_level': 0.9,         # Alta cautela
                'interaction_probability': 0.0, # Nessuna interazione
                'attention_radius': 0.5,      # Attenzione minima
                'decision_time_ms': 500       # Decisioni molto lente
            }
        }
        
        # Merge con config se presente
        config_modifiers = self.emotions_config
        for emotion_name, modifiers in config_modifiers.items():
            if emotion_name in default_modifiers:
                default_modifiers[emotion_name].update(modifiers)
                
        return default_modifiers
    
    async def update_emotion(self, sensor_data: Dict[str, Any], 
                           context: Dict[str, Any] = None) -> EmotionState:
        """
        Aggiorna stato emotivo basato su dati sensori e contesto.
        
        Args:
            sensor_data: Dati da sensori (distanza, luce, oggetti, etc.)
            context: Contesto aggiuntivo (batteria, posizione, tempo, etc.)
            
        Returns:
            EmotionState: Nuovo stato emotivo
        """
        try:
            current_time = time.time()
            time_delta = current_time - self.last_update_time
            
            # Aggiorna durata emozione corrente
            self.emotion_duration += time_delta
            
            # Analizza triggers emotivi dai sensori
            triggered_emotions = self._analyze_emotion_triggers(sensor_data, context or {})
            
            # Aggiorna momentum per ogni emozione
            self._update_emotion_momentum(triggered_emotions, time_delta)
            
            # Determina se cambiare stato emotivo
            new_emotion = self._determine_emotion_transition()
            
            # Effettua transizione se necessario
            if new_emotion != self.current_emotion:
                await self._transition_to_emotion(new_emotion)
            
            # Aggiorna statistics
            self._update_statistics(time_delta)
            
            self.last_update_time = current_time
            return self.current_emotion
            
        except Exception as e:
            self.logger.error(f"Errore update emozione: {e}")
            return self.current_emotion
    
    def _analyze_emotion_triggers(self, sensor_data: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[EmotionState, float]:
        """Analizza dati e determina spinte emotive."""
        
        triggered_emotions = {emotion: 0.0 for emotion in EmotionState}
        
        # Analizza batteria
        battery_level = context.get('battery_level', 100)
        if battery_level < 30:
            triggered_emotions[EmotionState.RESTING] += 0.8
        elif battery_level < 50:
            triggered_emotions[EmotionState.CAUTIOUS] += 0.3
            
        # Analizza distanza ostacoli
        distance = sensor_data.get('distance_cm', 200)
        if distance < 20:
            triggered_emotions[EmotionState.ALERT] += 0.7
        elif distance < 50:
            triggered_emotions[EmotionState.CAUTIOUS] += 0.5
        elif distance > 150:
            triggered_emotions[EmotionState.CURIOUS] += 0.4
            
        # Analizza livelli di luce
        light_levels = sensor_data.get('light_levels', [500] * 4)
        avg_light = sum(light_levels) / len(light_levels) if light_levels else 500
        
        if avg_light < 300:  # Ambiente buio
            triggered_emotions[EmotionState.CAUTIOUS] += 0.4
        elif avg_light > 700:  # Ambiente molto luminoso
            triggered_emotions[EmotionState.CURIOUS] += 0.3
            
        # Analizza oggetti rilevati
        objects_detected = sensor_data.get('objects_detected', [])
        for obj in objects_detected:
            if obj == 'person':
                triggered_emotions[EmotionState.PLAYFUL] += 0.6 * self.personality['social_attraction']
            elif obj in ['chair', 'table', 'furniture']:
                triggered_emotions[EmotionState.FOCUSED] += 0.3
                
        # Analizza movimento rilevato
        motion_detected = sensor_data.get('motion_detected', False)
        if motion_detected:
            triggered_emotions[EmotionState.ALERT] += 0.5
            
        # Influence della personalità
        triggered_emotions[EmotionState.CURIOUS] += self.personality['curiosity_base'] * 0.2
        
        # Decadimento naturale verso stati neutri nel tempo
        if self.emotion_duration > 60:  # Dopo 1 minuto
            triggered_emotions[EmotionState.CURIOUS] += 0.1
            triggered_emotions[EmotionState.RESTING] += 0.05
            
        return triggered_emotions
    
    def _update_emotion_momentum(self, triggered_emotions: Dict[EmotionState, float], 
                               time_delta: float):
        """Aggiorna momentum emotivo per transizioni smooth."""
        
        decay_rate = 0.95  # Momentum decade nel tempo
        
        for emotion in EmotionState:
            # Decadimento momentum esistente
            self.emotion_momentum[emotion] *= pow(decay_rate, time_delta)
            
            # Aggiungi nuovo trigger se presente
            trigger_strength = triggered_emotions.get(emotion, 0.0)
            if trigger_strength > 0:
                self.emotion_momentum[emotion] += trigger_strength * time_delta
                
            # Limita momentum massimo
            self.emotion_momentum[emotion] = min(1.0, self.emotion_momentum[emotion])
    
    def _determine_emotion_transition(self) -> EmotionState:
        """Determina se fare transizione emotiva basata su momentum."""
        
        # Soglia per cambiare emozione (hysteresis per evitare flickering)
        current_momentum = self.emotion_momentum[self.current_emotion]
        transition_threshold = 0.3
        
        # Trova emozione con momentum più alto
        best_emotion = self.current_emotion
        best_momentum = current_momentum + 0.1  # Bias verso emozione corrente
        
        for emotion, momentum in self.emotion_momentum.items():
            if emotion != self.current_emotion and momentum > best_momentum:
                if momentum > transition_threshold:
                    best_emotion = emotion
                    best_momentum = momentum
                    
        return best_emotion
    
    async def _transition_to_emotion(self, new_emotion: EmotionState):
        """Effettua transizione verso nuova emozione."""
        
        old_emotion = self.current_emotion
        transition_time = time.time()
        
        # Log transizione
        self.logger.info(f"Transizione emotiva: {old_emotion.value} → {new_emotion.value} "
                        f"(durata precedente: {self.emotion_duration:.1f}s)")
        
        # Aggiorna stato
        self.current_emotion = new_emotion
        self.emotion_intensity = min(1.0, self.emotion_momentum[new_emotion])
        self.emotion_duration = 0.0
        
        # Reset momentum dell'emozione raggiunta
        self.emotion_momentum[new_emotion] = 0.5  # Evita oscillazioni immediate
        
        # Salva in storico
        transition_record = {
            'timestamp': transition_time,
            'from_emotion': old_emotion.value,
            'to_emotion': new_emotion.value,
            'duration_previous': self.emotion_duration,
            'intensity': self.emotion_intensity,
            'trigger_momentum': dict([(e.value, m) for e, m in self.emotion_momentum.items()])
        }
        
        self.emotion_history.append(transition_record)
        if len(self.emotion_history) > self.max_history:
            self.emotion_history.pop(0)
            
        # Aggiorna stats
        self.stats['total_transitions'] += 1
    
    def _update_statistics(self, time_delta: float):
        """Aggiorna statistiche emotive."""
        
        # Tempo nello stato corrente
        self.stats['time_in_emotions'][self.current_emotion.value] += time_delta
        
        # Emozione più frequente
        most_frequent = max(self.stats['time_in_emotions'].items(), key=lambda x: x[1])
        self.stats['most_frequent_emotion'] = most_frequent[0]
        
        # Tempo medio tra transizioni
        if self.stats['total_transitions'] > 0:
            total_time = sum(self.stats['time_in_emotions'].values())
            self.stats['avg_transition_time'] = total_time / self.stats['total_transitions']
        
        self.stats['last_update'] = time.time()
    
    async def get_current_behavior_modifiers(self) -> Dict[str, Any]:
        """
        Ottieni modificatori comportamentali per stato emotivo corrente.
        
        Returns:
            dict: Modificatori che influenzano movimento, decisioni, etc.
        """
        base_modifiers = self.behavior_modifiers.get(self.current_emotion.value, {}).copy()
        
        # Modula con intensità emotiva
        for key, value in base_modifiers.items():
            if isinstance(value, (int, float)):
                # Interpola tra valore neutro (0.5) e valore emotivo based su intensità
                neutral_value = 0.5
                emotional_value = value
                base_modifiers[key] = neutral_value + (emotional_value - neutral_value) * self.emotion_intensity
        
        # Aggiungi metadata
        base_modifiers.update({
            'current_emotion': self.current_emotion.value,
            'emotion_intensity': self.emotion_intensity,
            'emotion_duration': self.emotion_duration,
            'personality_influence': self.personality
        })
        
        return base_modifiers
    
    async def get_emotion_status(self) -> Dict[str, Any]:
        """Ottieni stato completo sistema emotivo."""
        
        return {
            'timestamp': time.time(),
            'current_emotion': self.current_emotion.value,
            'emotion_intensity': self.emotion_intensity,
            'emotion_duration': self.emotion_duration,
            'emotion_momentum': {e.value: m for e, m in self.emotion_momentum.items()},
            'personality_traits': self.personality,
            'behavior_modifiers': await self.get_current_behavior_modifiers(),
            'statistics': self.stats.copy(),
            'recent_transitions': self.emotion_history[-5:] if self.emotion_history else []
        }
    
    async def force_emotion(self, emotion: EmotionState, intensity: float = 1.0, 
                          duration_seconds: float = None):
        """
        Forza un'emozione specifica (per testing o situazioni speciali).
        
        Args:
            emotion: Emozione da forzare
            intensity: Intensità 0.0-1.0
            duration_seconds: Durata minima (None = permanente fino a trigger naturali)
        """
        self.logger.info(f"Forzata emozione: {emotion.value} (intensità: {intensity})")
        
        # Effettua transizione
        if emotion != self.current_emotion:
            await self._transition_to_emotion(emotion)
        
        self.emotion_intensity = max(0.0, min(1.0, intensity))
        
        # Se specificata durata, imposta momentum alto per quella durata
        if duration_seconds:
            self.emotion_momentum[emotion] = 1.0
            # In implementazione reale, si potrebbe usare un timer per reset automatico


# Test functions
async def test_emotion_engine():
    """Test del sistema emotivo."""
    print("=== TESTING EMOTION ENGINE ===")
    
    # Config di test
    config = {
        'behavior': {
            'emotions': {
                'curious': {'speed_multiplier': 0.9},
                'cautious': {'speed_multiplier': 0.3}
            }
        }
    }
    
    # Personalità di test (robot curioso ma cauto)
    personality = {
        'curiosity_base': 0.8,
        'caution_threshold': 0.3,
        'energy_level': 0.7,
        'social_attraction': 0.9,
        'exploration_drive': 0.8,
        'risk_tolerance': 0.2
    }
    
    engine = EmotionEngine(config, personality)
    
    print(f"Stato iniziale: {engine.current_emotion.value}")
    
    # Simula 60 secondi di situazioni diverse
    test_scenarios = [
        # Scenario 1: Ambiente normale
        {
            'name': 'Ambiente normale',
            'sensor_data': {'distance_cm': 120, 'light_levels': [500, 480, 520, 510], 'objects_detected': []},
            'context': {'battery_level': 80},
            'duration': 10
        },
        
        # Scenario 2: Ostacolo vicino
        {
            'name': 'Ostacolo vicino!',
            'sensor_data': {'distance_cm': 15, 'light_levels': [500, 480, 520, 510], 'objects_detected': ['wall']},
            'context': {'battery_level': 75},
            'duration': 5
        },
        
        # Scenario 3: Persona rilevata
        {
            'name': 'Persona rilevata',
            'sensor_data': {'distance_cm': 80, 'light_levels': [600, 580, 620, 610], 'objects_detected': ['person']},
            'context': {'battery_level': 70},
            'duration': 8
        },
        
        # Scenario 4: Ambiente buio
        {
            'name': 'Ambiente buio',
            'sensor_data': {'distance_cm': 100, 'light_levels': [200, 180, 220, 190], 'objects_detected': []},
            'context': {'battery_level': 65},
            'duration': 7
        },
        
        # Scenario 5: Batteria bassa
        {
            'name': 'Batteria bassa',
            'sensor_data': {'distance_cm': 150, 'light_levels': [500, 480, 520, 510], 'objects_detected': []},
            'context': {'battery_level': 25},
            'duration': 10
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # Simula scenario per la durata specificata
        for second in range(scenario['duration']):
            # Aggiungi un po' di randomness per realismo
            sensor_data = scenario['sensor_data'].copy()
            sensor_data['distance_cm'] += random.uniform(-10, 10)
            
            # Aggiorna emozione
            current_emotion = await engine.update_emotion(sensor_data, scenario['context'])
            
            # Mostra stato ogni 3 secondi
            if second % 3 == 0:
                behavior = await engine.get_current_behavior_modifiers()
                print(f"  {second+1}s: {current_emotion.value} "
                      f"(intensità: {engine.emotion_intensity:.2f}, "
                      f"velocità: {behavior['speed_multiplier']:.2f})")
            
            await asyncio.sleep(0.1)  # Simula real-time
    
    # Test forzatura emozione
    print(f"\n--- Test forzatura emozione ---")
    await engine.force_emotion(EmotionState.PLAYFUL, intensity=0.9)
    behavior = await engine.get_current_behavior_modifiers()
    print(f"Emozione forzata: {engine.current_emotion.value} "
          f"(velocità: {behavior['speed_multiplier']:.2f})")
    
    # Statistiche finali
    print(f"\n=== STATISTICHE FINALI ===")
    status = await engine.get_emotion_status()
    
    print(f"Transizioni totali: {status['statistics']['total_transitions']}")
    print(f"Emozione più frequente: {status['statistics']['most_frequent_emotion']}")
    print(f"Tempo medio per transizione: {status['statistics']['avg_transition_time']:.1f}s")
    
    print(f"\nTempo in ogni emozione:")
    for emotion, time_spent in status['statistics']['time_in_emotions'].items():
        if time_spent > 0:
            print(f"  {emotion}: {time_spent:.1f}s")
    
    print(f"\nUltime transizioni:")
    for transition in status['recent_transitions']:
        print(f"  {transition['from_emotion']} → {transition['to_emotion']} "
              f"({transition['duration_previous']:.1f}s)")
    
    print("\nTest completato! Il robot ha mostrato emozioni realistiche.")


if __name__ == "__main__":
    asyncio.run(test_emotion_engine())