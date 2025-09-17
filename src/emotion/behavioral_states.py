#!/usr/bin/env python3
"""
Behavioral States Manager - Robot AI Emotion System
===================================================

Sistema che coordina emozioni, espressioni LED e modificatori comportamentali.
È il "direttore d'orchestra" che sincronizza tutti gli aspetti emotivi del robot.

In parole semplici:
- Riceve dati dai sensori 
- Determina emozione appropriata
- Coordina espressioni LED con stati emotivi
- Fornisce parametri comportamentali per movimento e decisioni
- Mantiene coerenza tra "mente" e "corpo" del robot

È il ponte tra il sistema emotivo interno e i comportamenti visibili esterni.

Author: Andrea Vavassori
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
import json

# Import dei sistemi emotivi
from .emotion_engine import EmotionEngine, EmotionState
from .expression_manager import ExpressionManager

class BehavioralStates:
    """
    Manager centrale per coordinare tutti gli aspetti comportamentali emotivi.
    
    Responsabilità:
    - Sincronizzazione emozioni ↔ espressioni LED
    - Adattamento parametri comportamentali in tempo reale
    - Gestione transizioni smooth tra stati
    - Monitoring e logging stati comportamentali
    - Interface unificata per il sistema cognitive
    """
    
    def __init__(self, config: dict, simulation_mode: bool = True):
        self.config = config
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(__name__)
        
        # Configuration per behavioral mapping
        self.behavior_config = config.get('behavior', {})
        
        # Personalità del robot (influenza tutti i sistemi)
        self.personality_traits = self._load_personality_traits()
        
        # Sistemi emotivi core
        self.emotion_engine = EmotionEngine(config, self.personality_traits)
        self.expression_manager = ExpressionManager(config, simulation_mode)
        
        # Stato comportamentale corrente
        self.current_state = {
            'emotion': EmotionState.CURIOUS,
            'intensity': 0.7,
            'behavior_modifiers': {},
            'last_update': 0.0,
            'stable_duration': 0.0
        }
        
        # Buffer per smooth transitions dei parametri comportamentali
        self.behavior_buffer = {}
        self.buffer_size = 5  # Media mobile su N campioni
        
        # Statistics e monitoring
        self.stats = {
            'state_changes': 0,
            'total_updates': 0,
            'avg_state_duration': 0.0,
            'most_frequent_state': EmotionState.CURIOUS.value,
            'state_distribution': {state.value: 0.0 for state in EmotionState},
            'last_sensor_update': 0.0
        }
        
        # Sistema inizializzato flag
        self.is_initialized = False
        
        self.logger.info("Behavioral States Manager inizializzato")
    
    def _load_personality_traits(self) -> Dict[str, float]:
        """Carica tratti di personalità del robot."""
        
        # Default personality (robot equilibrato)
        default_personality = {
            'curiosity_base': 0.7,        # Livello base curiosità
            'caution_threshold': 0.5,     # Soglia per diventare cauto
            'energy_level': 0.8,          # Energia generale
            'social_attraction': 0.6,     # Attrazione verso persone
            'exploration_drive': 0.8,     # Spinta ad esplorare
            'risk_tolerance': 0.4,        # Tolleranza rischio
            'attention_span': 0.6,        # Durata focus su task
            'emotional_stability': 0.7,   # Resistenza a cambi emotivi rapidi
            'learning_eagerness': 0.8,    # Desiderio di apprendere
            'playfulness': 0.6            # Tendenza al gioco
        }
        
        # Override con config se presente
        config_personality = self.behavior_config.get('personality_traits', {})
        personality = default_personality.copy()
        personality.update(config_personality)
        
        # Normalizza valori a 0-1
        for key, value in personality.items():
            personality[key] = max(0.0, min(1.0, value))
        
        self.logger.info(f"Personalità caricata: curiosity={personality['curiosity_base']:.2f}, "
                        f"caution={personality['caution_threshold']:.2f}")
        
        return personality
    
    async def initialize(self) -> bool:
        """Inizializza tutti i sottosistemi comportamentali."""
        try:
            self.logger.info("Inizializzando sottosistemi comportamentali...")
            
            # Inizializza emotion engine (non ha hardware dependencies)
            emotion_ok = True  # EmotionEngine non ha initialize method
            
            # Inizializza expression manager
            expression_ok = await self.expression_manager.initialize()
            
            if emotion_ok and expression_ok:
                # Stato iniziale
                await self._sync_emotion_to_expression()
                await self._update_behavior_modifiers()
                
                self.is_initialized = True
                self.logger.info("Behavioral States Manager inizializzato con successo")
                return True
            else:
                self.logger.error("Errore inizializzazione sottosistemi")
                return False
                
        except Exception as e:
            self.logger.error(f"Errore inizializzazione behavioral states: {e}")
            return False
    
    async def update_from_sensors(self, sensor_data: Dict[str, Any], 
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Aggiorna stato comportamentale basato su dati sensori.
        
        Args:
            sensor_data: Dati da perception system
            context: Contesto aggiuntivo (batteria, posizione, etc.)
            
        Returns:
            dict: Stato comportamentale corrente con modificatori
        """
        try:
            update_start_time = time.time()
            
            # Aggiorna emotion engine
            new_emotion = await self.emotion_engine.update_emotion(sensor_data, context or {})
            
            # Controlla se emozione è cambiata
            emotion_changed = new_emotion != self.current_state['emotion']
            
            if emotion_changed:
                self.logger.info(f"Cambio stato comportamentale: "
                               f"{self.current_state['emotion'].value} → {new_emotion.value}")
                
                # Reset durata stato stabile
                self.current_state['stable_duration'] = 0.0
                self.stats['state_changes'] += 1
                
                # Sincronizza espressione LED
                await self._sync_emotion_to_expression()
                
            else:
                # Incrementa durata stato stabile
                time_delta = update_start_time - self.current_state['last_update']
                self.current_state['stable_duration'] += time_delta
            
            # Aggiorna stato corrente
            self.current_state.update({
                'emotion': new_emotion,
                'intensity': self.emotion_engine.emotion_intensity,
                'last_update': update_start_time
            })
            
            # Aggiorna modificatori comportamentali
            await self._update_behavior_modifiers()
            
            # Aggiorna statistics
            self._update_statistics()
            
            self.stats['total_updates'] += 1
            self.stats['last_sensor_update'] = update_start_time
            
            return self.current_state.copy()
            
        except Exception as e:
            self.logger.error(f"Errore update from sensors: {e}")
            return self.current_state.copy()
    
    async def _sync_emotion_to_expression(self):
        """Sincronizza emozione corrente con espressione LED."""
        try:
            emotion_name = self.current_state['emotion'].value
            intensity = self.emotion_engine.emotion_intensity
            
            # Imposta espressione LED
            await self.expression_manager.set_emotion_expression(emotion_name, intensity)
            
            self.logger.debug(f"Espressione sincronizzata: {emotion_name} (intensità: {intensity:.2f})")
            
        except Exception as e:
            self.logger.error(f"Errore sync emotion to expression: {e}")
    
    async def _update_behavior_modifiers(self):
        """Aggiorna modificatori comportamentali con smoothing."""
        try:
            # Ottieni modificatori base dall'emotion engine
            raw_modifiers = await self.emotion_engine.get_current_behavior_modifiers()
            
            # Applica personality influence
            personality_modifiers = self._apply_personality_influence(raw_modifiers)
            
            # Applica smoothing per transizioni fluide
            smooth_modifiers = self._smooth_behavior_modifiers(personality_modifiers)
            
            # Salva in stato corrente
            self.current_state['behavior_modifiers'] = smooth_modifiers
            
        except Exception as e:
            self.logger.error(f"Errore update behavior modifiers: {e}")
    
    def _apply_personality_influence(self, base_modifiers: Dict[str, Any]) -> Dict[str, Any]:
        """Applica influenza personalità ai modificatori comportamentali."""
        
        modified = base_modifiers.copy()
        personality = self.personality_traits
        
        # Influenza velocità con energy_level
        if 'speed_multiplier' in modified:
            energy_factor = 0.5 + personality['energy_level'] * 0.5  # 0.5-1.0
            modified['speed_multiplier'] *= energy_factor
        
        # Influenza esplorazione con exploration_drive
        if 'exploration_bias' in modified:
            exploration_factor = personality['exploration_drive']
            modified['exploration_bias'] = (modified['exploration_bias'] + exploration_factor) / 2
        
        # Influenza cautela con risk_tolerance (inverso)
        if 'caution_level' in modified:
            risk_factor = 1.0 - personality['risk_tolerance']
            modified['caution_level'] = (modified['caution_level'] + risk_factor) / 2
        
        # Influenza interazioni con social_attraction
        if 'interaction_probability' in modified:
            social_factor = personality['social_attraction']
            modified['interaction_probability'] *= social_factor
        
        # Influenza tempi decisione con emotional_stability
        if 'decision_time_ms' in modified:
            stability_factor = personality['emotional_stability']
            # Più stabilità = decisioni più ponderate
            modified['decision_time_ms'] *= (1.0 + stability_factor * 0.5)
        
        return modified
    
    def _smooth_behavior_modifiers(self, new_modifiers: Dict[str, Any]) -> Dict[str, Any]:
        """Applica smoothing ai modificatori per transizioni fluide."""
        
        smoothed = new_modifiers.copy()
        
        # Per ogni parametro numerico, applica media mobile
        for key, value in new_modifiers.items():
            if isinstance(value, (int, float)):
                # Inizializza buffer se non esiste
                if key not in self.behavior_buffer:
                    self.behavior_buffer[key] = []
                
                # Aggiungi nuovo valore
                self.behavior_buffer[key].append(value)
                
                # Mantieni buffer limitato
                if len(self.behavior_buffer[key]) > self.buffer_size:
                    self.behavior_buffer[key].pop(0)
                
                # Calcola media
                smoothed[key] = sum(self.behavior_buffer[key]) / len(self.behavior_buffer[key])
        
        return smoothed
    
    def _update_statistics(self):
        """Aggiorna statistiche comportamentali."""
        
        current_emotion = self.current_state['emotion'].value
        
        # Aggiorna distribuzione stati
        self.stats['state_distribution'][current_emotion] += 1
        
        # Trova stato più frequente
        most_frequent = max(self.stats['state_distribution'].items(), key=lambda x: x[1])
        self.stats['most_frequent_state'] = most_frequent[0]
        
        # Calcola durata media stato
        if self.stats['state_changes'] > 0:
            total_time = sum(self.stats['state_distribution'].values())
            self.stats['avg_state_duration'] = total_time / self.stats['state_changes']
    
    async def get_behavior_parameters(self) -> Dict[str, Any]:
        """
        Ottieni parametri comportamentali correnti per altri sistemi.
        
        Returns:
            dict: Parametri comportamentali completi
        """
        if not self.current_state['behavior_modifiers']:
            # Fallback ai parametri di default se non ancora inizializzato
            return {
                'speed_multiplier': 0.7,
                'exploration_bias': 0.5,
                'caution_level': 0.5,
                'interaction_probability': 0.5,
                'decision_time_ms': 200,
                'current_emotion': EmotionState.CURIOUS.value,
                'emotion_intensity': 0.7
            }
        
        return self.current_state['behavior_modifiers'].copy()
    
    async def get_emotional_state(self) -> Dict[str, Any]:
        """Ottieni stato emotivo completo."""
        
        emotion_status = await self.emotion_engine.get_emotion_status()
        expression_status = await self.expression_manager.get_expression_status()
        
        return {
            'timestamp': time.time(),
            'current_emotion': self.current_state['emotion'].value,
            'emotion_intensity': self.current_state['intensity'],
            'stable_duration': self.current_state['stable_duration'],
            'behavior_modifiers': self.current_state['behavior_modifiers'],
            'personality_traits': self.personality_traits,
            'emotion_engine_status': emotion_status,
            'expression_status': expression_status,
            'statistics': self.stats.copy()
        }
    
    async def force_emotional_state(self, emotion: str, intensity: float = 1.0, 
                                  duration_seconds: float = None):
        """
        Forza uno stato emotivo specifico.
        
        Args:
            emotion: Nome emozione da forzare
            intensity: Intensità 0.0-1.0
            duration_seconds: Durata minima (None = fino a override naturale)
        """
        try:
            # Converti string a enum
            emotion_enum = EmotionState(emotion)
            
            # Forza emozione
            await self.emotion_engine.force_emotion(emotion_enum, intensity, duration_seconds)
            
            # Sincronizza espressione
            await self._sync_emotion_to_expression()
            
            # Aggiorna stato
            self.current_state.update({
                'emotion': emotion_enum,
                'intensity': intensity,
                'stable_duration': 0.0
            })
            
            self.logger.info(f"Stato emotivo forzato: {emotion} (intensità: {intensity})")
            
        except ValueError:
            self.logger.error(f"Emozione sconosciuta: {emotion}")
        except Exception as e:
            self.logger.error(f"Errore forzatura stato emotivo: {e}")
    
    async def cleanup(self):
        """Cleanup di tutti i sottosistemi."""
        try:
            await self.expression_manager.cleanup()
            self.logger.info("Behavioral States Manager cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore cleanup behavioral states: {e}")


