/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 6.2
  Ultrasonic LED
  http://www.keyestudio.com
*/
int trigPin = 12;    // Trig is connected to 12
int echoPin = 13;    // Echo is connected to 13
int LED = 9;
long duration, cm, inches;
void setup() {
  //start serial port
  Serial.begin (9600);//set baud rate to 9600
  //define input and output
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(LED, OUTPUT);
}
void loop() {
  //Pre-given a short low pulse to ensure a clean high pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);//Give at least 10us high level trigger
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // The duration of the high level is the time from the launch to the return of the ultrasonic wave
  duration = pulseIn(echoPin, HIGH);
  // convert to distance
  cm = (duration / 2) / 29.1;   // convert to centimeters
  inches = (duration / 2) / 74; // convert to inches
  //serial port prints out
  Serial.print(inches);
  Serial.print("in, ");
  Serial.print(cm);
  Serial.print("cm");
  Serial.println();
  if (cm >= 2 && cm <= 10) {
    digitalWrite(LED, HIGH);//turn on LED
  } else {
    digitalWrite(LED, LOW); //turn off LED
  }
  delay(50);
}
//****************************************************************
