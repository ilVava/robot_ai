/*
 * Robot AI - Arduino Controller per Keyestudio Caterpillar V3
 * ===========================================================
 *
 * Sketch per comunicazione seriale tra Raspberry Pi 5 e Arduino Uno
 * Controlla sensori e attuatori del kit Keyestudio Caterpillar V3
 *
 * Hardware Connections (KS0555 Official):
 * - Ultrasonico HC-SR04: Trig=12, Echo=13
 * - Fotoresistori: A0,A1,A2,A3
 * - Motori: Left(PWM=6,Ctrl=4), Right(PWM=5,Ctrl=2)
 * - Servo Ultrasonico: Pin=10
 * - LED Matrix: Data=10, Clock=11, CS=13
 *
 * Serial Protocol: 115200 baud
 * Commands: READ_SENSORS, MOVE_FORWARD, MOVE_BACKWARD, TURN_LEFT, TURN_RIGHT, STOP, SET_SPEED, LED_PATTERN, SERVO
 *
 * Author: Robot AI Project
 */

// Hardware Pin Definitions - Keyestudio KS0555 Official Mapping
const int TRIG_PIN = 12;        // Ultrasonic Trigger
const int ECHO_PIN = 13;        // Ultrasonic Echo

// Photoresistors (Light Sensors)
const int PHOTO_PINS[4] = {A0, A1, A2, A3};

// Motor Control - Keyestudio KS0555 Official Pin Mapping
const int LEFT_MOTOR_PWM = 6;   // ML_PWM (Left Motor Speed)
const int LEFT_MOTOR_CTRL = 4;  // ML_Ctrl (Left Motor Direction)

const int RIGHT_MOTOR_PWM = 5;  // MR_PWM (Right Motor Speed)
const int RIGHT_MOTOR_CTRL = 2; // MR_Ctrl (Right Motor Direction)

// Servo for ultrasonic pan/tilt
const int SERVO_PIN = 10;

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
  pinMode(LEFT_MOTOR_CTRL, OUTPUT);

  pinMode(RIGHT_MOTOR_PWM, OUTPUT);
  pinMode(RIGHT_MOTOR_CTRL, OUTPUT);

  // Setup servo pin
  pinMode(SERVO_PIN, OUTPUT);

  // Setup LED pins
  pinMode(LED_DATA_PIN, OUTPUT);
  pinMode(LED_CLOCK_PIN, OUTPUT);
  pinMode(LED_CS_PIN, OUTPUT);

  // Initialize all systems
  stopMotors();
  setLedPattern(0); // LEDs off
  setServoAngle(90); // Center servo position

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
  else if (cmd.startsWith("SERVO:")) {
    int angle = cmd.substring(6).toInt();
    setServoAngle(angle);
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
  // Forward: HIGH direction control + PWM speed (based on KS0555 tutorial)
  digitalWrite(LEFT_MOTOR_CTRL, HIGH);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  digitalWrite(RIGHT_MOTOR_CTRL, HIGH);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:MOVE_FORWARD:SPEED:" + String(currentSpeed));
}

void moveBackward() {
  // Backward: LOW direction control + high PWM speed (based on KS0555 tutorial)
  digitalWrite(LEFT_MOTOR_CTRL, LOW);
  analogWrite(LEFT_MOTOR_PWM, 200);  // Higher PWM for reverse direction

  digitalWrite(RIGHT_MOTOR_CTRL, LOW);
  analogWrite(RIGHT_MOTOR_PWM, 200);

  Serial.println("ACTION:MOVE_BACKWARD:SPEED:200");
}

void turnLeft() {
  // Turn left: left motor reverse, right motor forward (KS0555 pattern)
  digitalWrite(LEFT_MOTOR_CTRL, LOW);
  analogWrite(LEFT_MOTOR_PWM, 200);

  digitalWrite(RIGHT_MOTOR_CTRL, HIGH);
  analogWrite(RIGHT_MOTOR_PWM, currentSpeed);

  Serial.println("ACTION:TURN_LEFT:SPEED:" + String(currentSpeed));
}

void turnRight() {
  // Turn right: left motor forward, right motor reverse (KS0555 pattern)
  digitalWrite(LEFT_MOTOR_CTRL, HIGH);
  analogWrite(LEFT_MOTOR_PWM, currentSpeed);

  digitalWrite(RIGHT_MOTOR_CTRL, LOW);
  analogWrite(RIGHT_MOTOR_PWM, 200);

  Serial.println("ACTION:TURN_RIGHT:SPEED:" + String(currentSpeed));
}

void stopMotors() {
  // Stop both motors (KS0555 pattern)
  analogWrite(LEFT_MOTOR_PWM, 0);
  analogWrite(RIGHT_MOTOR_PWM, 0);

  digitalWrite(LEFT_MOTOR_CTRL, LOW);
  digitalWrite(RIGHT_MOTOR_CTRL, LOW);

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

// Servo control function (from KS0555 tutorial)
void setServoAngle(int angle) {
  angle = constrain(angle, 0, 180);  // Ensure valid servo range

  for (int i = 0; i < 5; i++) {
    int pulsewidth = angle * 11 + 500;  // Calculate pulse width
    digitalWrite(SERVO_PIN, HIGH);
    delayMicroseconds(pulsewidth);
    digitalWrite(SERVO_PIN, LOW);
    delay(20 - pulsewidth / 1000);  // Complete 20ms cycle
  }

  Serial.println("ACTION:SERVO_ANGLE:" + String(angle));
}

int getFreeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}