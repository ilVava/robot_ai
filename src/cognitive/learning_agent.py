#!/usr/bin/env python3
"""
Learning Agent - Robot AI Cognitive System
==========================================

Sistema di apprendimento per rinforzo (Reinforcement Learning).
Il robot impara dai tentativi e errori come un bambino che scopre il mondo.

In parole semplici:
- Il robot prova azioni diverse in ogni situazione
- Se l'azione va bene = "premio" (impara a rifarla)
- Se l'azione va male = "punizione" (impara a evitarla)
- Col tempo diventa sempre più bravo a scegliere

Author: Andrea Vavassori
"""

import asyncio
import logging
import random
import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import statistics

class LearningAgent:
    """
    Agente di apprendimento per rinforzo.
    
    Usa una versione semplificata di Q-Learning:
    - Q-Table: mappa situazione → valore di ogni azione
    - Exploration vs Exploitation: bilanciamento tra provare cose nuove e usare ciò che sa
    - Experience Replay: impara dalle esperienze passate
    """
    
    def __init__(self, config: dict, experience_db=None):
        self.config = config.get('ai', {}).get('reinforcement_learning', {})
        self.logger = logging.getLogger(__name__)
        
        # Riferimento al database esperienze
        self.experience_db = experience_db
        
        # Parametri RL
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.epsilon_start = self.config.get('epsilon_start', 1.0)     # Esplorazione iniziale alta
        self.epsilon_end = self.config.get('epsilon_end', 0.01)       # Esplorazione finale bassa
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)  # Riduzione graduale
        self.gamma = 0.95  # Discount factor per reward futuri
        
        # Stato corrente
        self.current_epsilon = self.epsilon_start
        self.training_step = 0
        
        # Q-Table semplificata: dizionario situation_hash → {action: q_value}
        self.q_table = {}
        
        # Azioni possibili del robot
        self.actions = [
            'move_forward',
            'turn_left', 
            'turn_right',
            'stop',
            'explore',
            'approach_object',
            'avoid_obstacle'
        ]
        
        # Memory buffer per experience replay (ottimizzato)
        memory_size = self.config.get('memory_size', 1000)  # Ridotto da 10000 per RPi5
        self.memory_buffer = deque(maxlen=memory_size)
        self.batch_size = min(16, self.config.get('batch_size', 32))  # Batch più piccolo
        
        # Statistics di apprendimento
        self.stats = {
            'total_decisions': 0,
            'exploration_decisions': 0,
            'exploitation_decisions': 0,
            'avg_reward_recent': 0.0,
            'learning_episodes': 0,
            'best_cumulative_reward': 0.0,
            'current_epsilon': self.current_epsilon
        }
        
        # Buffer per calcolare media reward recenti
        self.recent_rewards = deque(maxlen=100)
        
        self.logger.info(f"Learning Agent inizializzato - LR: {self.learning_rate}, Epsilon: {self.current_epsilon:.3f}")
    
    def _hash_situation(self, situation: Dict[str, Any]) -> str:
        """
        Converte situazione in hash per uso come chiave Q-table.
        
        Args:
            situation: Dati sensori e contesto
            
        Returns:
            str: Hash rappresentativo della situazione
        """
        # Discretizza valori continui per creare stati gestibili
        discretized = {}
        
        for key, value in situation.items():
            if isinstance(value, (int, float)):
                if key == 'distance_cm':
                    # Discretizza distanza in range: very_close, close, medium, far
                    if value < 20:
                        discretized[key] = 'very_close'
                    elif value < 50:
                        discretized[key] = 'close'
                    elif value < 150:
                        discretized[key] = 'medium'
                    else:
                        discretized[key] = 'far'
                        
                elif key == 'light_level':
                    # Discretizza luce: dark, normal, bright
                    if value < 400:
                        discretized[key] = 'dark'
                    elif value < 700:
                        discretized[key] = 'normal'
                    else:
                        discretized[key] = 'bright'
                        
                elif key == 'battery_level':
                    # Discretizza batteria: low, medium, high
                    if value < 30:
                        discretized[key] = 'low'
                    elif value < 70:
                        discretized[key] = 'medium'
                    else:
                        discretized[key] = 'high'
                else:
                    # Altri valori numerici: discretizza in range
                    discretized[key] = f"range_{int(value // 50) * 50}"
            else:
                # Valori categorici rimangono uguali
                discretized[key] = value
        
        # Crea hash ordinato
        sorted_items = sorted(discretized.items())
        return json.dumps(sorted_items, sort_keys=True)
    
    async def choose_action(self, situation: Dict[str, Any], 
                          available_actions: List[str] = None) -> Tuple[str, bool]:
        """
        Sceglie l'azione migliore per la situazione corrente.
        
        Args:
            situation: Stato attuale sensori/contesto
            available_actions: Azioni disponibili (default: tutte)
            
        Returns:
            Tuple[str, bool]: (azione_scelta, was_exploration)
        """
        if available_actions is None:
            available_actions = self.actions.copy()
        
        situation_hash = self._hash_situation(situation)
        
        # Inizializza Q-values per situazione se mai vista prima
        if situation_hash not in self.q_table:
            self.q_table[situation_hash] = {action: 0.0 for action in self.actions}
        
        self.stats['total_decisions'] += 1
        
        # Epsilon-greedy: esplorazione vs sfruttamento
        is_exploration = random.random() < self.current_epsilon
        
        if is_exploration:
            # ESPLORAZIONE: prova azione casuale
            chosen_action = random.choice(available_actions)
            self.stats['exploration_decisions'] += 1
            self.logger.debug(f"Azione esplorazione: {chosen_action} (ε={self.current_epsilon:.3f})")
            
        else:
            # SFRUTTAMENTO: usa azione con Q-value più alto
            q_values = self.q_table[situation_hash]
            
            # Filtra solo azioni disponibili
            available_q_values = {action: q_values.get(action, 0.0) 
                                for action in available_actions}
            
            # Scegli azione con Q-value massimo
            chosen_action = max(available_q_values, key=available_q_values.get)
            self.stats['exploitation_decisions'] += 1
            
            best_q = available_q_values[chosen_action]
            self.logger.debug(f"Azione sfruttamento: {chosen_action} (Q={best_q:.3f})")
        
        return chosen_action, is_exploration
    
    async def learn_from_experience(self, 
                                  situation: Dict[str, Any],
                                  action: str,
                                  reward: float,
                                  next_situation: Dict[str, Any] = None,
                                  done: bool = False) -> bool:
        """
        Impara da un'esperienza (aggiorna Q-values).
        
        Args:
            situation: Situazione iniziale
            action: Azione eseguita
            reward: Reward ricevuto (-1.0 to +1.0)
            next_situation: Situazione risultante (opzionale)
            done: True se episodio terminato
            
        Returns:
            bool: True se learning riuscito
        """
        try:
            situation_hash = self._hash_situation(situation)
            
            # Assicura che situazione sia nella Q-table
            if situation_hash not in self.q_table:
                self.q_table[situation_hash] = {action: 0.0 for action in self.actions}
            
            # Q-Learning update formula:
            # Q(s,a) = Q(s,a) + lr * [reward + gamma * max(Q(s',a')) - Q(s,a)]
            
            current_q = self.q_table[situation_hash].get(action, 0.0)
            
            if next_situation and not done:
                # Calcola max Q-value per situazione successiva
                next_situation_hash = self._hash_situation(next_situation)
                if next_situation_hash in self.q_table:
                    max_next_q = max(self.q_table[next_situation_hash].values())
                else:
                    max_next_q = 0.0
                
                # Q-learning update con reward futuro
                target_q = reward + self.gamma * max_next_q
            else:
                # Episodio terminato o situazione finale
                target_q = reward
            
            # Aggiorna Q-value
            updated_q = current_q + self.learning_rate * (target_q - current_q)
            self.q_table[situation_hash][action] = updated_q
            
            # Aggiungi a memory buffer per experience replay
            experience = {
                'situation': situation,
                'action': action,
                'reward': reward,
                'next_situation': next_situation,
                'done': done,
                'timestamp': time.time()
            }
            self.memory_buffer.append(experience)
            
            # Aggiorna statistics
            self.recent_rewards.append(reward)
            if len(self.recent_rewards) > 0:
                self.stats['avg_reward_recent'] = statistics.mean(self.recent_rewards)
            
            self.stats['learning_episodes'] += 1
            
            # Riduce epsilon (meno esplorazione nel tempo)
            self.current_epsilon = max(self.epsilon_end, 
                                     self.current_epsilon * self.epsilon_decay)
            self.stats['current_epsilon'] = self.current_epsilon
            
            self.training_step += 1
            
            self.logger.debug(f"Learning: {action} Q: {current_q:.3f} → {updated_q:.3f} (reward: {reward})")
            
            # Experience replay periodico per rinforzare apprendimento
            if len(self.memory_buffer) >= self.batch_size and self.training_step % 10 == 0:
                await self._experience_replay()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore learning da esperienza: {e}")
            return False
    
    async def _experience_replay(self):
        """Riallena su batch casuale di esperienze passate."""
        try:
            # Seleziona batch casuale dalla memoria
            batch_size = min(self.batch_size, len(self.memory_buffer))
            batch = random.sample(list(self.memory_buffer), batch_size)
            
            for experience in batch:
                # Replica manualmente Q-learning update SENZA chiamare learn_from_experience
                # per evitare recursion infinita
                situation = experience['situation']
                action = experience['action']
                reward = experience['reward']
                next_situation = experience.get('next_situation')
                done = experience.get('done', False)
                
                situation_hash = self._hash_situation(situation)
                
                # Assicura che situazione sia nella Q-table
                if situation_hash not in self.q_table:
                    self.q_table[situation_hash] = {act: 0.0 for act in self.actions}
                
                # Q-Learning update diretto (senza recursion)
                current_q = self.q_table[situation_hash].get(action, 0.0)
                
                if next_situation and not done:
                    next_situation_hash = self._hash_situation(next_situation)
                    if next_situation_hash in self.q_table:
                        max_next_q = max(self.q_table[next_situation_hash].values())
                    else:
                        max_next_q = 0.0
                    target_q = reward + self.gamma * max_next_q
                else:
                    target_q = reward
                
                # Update con learning rate ridotto per replay
                reduced_lr = self.learning_rate * 0.3  # LR molto ridotto per stabilità
                updated_q = current_q + reduced_lr * (target_q - current_q)
                self.q_table[situation_hash][action] = updated_q
            
            self.logger.debug(f"Experience replay completato: {batch_size} esperienze")
            
        except Exception as e:
            self.logger.error(f"Errore experience replay: {e}")
    
    async def get_action_recommendations(self, situation: Dict[str, Any], 
                                       top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Ottieni raccomandazioni azioni ordinate per Q-value.
        
        Args:
            situation: Situazione corrente
            top_k: Numero raccomandazioni da restituire
            
        Returns:
            List[Dict]: Lista azioni con Q-values e confidenza
        """
        situation_hash = self._hash_situation(situation)
        
        if situation_hash not in self.q_table:
            # Situazione mai vista: raccomandazioni neutre
            return [
                {
                    'action': action,
                    'q_value': 0.0,
                    'confidence': 0.0,
                    'recommendation_reason': 'unexplored_situation'
                }
                for action in self.actions[:top_k]
            ]
        
        # Ordina azioni per Q-value
        q_values = self.q_table[situation_hash]
        sorted_actions = sorted(q_values.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        max_q = max(q_values.values()) if q_values.values() else 1.0
        
        for action, q_value in sorted_actions[:top_k]:
            # Calcola confidenza basata su Q-value relativo
            confidence = (q_value / max_q) if max_q > 0 else 0.0
            confidence = max(0.0, min(1.0, confidence))  # Clamp 0-1
            
            # Determina ragione raccomandazione
            if q_value > 0.5:
                reason = 'high_success_rate'
            elif q_value > 0.0:
                reason = 'positive_experience'
            elif q_value == 0.0:
                reason = 'no_experience'
            else:
                reason = 'negative_experience'
            
            recommendations.append({
                'action': action,
                'q_value': q_value,
                'confidence': confidence,
                'recommendation_reason': reason
            })
        
        return recommendations
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """Ottieni statistiche complete di apprendimento."""
        # Calcola diverse metriche
        exploration_rate = (self.stats['exploration_decisions'] / 
                          max(1, self.stats['total_decisions']))
        
        # Analizza trend Q-values
        q_value_stats = self._analyze_q_table()
        
        return {
            'timestamp': time.time(),
            'training_step': self.training_step,
            'total_decisions': self.stats['total_decisions'],
            'exploration_rate': exploration_rate,
            'current_epsilon': self.current_epsilon,
            'avg_reward_recent': self.stats['avg_reward_recent'],
            'learning_episodes': self.stats['learning_episodes'],
            'q_table_size': len(self.q_table),
            'memory_buffer_size': len(self.memory_buffer),
            'q_value_statistics': q_value_stats
        }
    
    def _analyze_q_table(self) -> Dict[str, Any]:
        """Analizza Q-table per insights."""
        if not self.q_table:
            return {}
        
        all_q_values = []
        action_averages = {action: [] for action in self.actions}
        
        for situation_q in self.q_table.values():
            for action, q_value in situation_q.items():
                all_q_values.append(q_value)
                if action in action_averages:
                    action_averages[action].append(q_value)
        
        # Calcola statistiche generali
        stats = {
            'total_q_values': len(all_q_values),
            'avg_q_value': statistics.mean(all_q_values) if all_q_values else 0.0,
            'max_q_value': max(all_q_values) if all_q_values else 0.0,
            'min_q_value': min(all_q_values) if all_q_values else 0.0,
            'std_q_value': statistics.stdev(all_q_values) if len(all_q_values) > 1 else 0.0
        }
        
        # Calcola medie per azione
        stats['action_averages'] = {}
        for action, values in action_averages.items():
            if values:
                stats['action_averages'][action] = {
                    'avg': statistics.mean(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return stats
    
    async def save_model(self, filename: str = None) -> bool:
        """Salva modello (Q-table) su file."""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"learning_model_{timestamp}.json"
            
            models_dir = Path("data/models")
            models_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = models_dir / filename
            
            model_data = {
                'q_table': self.q_table,
                'training_step': self.training_step,
                'current_epsilon': self.current_epsilon,
                'stats': self.stats,
                'config': self.config,
                'actions': self.actions,
                'saved_timestamp': time.time()
            }
            
            with open(filepath, 'w') as f:
                json.dump(model_data, f, indent=2)
            
            self.logger.info(f"Modello salvato: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio modello: {e}")
            return False
    
    async def load_model(self, filename: str) -> bool:
        """Carica modello precedente."""
        try:
            filepath = Path("data/models") / filename
            
            if not filepath.exists():
                self.logger.error(f"File modello non trovato: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            self.q_table = model_data.get('q_table', {})
            self.training_step = model_data.get('training_step', 0)
            self.current_epsilon = model_data.get('current_epsilon', self.epsilon_start)
            
            if 'stats' in model_data:
                self.stats.update(model_data['stats'])
            
            self.logger.info(f"Modello caricato: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore caricamento modello: {e}")
            return False


# Testing functions
async def test_learning_agent():
    """Test del sistema di apprendimento per rinforzo."""
    print("=== TESTING REINFORCEMENT LEARNING AGENT ===")
    
    # Config di test
    config = {
        'ai': {
            'reinforcement_learning': {
                'learning_rate': 0.1,
                'epsilon_start': 1.0,
                'epsilon_end': 0.1,
                'epsilon_decay': 0.99,
                'memory_size': 1000,
                'batch_size': 16
            }
        }
    }
    
    agent = LearningAgent(config)
    
    print("Simulando 200 episodi di apprendimento...")
    
    # Simula episodi di apprendimento
    for episode in range(200):
        # Situazione iniziale casuale
        situation = {
            'distance_cm': random.uniform(10, 200),
            'light_level': random.uniform(300, 800),
            'battery_level': random.uniform(20, 100),
            'object_detected': random.choice(['none', 'person', 'chair', 'wall'])
        }
        
        # Agent sceglie azione
        action, was_exploration = await agent.choose_action(situation)
        
        # Simula reward basato su "logica del buon senso"
        reward = 0.0
        
        if situation['distance_cm'] < 30:
            # Vicino a ostacolo
            if action in ['stop', 'turn_left', 'turn_right']:
                reward = 1.0  # Bene, evita collisione
            elif action == 'move_forward':
                reward = -1.0  # Male, rischio collisione
            else:
                reward = 0.0
                
        elif situation['distance_cm'] > 100:
            # Spazio libero
            if action == 'move_forward':
                reward = 0.8  # Bene, esplora
            elif action == 'explore':
                reward = 0.6  # Discreto
            else:
                reward = 0.2
                
        else:
            # Distanza media
            if action in ['move_forward', 'explore']:
                reward = 0.5
            else:
                reward = 0.2
        
        # Bonus per oggetti interessanti
        if situation['object_detected'] == 'person' and action == 'approach_object':
            reward += 0.3
        
        # Penalità batteria bassa senza azione appropriata
        if situation['battery_level'] < 30 and action != 'stop':
            reward -= 0.2
        
        # Agent impara dall'esperienza
        await agent.learn_from_experience(situation, action, reward, done=True)
        
        # Mostra progresso ogni 50 episodi
        if (episode + 1) % 50 == 0:
            stats = await agent.get_learning_statistics()
            print(f"  Episodio {episode + 1}: "
                  f"ε={stats['current_epsilon']:.3f}, "
                  f"reward_avg={stats['avg_reward_recent']:.3f}, "
                  f"exploration_rate={stats['exploration_rate']:.3f}")
    
    # Test raccomandazioni finali
    print("\n=== TEST RACCOMANDAZIONI FINALI ===")
    
    test_situations = [
        {
            'distance_cm': 15,
            'light_level': 500,
            'battery_level': 80,
            'object_detected': 'wall'
        },
        {
            'distance_cm': 150,
            'light_level': 600,
            'battery_level': 60,
            'object_detected': 'none'
        },
        {
            'distance_cm': 80,
            'light_level': 400,
            'battery_level': 25,
            'object_detected': 'person'
        }
    ]
    
    for i, test_situation in enumerate(test_situations, 1):
        print(f"\nSituazione {i}: {test_situation}")
        recommendations = await agent.get_action_recommendations(test_situation, 3)
        
        print("  Raccomandazioni:")
        for rec in recommendations:
            print(f"    {rec['action']}: Q={rec['q_value']:.3f}, "
                  f"confidence={rec['confidence']:.3f} ({rec['recommendation_reason']})")
    
    # Statistiche finali
    final_stats = await agent.get_learning_statistics()
    print(f"\n=== STATISTICHE FINALI ===")
    print(f"Decisioni totali: {final_stats['total_decisions']}")
    print(f"Q-table size: {final_stats['q_table_size']} situazioni")
    print(f"Reward medio recente: {final_stats['avg_reward_recent']:.3f}")
    print(f"Tasso esplorazione finale: {final_stats['exploration_rate']:.3f}")
    
    # Salva modello
    await agent.save_model("test_model.json")
    print("Modello salvato per utilizzi futuri")
    
    print("\nTest completato! Il robot ha imparato a scegliere azioni migliori.")


if __name__ == "__main__":
    asyncio.run(test_learning_agent())