# Troubleshooting - Robot AI

## 🔧 Problemi Hardware Comuni

### **Camera Non Funziona**
```bash
# Test camera
libcamera-still -o test.jpg
# Se fallisce:
sudo raspi-config  # Enable camera
sudo reboot
```

### **GPIO Permission Denied**
```bash
# Aggiungi user al gruppo gpio
sudo usermod -a -G gpio $USER
# Logout/login richiesto
```

### **Arduino Non Risponde**
```bash
# Check connessione seriale
ls /dev/ttyUSB* /dev/ttyACM*
sudo chmod 666 /dev/ttyUSB0
```

---

## 💻 Problemi Software Comuni

### **Import Error su RPi5**
```bash
# Spesso problema virtual environment
source robot_env/bin/activate
pip install --upgrade -r requirements.txt
```

### **OpenCV Import Fail**
```bash
# RPi5 specific fix
sudo apt install python3-opencv
# In venv:
pip uninstall opencv-python
pip install opencv-python-headless
```

### **Memory Error durante AI**
```python
# Riduci batch size in config
ai:
  reinforcement_learning:
    batch_size: 16  # Era 32
```

---

## ⚡ Performance Issues

### **Lag nella Decision Loop**
1. Check CPU usage: `htop`
2. Check memory: `free -h`  
3. Reduce perception frequency in config
4. Profile code: `python -m cProfile src/main.py`

### **Camera Lag**
```yaml
# In robot_config.yaml
camera:
  resolution: [320, 240]  # Riduci risoluzione
  framerate: 15           # Riduci FPS
```

---

## 🌐 Network/Communication

### **MQTT Connection Failed**
```bash
# Check broker
mosquitto_sub -h localhost -t test
# Start broker se necessario:
sudo systemctl start mosquitto
```

### **Web Dashboard Not Loading**
```bash
# Check port availability
sudo netstat -tulpn | grep :8080
# Kill process se necessario
```

---

## 📋 Quick Diagnostic Commands

```bash
# System health
make health

# Hardware test  
make hw-test

# Full system check
python3 src/main.py --debug --no-hardware

# GPIO status
gpio readall

# Camera test
libcamera-hello --qt-preview
```

---

*Aggiorna ogni volta che risolvi un problema ricorrente*