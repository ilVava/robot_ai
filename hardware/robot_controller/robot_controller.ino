/*
 * Robot AI - Arduino Controller per Keyestudio Caterpillar V3
 * ===========================================================
 *
 * Sketch per comunicazione seriale tra Raspberry Pi 5 e Arduino Uno
 * Controlla sensori e attuatori del kit Keyestudio Caterpillar V3
 *
 * Hardware Connections:
 * - Ultrasonico HC-SR04: Trig=7, Echo=8
 * - Fotoresistori: A0,A1,A2,A3
 * - Motori: PWM=3,5,6,9 Direction=2,4,7,12
 * - LED Matrix: Data=10, Clock=11, CS=13
 *
 * Serial Protocol: 115200 baud
 * Commands: READ_SENSORS, MOVE_FORWARD, MOVE_BACKWARD, TURN_LEFT, TURN_RIGHT, STOP, SET_SPEED, LED_PATTERN
 *
 * Author: Robot AI Project
 */

// Hardware Pin Definitions
const int TRIG_PIN = 7;
const int ECHO_PIN = 8;

// Photoresistors (Light Sensors)
const int PHOTO_PINS[4] = {A0, A1, A2, A3};

// Motor Control - Keyestudio configuration
const int LEFT_MOTOR_PWM = 5;
const int LEFT_MOTOR_DIR1 = 4;
const int LEFT_MOTOR_DIR2 = 2;

const int RIGHT_MOTOR_PWM = 6;
const int RIGHT_MOTOR_DIR1 = 7;
const int RIGHT_MOTOR_DIR2 = 8;

// LED Matrix
const int LED_DATA_PIN = 10;
const int LED_CLOCK_PIN = 11;
const int LED_CS_PIN = 13;

// Motor control variables
int currentSpeed = 80;  // Default speed (0-255)

void setup() {
  // Initialize serial communication at 115200 baud
  Serial.begin(115200);

  // Setup ultrasonic sensor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Setup motor pins
  pinMode(LEFT_MOTOR_PWM, OUTPUT);
  pinMode(LEFT_MOTOR_DIR1, OUTPUT);
  pinMode(LEFT_MOTOR_DIR2, OUTPUT);

  pinMode(RIGHT_MOTOR_PWM, OUTPUT);
  pinMode(RIGHT_MOTOR_DIR1, OUTPUT);
  pinMode(RIGHT_MOTOR_DIR2, OUTPUT);

  // Setup LED pins
  pinMode(LED_DATA_PIN, OUTPUT);
  pinMode(LED_CLOCK_PIN, OUTPUT);
  pinMode(LED_CS_PIN, OUTPUT);

  // Initialize all systems
  stopMotors();
  setLedPattern(0); // LEDs off

  // Send ready signal to Raspberry Pi
  Serial.println("ARDUINO_READY");
  Serial.flush();

  delay(100);
}

void loop() {
  // Check for incoming serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.length() > 0) {
      processCommand(command);
    }
  }

  // Small delay to prevent overwhelming the serial port
  delay(20);
}

void processCommand(String cmd) {
  // Convert command to uppercase for consistency
  cmd.toUpperCase();

  if (cmd == "READ_SENSORS") {
    readAllSensors();
  }
  else if (cmd == "MOVE_FORWARD") {
    moveForward();
  }
  else if (cmd == "MOVE_BACKWARD") {
    moveBackward();
  }
  else if (cmd == "TURN_LEFT") {
    turnLeft();
  }
  else if (cmd == "TURN_RIGHT") {
    turnRight();
  }
  else if (cmd == "STOP") {
    stopMotors();
  }
  else if (cmd.startsWith("SET_SPEED:")) {
    int speed = cmd.substring(10).toInt();
    setSpeed(speed);
  }
  else if (cmd.startsWith("LED_PATTERN:")) {
    int pattern = cmd.substring(12).toInt();
    setLedPattern(pattern);
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
  }
  else if (cmd == "STATUS") {
    printStatus();
  }
  else {
    Serial.println("ERROR:UNKNOWN_COMMAND:" + cmd);
  }
}

void readAllSensors() {
  // Read ultrasonic distance
  long distance = readUltrasonicDistance();

  // Read all photoresistors
  int lightValues[4];
  for(int i = 0; i < 4; i++) {
    lightValues[i] = analogRead(PHOTO_PINS[i]);
  }

  // Send sensor data in JSON format
  Serial.print("SENSORS:{\"distance\":");
  Serial.print(distance);
  Serial.print(",\"light\":[");

  for(int i = 0; i < 4; i++) {
    Serial.print(lightValues[i]);
    if(i < 3) Serial.print(",");
  }

  Serial.print("],\"timestamp\":");
  Serial.print(millis());
  Serial.println("}");
}

