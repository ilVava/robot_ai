# Bug Tracking - Robot AI

## 🐛 Bug Risolti

*Formato: Data | Problema | Causa | Soluzione | File coinvolti*

### **[DATA] - Esempio Bug Template**
- **Problema**: Descrizione del bug
- **Causa**: Perché è successo  
- **Soluzione**: Come l'abbiamo risolto
- **File**: Lista file modificati
- **Test**: Come verificare che sia risolto

### **13 Set 2024 - Recursion Infinita in Learning Agent**
- **Problema**: Maximum recursion depth exceeded durante training RL
- **Causa**: Experience replay richiamava learn_from_experience → loop infinito
- **Soluzione**: Experience replay ora fa Q-learning update diretto senza recursion
- **File**: src/cognitive/learning_agent.py:280-323
- **Test**: 200 episodi completati con successo, reward medio 0.366

### **13 Set 2024 - Variable Not Initialized in Behavioral States**
- **Problema**: AttributeError: 'BehavioralStates' object has no attribute 'behavior_config'
- **Causa**: behavior_config usato in _load_personality_traits() prima dell'inizializzazione
- **Soluzione**: Spostato self.behavior_config prima di personality_traits
- **File**: src/emotion/behavioral_states.py:48-69
- **Test**: Sistema comportamentale completo funziona, 20 updates, 2 stati emotivi

---

## 🔍 Bug Attivi

*Lista bug noti non ancora risolti*

---

## 📋 Pattern Ricorrenti

*Bug che si ripetono spesso e loro soluzioni standard*

---

*Aggiorna questo file ogni volta che risolvi un bug*