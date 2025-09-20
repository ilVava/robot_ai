/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 12
  Ultrasonic avoid tank
  http://www.keyestudio.com
*/
#define servoPin 10  //The pin of servo
int a, a1, a2;
#define ML_Ctrl 4  //Define the direction control pin of the left motor
#define ML_PWM 6   //Define the PWM control pin of the left motor
#define MR_Ctrl 2  //Define the direction control pin of the right motor
#define MR_PWM 5   //Define the PWM control pin of the right motor
#define Trig 12
#define Echo 13
float distance;

void setup() {
  Serial.begin(9600);
  pinMode(servoPin, OUTPUT);
  pinMode(Trig, OUTPUT);
  pinMode(Echo, INPUT);
  pinMode(ML_Ctrl, OUTPUT);
  pinMode(ML_PWM, OUTPUT);
  pinMode(MR_Ctrl, OUTPUT);
  pinMode(MR_PWM, OUTPUT);
  procedure(90); //Set the angle of the servo to 90°
  delay(500); //delay in 500ms
}
void loop() {
  a = checkdistance();  //Assign the distance to the front detected by ultrasonic sensor to the variable a

  if (a < 20) {//When the distance to the front is less than 20cm
    Car_Stop();  //The robot stops
    delay(500); //delay in 500ms
    procedure(180);  //Ultrasonic pan-tilt turns left
    delay(500); //delay in 500ms
    a1 = checkdistance();  //Assign the distance to the left detected by ultrasonic sensor to the variable a1
    delay(100); //read value
    procedure(0); //Ultrasonic pan-tilt turns right
    delay(500); //delay in 500ms
    a2 = checkdistance(); //Assign the distance to the right detected by ultrasonic sensor to the variable a2
    delay(100); //read value
    
    procedure(90);  //Back to 90°
    delay(500);
    if (a1 > a2) { //When the distance to the left is bigger than to the right
      Car_left();  //The robot turns left
      delay(700);  //turn left700ms
    } else {
      Car_right(); //It turns left for 700ms
      delay(700);
    }
  } 
  else { //When the distance to the front is >=20c，the robot moves forward
    Car_front(); //go front
  }

}

void Car_front()
{
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, 55);
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, 55);
}
void Car_back()
{
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, 200);
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, 200);
}
void Car_left()
{
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, 55);
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, 200);
}
void Car_right()
{
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, 200);
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, 55);
}
void Car_Stop()
{
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, 0);
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, 0);
}

//The function controls servos
void procedure(byte myangle) {
  int pulsewidth;
  for (int i = 0; i < 5; i++) {
    pulsewidth = myangle * 11 + 500;  //Calculate the value of pulse width
    digitalWrite(servoPin, HIGH);
    delayMicroseconds(pulsewidth);   //The time in high level represents the pulse width
    digitalWrite(servoPin, LOW);
    delay((20 - pulsewidth / 1000));  //As the cycle is 20ms, the time left is in low level
  }
}

//The function controls ultrasonic sound
float checkdistance() {
  float distance;
  digitalWrite(Trig, LOW);
  delayMicroseconds(2);
  digitalWrite(Trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(Trig, LOW);
  distance = pulseIn(Echo, HIGH) / 58.20;  //The 58.20 here comes from 2*29.1=58.2
  delay(10);
  return distance;
}
//****************************************************************
