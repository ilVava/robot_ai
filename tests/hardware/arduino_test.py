#!/usr/bin/env python3
"""
Simple Arduino Test - Direct Serial Communication

Test diretto della comunicazione seriale con Arduino
per verificare se lo sketch è caricato e funzionante.
"""

import serial
import time

def test_arduino():
    try:
        print("🔌 Opening serial connection to Arduino...")
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2.0)

        # Wait for Arduino boot
        print("⏳ Waiting for Arduino boot...")
        time.sleep(3.0)

        # Clear any existing data
        ser.flushInput()
        ser.flushOutput()

        print("📡 Testing basic communication...")

        # Test 1: Send PING
        print("Sending: PING")
        ser.write(b"PING\n")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Received: {response}")
        else:
            print("❌ No response to PING")

        # Test 2: Send STATUS
        print("Sending: STATUS")
        ser.write(b"STATUS\n")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Received: {response}")
        else:
            print("❌ No response to STATUS")

        # Test 3: Send LED_PATTERN:0
        print("Sending: LED_PATTERN:0")
        ser.write(b"LED_PATTERN:0\n")
        time.sleep(0.5)

        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Received: {response}")
        else:
            print("❌ No response to LED_PATTERN:0")

        # Test 3: Read any startup messages
        print("Listening for any messages...")
        for i in range(5):
            if ser.in_waiting > 0:
                msg = ser.readline().decode('utf-8').strip()
                print(f"Message: {msg}")
            time.sleep(0.5)

        ser.close()
        print("✅ Test completed")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_arduino()