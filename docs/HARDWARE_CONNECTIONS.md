# Hardware Connections - Robot AI

## 🔌 Schema Collegamenti Completo

### **Arduino Uno ↔ Raspberry Pi 5**
```
Arduino Uno          Raspberry Pi 5
-----------          --------------
5V        ←→        5V (Pin 2)
GND       ←→        GND (Pin 6)  
D0 (RX)   ←→        GPIO14 (Pin 8) - UART TX
D1 (TX)   ←→        GPIO15 (Pin 10) - UART RX
```

### **Sensori → Arduino Uno**
```
HC-SR04 Ultrasonico:
- VCC  → Arduino 5V
- GND  → Arduino GND  
- Trig → Arduino Pin 7 (Digital)
- Echo → Arduino Pin 8 (Digital)

Fotoresistori x4 (con pull-down 10kΩ):
- LDR1 → Arduino A0 (Analog)
- LDR2 → Arduino A1 (Analog)
- LDR3 → Arduino A2 (Analog)
- LDR4 → Arduino A3 (Analog)
- Tutti con 5V e GND comuni

Motori Cingoli (via Motor Driver):
- Motor Driver → Arduino Pins 3,5,6,9 (PWM)
- Motor Driver → Arduino Pins 2,4,7,12 (Direction)

LED Matrix 8x8:
- Data → Arduino Pin 10 (Digital)
- Clock → Arduino Pin 11 (Digital)
- CS → Arduino Pin 12 (Digital)
```

### **Camera → Raspberry Pi 5**
```
RPi Camera Module v3:
- Connessione via flat cable 15-pin
- Porta CSI del Raspberry Pi 5
- Configurazione: sudo raspi-config → Enable Camera
```

---

## ⚡ Alimentazione

### **Sistema Doppia Alimentazione**
```
Robot Base (7.4V Li-ion 2200mAh):
├── Arduino Uno (via USB o Vin)
├── Sensori (5V/3.3V regolati)
├── Motori (7.4V diretti)
└── LED Matrix (5V regolato)

Raspberry Pi 5 (USB-C PD):
├── Power Bank 20.000mAh
├── 5V/3A minimum per RPi5  
├── Camera Module (alimentata da RPi)
└── Alimentazione separata per stabilità AI
```

**IMPORTANTE**: Alimentazioni separate per evitare interferenze tra motori e processamento AI.

---

## 🔧 Setup Procedure

### **Fase 1: Preparazione Arduino**
```arduino
// Sketch Arduino per comunicazione seriale
void setup() {
  Serial.begin(115200);
  // Setup pins sensori e attuatori
}

void loop() {
  // Leggi comandi da RPi via seriale
  // Invia dati sensori a RPi
}
```

### **Fase 2: Setup Raspberry Pi 5**
```bash
# Enable UART comunicazione
sudo raspi-config
# Advanced Options → Serial Port → Enable

# Enable Camera
sudo raspi-config  
# Interface Options → Camera → Enable

# Test comunicazione
echo "test" > /dev/serial0
cat /dev/serial0
```

### **Fase 3: Test Collegamenti**
```bash
# Test camera
libcamera-still -o test.jpg

# Test comunicazione Arduino
python3 -c "
import serial
ser = serial.Serial('/dev/serial0', 115200)
ser.write(b'READ_SENSORS\n')
print(ser.readline())
"
```

---

## 📋 Checklist Hardware

### **Componenti Necessari**
- [x] Keyestudio Caterpillar V3 Kit  
- [x] Raspberry Pi 5 8GB
- [x] RPi Camera Module v3
- [x] Power Bank USB-C 20.000mAh
- [x] MicroSD 128GB (per RPi OS)
- [ ] Cavi jumper maschio-femmina
- [ ] Breadboard (opzionale per prototyping)

### **Strumenti Setup**  
- [ ] Cacciaviti per assemblaggio
- [ ] Multimetro per test connessioni
- [ ] Computer con Arduino IDE
- [ ] SD Card reader per RPi setup

---

## 🚨 Safety & Troubleshooting

### **Precauzioni**
- **MAI collegare 5V Arduino direttamente a GPIO RPi** (solo 3.3V safe)
- **Usare level shifter** se necessario per comunicazione seriale
- **Verificare polarità** alimentazione prima di accendere
- **Ground comune** tra Arduino e RPi obbligatorio

### **Test Hardware**
```bash
# RPi GPIO test
gpio readall

# Arduino communication test  
make hw-test

# Camera test
libcamera-hello --qt-preview

# Complete system test
python3 src/main.py --debug --no-hardware  # Prima software
python3 src/main.py --debug                # Poi con hardware
```

### **Problemi Comuni**
- **Comunicazione seriale fallisce**: Check baud rate (115200) e GPIO enable
- **Camera non riconosciuta**: sudo raspi-config enable camera + reboot
- **Sensori letture errate**: Check alimentazione 5V stabile e ground
- **Motori non funzionano**: Verificare motor driver connections e PWM pins

---

## 📊 Pin Mapping Reference

### **Arduino Uno Pins**
```
Digital Pins:
├── 0,1    - Serial Communication (RX/TX)
├── 2,4,7,12 - Motor Direction Control
├── 3,5,6,9  - Motor PWM Control
├── 7,8    - Ultrasonic (Trig/Echo) 
└── 10,11,12 - LED Matrix (Data/Clock/CS)

Analog Pins:
├── A0 - Photoresistor 1
├── A1 - Photoresistor 2  
├── A2 - Photoresistor 3
└── A3 - Photoresistor 4
```

### **Raspberry Pi 5 GPIO**
```
Used Pins:
├── Pin 2  - 5V Power
├── Pin 6  - Ground
├── Pin 8  - GPIO14 (UART TX to Arduino)
├── Pin 10 - GPIO15 (UART RX from Arduino)
└── CSI Port - Camera Module
```

---

*Aggiorna questo file ogni volta che modifichi collegamenti hardware*