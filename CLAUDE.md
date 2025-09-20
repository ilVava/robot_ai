# CLAUDE - Robot AI Project Guidelines

## 🎯 Principi Fondamentali

### **SEMPRE SPIEGARE PRIMA DI AGIRE**
- Descrivi cosa stai per fare e perché
- L'utente è inesperto - usa linguaggio semplice
- Non assumere conoscenze pregresse

### **CODICE SEMPLICE ED EFFICACE**
- File non troppo pesanti - spezzare se necessario
- Commenti sintetici che spiegano il PERCHÉ delle scelte
- Evitare over-engineering

### **ARCHITETTURA DEL PROGETTO**
```
MacBook Air (16GB) → Sviluppo
    ↓
Raspberry Pi 5 (8GB) → AI Core
    ↓
Arduino (Keyestudio Kit) → Hardware Control
```

## 🏗️ Struttura Sistema

### **Core Components**
- **Perception**: Camera + Sensori → Dati ambiente
- **Cognitive**: AI Decision Making → Scelte intelligenti
- **Memory**: SLAM + Database → Ricordi e mappa
- **Emotion**: Stati comportamentali → Personalità
- **Action**: Motori + LED → Azioni fisiche

## 📝 Coding Guidelines

### **File Organization**
- Max 200-300 righe per file
- Separare logica in moduli specifici
- Un file = una responsabilità chiara

### **Comments Style**
```python
# Uso RL perché il robot deve imparare da solo
# Separo i sensori per elaborazione parallela
# Cache per evitare riprocessing inutile
```

### **Performance Priorities**
1. **Real-time responsiveness** (< 100ms decisions)
2. **Memory efficiency** (8GB limit RPi5)
3. **Battery optimization** (4-6h autonomy)

## 🚀 Development Status: **100% COMPLETATO** ✅

### **🤖 ROBOT AI È COMPLETAMENTE AUTONOMO!** *(14 Set 2024)*
- ✅ **Core AI System** (Phase 1-4): Personality, emotions, memory, learning
- ✅ **Hardware Integration** (Phase 6): RPi5 + Arduino + Physical Movement
- ✅ **Autonomous Operation**: Robot esplora indipendentemente il mondo reale
- 🔄 **Vision System** (Phase 5): Camera in ordinazione - enhancement opzionale

## ⚡ Quick Commands

```bash
# ROBOT OPERATIONS (Simplified)
python3 launch_robot.py autonomous  # Full autonomous exploration
python3 launch_robot.py test       # Hardware movement test
python3 launch_robot.py basic      # Basic autonomy test

# Development
make sim                            # Test AI logic simulation
make deploy                         # Deploy to RPi5

# Specific Tests
python3 tests/hardware/test_direct_movement.py
python3 deployment/launch_autonomous_robot.py

# Test KS0555 Pin Mapping
python3 tests/hardware/test_ks0555_pins.py  # Validate pin config

# Deploy
scp -r src config tests deployment andrea@raspberrypi.local:/home/andrea/
```

## 🔌 **CRITICAL Hardware Lessons** *(Mai più questi errori!)*

### **Arduino Serial Buffer Management**
```python
# SEMPRE prima di ogni nuovo controller:
self.arduino_serial.serial_connection.flushInput()
self.arduino_serial.serial_connection.flushOutput()
await asyncio.sleep(0.1)
```
**Why**: Arduino mantiene buffer, senza flush = command collision

### **AsyncIO Response Timing**
```python
# WRONG: await asyncio.sleep(0.01)   # 30% success
# RIGHT: await asyncio.sleep(0.001)  # 99% success
```

### **Hardware Initialization**
```
Motor → 1s delay → LED → Sensor → Safety (LAST)
```
**Never parallel**: Timing dependencies

### **Keyestudio KS0555 Pin Mapping**
```arduino
// OFFICIAL pin mapping from KS0555 tutorial
ULTRASONIC: Trig=12, Echo=13
MOTORS: Left(PWM=6,Ctrl=4), Right(PWM=5,Ctrl=2)
SERVO: Pin=10 (ultrasonico pan/tilt)
SENSORS: A0,A1,A2,A3 (photoresistors)
```
**Critical**: HIGH=forward, LOW=reverse for motors

### **Error Logging**
```python
# ALWAYS: logger.error(f"❌ Failed: {command} | Response: {response}")
```

### **RPi5 Setup**
```bash
sudo apt install python3-serial python3-opencv python3-yaml
sudo usermod -a -G dialout,gpio username
newgrp dialout
```

## 📋 Always Remember

1. **Explain → Code → Test** workflow
2. **Simple solutions** over complex ones
3. **Comment the WHY** not the WHAT
4. **MacBook dev → RPi5 deploy** pipeline
5. **DOCUMENTAZIONE SEMPRE AGGIORNATA**

## 📚 Documentation References

- **README.md**: Overview generale e stato progetto
- **docs/LESSONS.md**: Lezioni dettagliate e best practices
- **docs/DECISIONS.md**: Scelte tecniche e rationale
- **docs/HARDWARE_BEST_PRACTICES.md**: Pattern hardware validati

---
*IMPORTANTE: Aggiorna SEMPRE documentazione insieme al codice*