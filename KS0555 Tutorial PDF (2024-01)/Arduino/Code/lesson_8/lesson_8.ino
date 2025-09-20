/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 8
  motor driver
  http://www.keyestudio.com
*/
#define ML_Ctrl 4  //Define the direction control pin of the left motor
#define ML_PWM  6  //Define the PWM control pin of the left motor
#define MR_Ctrl 2  //Define the direction control pin of the right motor
#define MR_PWM  5  //Define the PWM control pin of the right motor

void setup()
{
  pinMode(ML_Ctrl, OUTPUT);//Define the direction control pin of the left motor as OUTPUT
  pinMode(ML_PWM, OUTPUT);//Define the PWM control pin of the left motor as OUTPUT
  pinMode(MR_Ctrl, OUTPUT);//Define the direction control pin of the right motor as OUTPUT
  pinMode(MR_PWM, OUTPUT);//Define the PWM control pin of the right motor as OUTPUT
}

void loop()
{
  //front
  digitalWrite(ML_Ctrl, HIGH); //Set direction control speed of the left motor to HIGH
  analogWrite(ML_PWM, 55); //PWM control speed of the left motor is 200
  digitalWrite(MR_Ctrl, HIGH); //Set direction control speed of the right motor to HIGH
  analogWrite(MR_PWM, 55); //PWM control speed of the right motor is 200
  delay(2000);//delay in 2s
  
  //back
  digitalWrite(ML_Ctrl, LOW); //Set direction control speed of the left motor to LOW
  analogWrite(ML_PWM, 200); //PWM control speed of the left motor is 200
  digitalWrite(MR_Ctrl, LOW); //Set direction control speed of the right motor to LOW
  analogWrite(MR_PWM, 200); //PWM control speed of the right motor is 200
  delay(2000);//delay in 2s
  
  //turn left
  digitalWrite(ML_Ctrl, LOW); //Set direction control speed of the left motor to LOW
  analogWrite(ML_PWM, 200); //PWM control speed of the left motor is 200
  digitalWrite(MR_Ctrl, HIGH); //Set direction control speed of the right motor to HIGH
  analogWrite(MR_PWM, 55); //PWM control speed of the right motor is 200
  delay(2000);//delay in 2s

  //turn right
  digitalWrite(ML_Ctrl, HIGH); //Set direction control speed of the left motor to HIGH
  analogWrite(ML_PWM, 55); //PWM control speed of the left motor is 200
  digitalWrite(MR_Ctrl, LOW); //Set direction control speed of the right motor to LOW
  analogWrite(MR_PWM, 200); //PWM control speed of the right motor is 200
  delay(2000);//delay in 2s

  //stop
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, 0); //PWM control speed of the left motor is 0
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, 0); //PWM control speed of the right motor is 0
  delay(2000);//delay in 2s
}
//*****************************************