long readUltrasonicDistance() {
  // Clear trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  // Send 10µs trigger pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read echo pulse duration (timeout after 30ms = ~500cm)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  // Convert to distance in cm
  long distance = duration * 0.034 / 2;

  // Return max range if no echo or out of range
  if (distance <= 0 || distance > 400) {
    distance = 400;
  }

  return distance;
}

void moveForward() {
  // Left motor forward
  digitalWrite(LEFT_MOTOR_DIR1, HIGH);
  digitalWrite(LEFT_MOTOR_DIR2, LOW);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  // Right motor forward
  digitalWrite(RIGHT_MOTOR_DIR1, HIGH);
  digitalWrite(RIGHT_MOTOR_DIR2, LOW);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:MOVE_FORWARD:SPEED:" + String(currentSpeed));
}

void moveBackward() {
  // Left motor backward
  digitalWrite(LEFT_MOTOR_DIR1, LOW);
  digitalWrite(LEFT_MOTOR_DIR2, HIGH);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  // Right motor backward
  digitalWrite(RIGHT_MOTOR_DIR1, LOW);
  digitalWrite(RIGHT_MOTOR_DIR2, HIGH);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:MOVE_BACKWARD:SPEED:" + String(currentSpeed));
}

void turnLeft() {
  // Left motor backward, right motor forward
  digitalWrite(LEFT_MOTOR_DIR1, LOW);
  digitalWrite(LEFT_MOTOR_DIR2, HIGH);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  digitalWrite(RIGHT_MOTOR_DIR1, HIGH);
  digitalWrite(RIGHT_MOTOR_DIR2, LOW);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:TURN_LEFT:SPEED:" + String(currentSpeed));
}

void turnRight() {
  // Left motor forward, right motor backward
  digitalWrite(LEFT_MOTOR_DIR1, HIGH);
  digitalWrite(LEFT_MOTOR_DIR2, LOW);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  digitalWrite(RIGHT_MOTOR_DIR1, LOW);
  digitalWrite(RIGHT_MOTOR_DIR2, HIGH);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:TURN_RIGHT:SPEED:" + String(currentSpeed));
}

void stopMotors() {
  // Stop both motors
  analogWrite(LEFT_MOTOR_PWM, 0);
  analogWrite(RIGHT_MOTOR_PWM, 0);

  digitalWrite(LEFT_MOTOR_DIR1, LOW);
  digitalWrite(LEFT_MOTOR_DIR2, LOW);
  digitalWrite(RIGHT_MOTOR_DIR1, LOW);
  digitalWrite(RIGHT_MOTOR_DIR2, LOW);

  Serial.println("ACTION:STOP");
}

void setSpeed(int speed) {
  // Constrain speed to valid PWM range
  currentSpeed = constrain(speed, 0, 255);
  Serial.println("ACTION:SPEED_SET:" + String(currentSpeed));
}

void setLedPattern(int pattern) {
  // Simple LED patterns for now
  switch(pattern) {
    case 0:
      // All off
      digitalWrite(LED_DATA_PIN, LOW);
      Serial.println("ACTION:LED_PATTERN:OFF");
      break;

    case 1:
      // Blink once
      digitalWrite(LED_DATA_PIN, HIGH);
      delay(100);
      digitalWrite(LED_DATA_PIN, LOW);
      Serial.println("ACTION:LED_PATTERN:BLINK");
      break;

    case 2:
      // Fast pulse
      for(int i = 0; i < 3; i++) {
        digitalWrite(LED_DATA_PIN, HIGH);
        delay(50);
        digitalWrite(LED_DATA_PIN, LOW);
        delay(50);
      }
      Serial.println("ACTION:LED_PATTERN:PULSE");
      break;

    case 3:
      // Slow pulse
      for(int i = 0; i < 2; i++) {
        digitalWrite(LED_DATA_PIN, HIGH);
        delay(200);
        digitalWrite(LED_DATA_PIN, LOW);
        delay(200);
      }
      Serial.println("ACTION:LED_PATTERN:SLOW_PULSE");
      break;

    default:
      digitalWrite(LED_DATA_PIN, LOW);
      Serial.println("ACTION:LED_PATTERN:DEFAULT_OFF");
      break;
  }
}

void printStatus() {
  Serial.print("STATUS:{\"speed\":");
  Serial.print(currentSpeed);
  Serial.print(",\"uptime\":");
  Serial.print(millis());
  Serial.print(",\"free_memory\":");
  Serial.print(getFreeMemory());
  Serial.println("}");
}

int getFreeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}