# Test functions
async def test_behavioral_states():
    """Test completo del sistema behavioral states."""
    print("=== TESTING BEHAVIORAL STATES MANAGER ===")
    
    # Config con personalità custom
    config = {
        'behavior': {
            'personality_traits': {
                'curiosity_base': 0.9,      # Robot molto curioso
                'caution_threshold': 0.3,   # Poco cauto
                'social_attraction': 0.8,   # Molto sociale
                'energy_level': 0.9,        # Energia alta
                'risk_tolerance': 0.7       # Tolleranza rischio alta
            }
        },
        'hardware': {
            'led_matrix': {'brightness': 6}
        }
    }
    
    behavioral_manager = BehavioralStates(config, simulation_mode=True)
    
    # Inizializza
    success = await behavioral_manager.initialize()
    print(f"Inizializzazione: {'OK' if success else 'FAILED'}")
    
    if not success:
        return
    
    # Test scenari comportamentali
    test_scenarios = [
        {
            'name': 'Robot in esplorazione normale',
            'sensor_data': {
                'distance_cm': 120,
                'light_levels': [500, 480, 520, 510],
                'objects_detected': [],
                'motion_detected': False
            },
            'context': {'battery_level': 80},
            'duration': 5
        },
        
        {
            'name': 'Persona avvistata - comportamento sociale',
            'sensor_data': {
                'distance_cm': 80,
                'light_levels': [600, 580, 620, 610],
                'objects_detected': ['person'],
                'motion_detected': True
            },
            'context': {'battery_level': 75},
            'duration': 6
        },
        
        {
            'name': 'Ostacolo vicino - comportamento cauto',
            'sensor_data': {
                'distance_cm': 15,
                'light_levels': [500, 480, 520, 510],
                'objects_detected': ['wall'],
                'motion_detected': False
            },
            'context': {'battery_level': 70},
            'duration': 4
        },
        
        {
            'name': 'Batteria bassa - modalità riposo',
            'sensor_data': {
                'distance_cm': 150,
                'light_levels': [400, 380, 420, 410],
                'objects_detected': [],
                'motion_detected': False
            },
            'context': {'battery_level': 20},
            'duration': 5
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        for second in range(scenario['duration']):
            # Aggiorna comportamento
            current_state = await behavioral_manager.update_from_sensors(
                scenario['sensor_data'], 
                scenario['context']
            )
            
            # Ottieni parametri comportamentali
            behavior_params = await behavioral_manager.get_behavior_parameters()
            
            # Mostra stato ogni 2 secondi
            if second % 2 == 0:
                print(f"  {second+1}s: {current_state['emotion'].value} "
                      f"(intensità: {current_state['intensity']:.2f}) "
                      f"→ velocità: {behavior_params['speed_multiplier']:.2f}, "
                      f"esplorazione: {behavior_params['exploration_bias']:.2f}")
            
            await asyncio.sleep(0.2)  # Simula tempo reale
    
    # Test forzatura stato
    print(f"\n--- Test controllo diretto emozioni ---")
    await behavioral_manager.force_emotional_state('playful', intensity=0.9)
    await asyncio.sleep(1)
    
    behavior_params = await behavioral_manager.get_behavior_parameters()
    print(f"Stato forzato PLAYFUL → velocità: {behavior_params['speed_multiplier']:.2f}")
    
    # Statistiche finali
    print(f"\n=== STATISTICHE COMPORTAMENTALI FINALI ===")
    emotional_state = await behavioral_manager.get_emotional_state()
    
    print(f"Cambi di stato totali: {emotional_state['statistics']['state_changes']}")
    print(f"Update totali: {emotional_state['statistics']['total_updates']}")
    print(f"Stato più frequente: {emotional_state['statistics']['most_frequent_state']}")
    
    print(f"\nDistribuzione stati:")
    for emotion, count in emotional_state['statistics']['state_distribution'].items():
        if count > 0:
            percentage = (count / emotional_state['statistics']['total_updates']) * 100
            print(f"  {emotion}: {count} volte ({percentage:.1f}%)")
    
    print(f"\nPersonalità robot:")
    for trait, value in emotional_state['personality_traits'].items():
        print(f"  {trait}: {value:.2f}")
    
    await behavioral_manager.cleanup()
    print("\nTest completato! Il robot ha mostrato comportamenti emotivi complessi.")


if __name__ == "__main__":
    asyncio.run(test_behavioral_states())