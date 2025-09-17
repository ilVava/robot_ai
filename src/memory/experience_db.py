#!/usr/bin/env python3
"""
Experience Database - Robot AI Memory System
============================================

Database SQLite per memorizzare tutte le esperienze del robot.
Come un "diario" che ricorda tutto quello che succede e impara dai pattern.

In parole semplici:
- Ogni azione del robot viene registrata
- Si ricorda se l'azione è andata bene o male
- Analizza i pattern per migliorare le decisioni future
- Come un bambino che impara dalle esperienze

Author: Andrea Vavassori
"""

import asyncio
import logging
import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import statistics

class ExperienceDatabase:
    """
    Database per memorizzare e analizzare esperienze del robot.
    
    Tabelle principali:
    - experiences: Situazione → Azione → Risultato
    - objects: Oggetti riconosciuti nel tempo
    - locations: Luoghi interessanti mappati
    - patterns: Pattern di comportamento scoperti
    """
    
    def __init__(self, config: dict, db_path: str = None):
        self.config = config.get('system', {}).get('database', {})
        self.logger = logging.getLogger(__name__)
        
        # Path database
        if db_path is None:
            db_path = self.config.get('path', 'data/robot_memory.db')
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connessione database
        self.connection = None
        self.is_initialized = False
        
        # Cache per performance (evita query ripetute)
        self.recent_experiences = []  # Ultimi 100 record
        self.pattern_cache = {}       # Pattern di comportamento
        self.cache_max_size = 100
        
        # Cache JSON parsing per evitare parsing ripetuto
        self.situation_cache = {}     # Hash → parsed situation
        
        # Batch operations per performance
        self.pending_experiences = []  # Buffer per batch insert
        self.batch_size = 10          # Inserisci ogni N esperienze
        
        # Statistics
        self.stats = {
            'total_experiences': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'unique_situations': 0,
            'learning_rate': 0.0,
            'last_update': 0.0
        }
        
        self.logger.info(f"ExperienceDatabase inizializzato - Path: {self.db_path}")
    
    async def initialize(self) -> bool:
        """
        Inizializza database e crea tabelle se necessario.
        
        Returns:
            bool: True se inizializzazione ok
        """
        try:
            # Connetti a SQLite
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Accesso per nome colonna
            
            # Crea tabelle
            await self._create_tables()
            
            # Carica cache iniziale
            await self._load_initial_cache()
            
            self.is_initialized = True
            self.logger.info("Database esperienze inizializzato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione database: {e}")
            return False
    
    async def _create_tables(self):
        """Crea struttura tabelle database."""
        cursor = self.connection.cursor()
        
        # Tabella principale esperienze
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                situation TEXT NOT NULL,           -- JSON: sensori, posizione, contesto
                action TEXT NOT NULL,              -- Azione intrapresa
                action_parameters TEXT,            -- JSON: parametri azione
                outcome TEXT NOT NULL,             -- success/failure/partial
                reward REAL DEFAULT 0.0,           -- Punteggio -1.0 to +1.0
                duration_ms INTEGER DEFAULT 0,     -- Durata azione in ms
                context TEXT,                      -- JSON: contesto aggiuntivo
                learned_from INTEGER DEFAULT 0     -- 1 se usato per training
            )
        """)
        
        # Indici per performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON experiences(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_situation ON experiences(situation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcome ON experiences(outcome)")
        
        # Tabella oggetti riconosciuti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                object_type TEXT NOT NULL,         -- persona, sedia, bottiglia, etc.
                confidence REAL NOT NULL,          -- 0.0-1.0 confidenza riconoscimento
                position_x REAL,                   -- Posizione nella mappa
                position_y REAL,
                properties TEXT,                   -- JSON: colore, dimensioni, etc.
                interaction_count INTEGER DEFAULT 0
            )
        """)
        
        # Tabella luoghi di interesse
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,                -- "angolo_cucina", "davanti_tv", etc.
                center_x REAL NOT NULL,
                center_y REAL NOT NULL,
                radius REAL DEFAULT 1.0,           -- Raggio area in metri
                visit_count INTEGER DEFAULT 0,
                avg_stay_time REAL DEFAULT 0.0,    -- Tempo medio di permanenza
                interest_score REAL DEFAULT 0.0,   -- Quanto è interessante 0-1
                last_visit REAL
            )
        """)
        
        # Tabella pattern comportamentali scoperti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,        -- "obstacle_avoidance", "exploration", etc.
                trigger_conditions TEXT NOT NULL,  -- JSON: quando si attiva
                action_sequence TEXT NOT NULL,     -- JSON: sequenza azioni
                success_rate REAL DEFAULT 0.0,    -- 0.0-1.0
                usage_count INTEGER DEFAULT 0,
                last_used REAL,
                created_timestamp REAL NOT NULL
            )
        """)
        
        self.connection.commit()
        self.logger.debug("Tabelle database create/verificate")
    
    async def _load_initial_cache(self):
        """Carica cache iniziale dal database."""
        cursor = self.connection.cursor()
        
        # Carica ultimi N esperienze in cache
        cursor.execute("""
            SELECT * FROM experiences 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (self.cache_max_size,))
        
        self.recent_experiences = [dict(row) for row in cursor.fetchall()]
        
        # Carica statistiche base
        cursor.execute("SELECT COUNT(*) as total FROM experiences")
        self.stats['total_experiences'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as success FROM experiences WHERE outcome = 'success'")
        self.stats['successful_actions'] = cursor.fetchone()['success']
        
        cursor.execute("SELECT COUNT(*) as failed FROM experiences WHERE outcome = 'failure'")
        self.stats['failed_actions'] = cursor.fetchone()['failed']
        
        # Calcola learning rate (miglioramento nel tempo)
        if self.stats['total_experiences'] > 0:
            self.stats['learning_rate'] = (
                self.stats['successful_actions'] / self.stats['total_experiences']
            )
        
        self.logger.debug(f"Cache caricata: {len(self.recent_experiences)} esperienze recenti")
    
    async def record_experience(self, 
                              situation: Dict[str, Any],
                              action: str,
                              action_parameters: Dict[str, Any] = None,
                              outcome: str = 'unknown',
                              reward: float = 0.0,
                              duration_ms: int = 0) -> int:
        """
        Registra una nuova esperienza nel database.
        
        Args:
            situation: Dati sensori e contesto quando è successo
            action: Nome dell'azione eseguita
            action_parameters: Parametri specifici dell'azione
            outcome: 'success', 'failure', 'partial', 'unknown'
            reward: Punteggio esperienza (-1.0 = male, +1.0 = ottimo)
            duration_ms: Quanto tempo ha preso l'azione
            
        Returns:
            int: ID dell'esperienza registrata
        """
        try:
            cursor = self.connection.cursor()
            timestamp = time.time()
            
            # Converti dict in JSON per storage
            situation_json = json.dumps(situation)
            parameters_json = json.dumps(action_parameters) if action_parameters else None
            
            # Aggiungi al buffer per batch insert
            experience_data = (timestamp, situation_json, action, parameters_json, outcome, reward, duration_ms)
            self.pending_experiences.append(experience_data)
            experience_id = len(self.recent_experiences) + len(self.pending_experiences)  # ID temporaneo
            
            # Batch insert quando buffer è pieno
            if len(self.pending_experiences) >= self.batch_size:
                await self._flush_pending_experiences()
            
            # Aggiorna cache
            new_experience = {
                'id': experience_id,
                'timestamp': timestamp,
                'situation': situation_json,
                'action': action,
                'outcome': outcome,
                'reward': reward,
                'duration_ms': duration_ms
            }
            
            self.recent_experiences.insert(0, new_experience)
            if len(self.recent_experiences) > self.cache_max_size:
                self.recent_experiences.pop()
            
            # Aggiorna statistics
            self.stats['total_experiences'] += 1
            if outcome == 'success':
                self.stats['successful_actions'] += 1
            elif outcome == 'failure':
                self.stats['failed_actions'] += 1
                
            self.stats['last_update'] = timestamp
            
            self.logger.debug(f"Esperienza registrata: {action} → {outcome} (reward: {reward})")
            return experience_id
            
        except Exception as e:
            self.logger.error(f"Errore registrazione esperienza: {e}")
            return -1
    
    async def _flush_pending_experiences(self):
        """Esegue batch insert delle esperienze in buffer."""
        if not self.pending_experiences:
            return
            
        try:
            cursor = self.connection.cursor()
            cursor.executemany("""
                INSERT INTO experiences 
                (timestamp, situation, action, action_parameters, outcome, reward, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, self.pending_experiences)
            
            self.connection.commit()
            self.logger.debug(f"Batch insert completato: {len(self.pending_experiences)} esperienze")
            self.pending_experiences.clear()
            
        except Exception as e:
            self.logger.error(f"Errore batch insert: {e}")
            # Ripristina buffer se errore
            pass
    
    async def find_similar_experiences(self, 
                                     current_situation: Dict[str, Any],
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Trova esperienze simili alla situazione corrente per imparare.
        
        Args:
            current_situation: Situazione attuale sensori/contesto
            limit: Max numero esperienze da restituire
            
        Returns:
            List[Dict]: Lista esperienze simili ordinate per rilevanza
        """
        try:
            # Per ora usa un matching semplice basato su chiavi comuni
            # In futuro si può implementare similarity più sofisticata
            
            similar_experiences = []
            
            # Prima cerca nella cache (più veloce)
            for exp in self.recent_experiences:
                similarity = self._calculate_similarity(current_situation, exp)
                if similarity > 0.3:  # Soglia minima similarità
                    exp['similarity_score'] = similarity
                    similar_experiences.append(exp)
            
            # Se non abbastanza nella cache, cerca nel database
            if len(similar_experiences) < limit:
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT * FROM experiences 
                    WHERE outcome IN ('success', 'failure')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit * 2,))  # Prendi più records per fare filtering
                
                db_experiences = [dict(row) for row in cursor.fetchall()]
                
                for exp in db_experiences:
                    if exp not in self.recent_experiences:  # Evita duplicati
                        similarity = self._calculate_similarity(current_situation, exp)
                        if similarity > 0.3:
                            exp['similarity_score'] = similarity
                            similar_experiences.append(exp)
            
            # Ordina per similarity score e limita risultati
            similar_experiences.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_experiences[:limit]
            
        except Exception as e:
            self.logger.error(f"Errore ricerca esperienze simili: {e}")
            return []
    
    def _calculate_similarity(self, situation1: Dict[str, Any], experience: Dict[str, Any]) -> float:
        """
        Calcola similarità tra situazione corrente e esperienza passata.
        
        Returns:
            float: Score similarità 0.0-1.0
        """
        try:
            # Parse JSON della situazione dell'esperienza con caching
            situation_str = experience.get('situation')
            if isinstance(situation_str, str):
                # Usa cache per evitare parsing ripetuto
                if situation_str in self.situation_cache:
                    exp_situation = self.situation_cache[situation_str]
                else:
                    exp_situation = json.loads(situation_str)
                    # Mantieni cache limitata
                    if len(self.situation_cache) < 1000:
                        self.situation_cache[situation_str] = exp_situation
            else:
                exp_situation = experience.get('situation', {})
            
            # Cerca chiavi comuni e calcola differenze
            common_keys = set(situation1.keys()) & set(exp_situation.keys())
            
            if not common_keys:
                return 0.0
            
            total_similarity = 0.0
            weight_sum = 0.0
            
            for key in common_keys:
                weight = 1.0  # Peso uguale per ora, in futuro si può raffinare
                
                val1 = situation1[key]
                val2 = exp_situation[key]
                
                # Calcola similarità based su tipo di dato
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Per numeri, usa differenza normalizzata
                    max_val = max(abs(val1), abs(val2), 1)  # Evita divisione per 0
                    diff = abs(val1 - val2) / max_val
                    similarity = max(0, 1.0 - diff)
                    
                elif isinstance(val1, str) and isinstance(val2, str):
                    # Per stringhe, match esatto o parziale
                    if val1 == val2:
                        similarity = 1.0
                    elif val1 in val2 or val2 in val1:
                        similarity = 0.7
                    else:
                        similarity = 0.0
                        
                else:
                    # Altri tipi, match esatto
                    similarity = 1.0 if val1 == val2 else 0.0
                
                total_similarity += similarity * weight
                weight_sum += weight
            
            return total_similarity / weight_sum if weight_sum > 0 else 0.0
            
        except Exception as e:
            self.logger.debug(f"Errore calcolo similarità: {e}")
            return 0.0
    
    async def get_success_rate_for_action(self, action: str, 
                                        situation_context: Dict[str, Any] = None) -> float:
        """
        Calcola tasso di successo per un'azione specifica.
        
        Args:
            action: Nome azione
            situation_context: Contesto situazionale opzionale
            
        Returns:
            float: Tasso successo 0.0-1.0
        """
        try:
            cursor = self.connection.cursor()
            
            if situation_context:
                # Cerca esperienze simili con quest'azione
                similar_experiences = await self.find_similar_experiences(situation_context)
                action_experiences = [exp for exp in similar_experiences if exp['action'] == action]
            else:
                # Tutte le esperienze con quest'azione
                cursor.execute("""
                    SELECT outcome FROM experiences 
                    WHERE action = ? AND outcome IN ('success', 'failure')
                """, (action,))
                
                results = cursor.fetchall()
                action_experiences = [{'outcome': row['outcome']} for row in results]
            
            if not action_experiences:
                return 0.5  # Nessun dato = probabilità neutra
            
            successes = sum(1 for exp in action_experiences if exp['outcome'] == 'success')
            return successes / len(action_experiences)
            
        except Exception as e:
            self.logger.error(f"Errore calcolo success rate: {e}")
            return 0.5
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """
        Analizza database per insights sui pattern di apprendimento.
        
        Returns:
            dict: Insights e statistiche di apprendimento
        """
        try:
            cursor = self.connection.cursor()
            
            insights = {
                'timestamp': time.time(),
                'total_experiences': self.stats['total_experiences'],
                'overall_success_rate': self.stats['learning_rate'],
                'most_successful_actions': [],
                'most_failed_actions': [],
                'learning_trends': {},
                'recent_performance': {}
            }
            
            # Azioni più riuscite
            cursor.execute("""
                SELECT action, 
                       COUNT(*) as total,
                       SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes,
                       CAST(SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate
                FROM experiences 
                WHERE outcome IN ('success', 'failure')
                GROUP BY action
                HAVING COUNT(*) >= 5
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            insights['most_successful_actions'] = [
                {
                    'action': row['action'],
                    'success_rate': row['success_rate'],
                    'total_attempts': row['total']
                }
                for row in cursor.fetchall()
            ]
            
            # Performance recente (ultima ora)
            one_hour_ago = time.time() - 3600
            cursor.execute("""
                SELECT COUNT(*) as recent_total,
                       SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as recent_successes
                FROM experiences 
                WHERE timestamp > ? AND outcome IN ('success', 'failure')
            """, (one_hour_ago,))
            
            recent_data = cursor.fetchone()
            if recent_data['recent_total'] > 0:
                insights['recent_performance'] = {
                    'total_actions': recent_data['recent_total'],
                    'success_rate': recent_data['recent_successes'] / recent_data['recent_total'],
                    'improvement': self._calculate_improvement_trend()
                }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Errore calcolo insights: {e}")
            return {}
    
    def _calculate_improvement_trend(self) -> float:
        """Calcola trend di miglioramento nel tempo."""
        if len(self.recent_experiences) < 10:
            return 0.0
        
        # Confronta prime 10 e ultime 10 esperienze recenti
        first_half = self.recent_experiences[:5]
        second_half = self.recent_experiences[5:10]
        
        first_success_rate = sum(1 for exp in first_half if exp['outcome'] == 'success') / len(first_half)
        second_success_rate = sum(1 for exp in second_half if exp['outcome'] == 'success') / len(second_half)
        
        return first_success_rate - second_success_rate  # Positivo = miglioramento
    
    async def cleanup(self):
        """Cleanup database connection."""
        try:
            # Flush pending experiences prima di chiudere
            await self._flush_pending_experiences()
            
            if self.connection:
                self.connection.close()
                self.logger.info("Database connessione chiusa")
        except Exception as e:
            self.logger.error(f"Errore cleanup database: {e}")


# Testing functions
async def test_experience_db():
    """Test del database esperienze."""
    import random
    
    # Setup database di test
    test_db_path = "data/test_experiences.db"
    
    # Rimuovi database precedente se esiste
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
    
    config = {
        'system': {
            'database': {
                'path': test_db_path
            }
        }
    }
    
    db = ExperienceDatabase(config)
    
    print("=== TESTING EXPERIENCE DATABASE ===")
    
    # Inizializza
    success = await db.initialize()
    print(f"Inizializzazione: {'OK' if success else 'FAILED'}")
    
    if not success:
        return
    
    # Simula 50 esperienze diverse
    actions = ['move_forward', 'turn_left', 'turn_right', 'stop', 'explore']
    outcomes = ['success', 'failure', 'partial']
    
    print("Registrando 50 esperienze simulate...")
    
    for i in range(50):
        situation = {
            'distance_cm': random.uniform(10, 200),
            'light_level': random.uniform(300, 800),
            'battery_level': random.uniform(20, 100),
            'time_of_day': random.choice(['morning', 'afternoon', 'evening'])
        }
        
        action = random.choice(actions)
        outcome = random.choice(outcomes)
        
        # Bias realistico: azioni più sensate hanno più successo
        if situation['distance_cm'] < 30 and action == 'stop':
            outcome = 'success'  # Fermarsi vicino a ostacoli = buono
        elif situation['distance_cm'] > 100 and action == 'move_forward':
            outcome = 'success'  # Avanzare in spazio libero = buono
        
        reward = 1.0 if outcome == 'success' else (-0.5 if outcome == 'failure' else 0.0)
        
        exp_id = await db.record_experience(situation, action, {}, outcome, reward, random.randint(100, 2000))
        
        if i % 10 == 0:
            print(f"  Registrate {i+1} esperienze...")
    
    # Test ricerca esperienze simili
    print("\nTestando ricerca esperienze simili...")
    
    test_situation = {
        'distance_cm': 25,
        'light_level': 500,
        'battery_level': 60,
        'time_of_day': 'afternoon'
    }
    
    similar = await db.find_similar_experiences(test_situation, 5)
    print(f"Trovate {len(similar)} esperienze simili alla situazione test")
    
    for exp in similar:
        print(f"  {exp['action']} → {exp['outcome']} (similarity: {exp['similarity_score']:.2f})")
    
    # Test success rate
    success_rate = await db.get_success_rate_for_action('stop', test_situation)
    print(f"\nSuccess rate 'stop' in situazione simile: {success_rate:.2f}")
    
    # Test insights
    insights = await db.get_learning_insights()
    print(f"\n=== LEARNING INSIGHTS ===")
    print(f"Esperienze totali: {insights['total_experiences']}")
    print(f"Success rate generale: {insights['overall_success_rate']:.2f}")
    print(f"Azioni più riuscite:")
    for action in insights['most_successful_actions']:
        print(f"  {action['action']}: {action['success_rate']:.2f} ({action['total_attempts']} tentativi)")
    
    await db.cleanup()
    print("\nTest completato!")


if __name__ == "__main__":
    asyncio.run(test_experience_db())