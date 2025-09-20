/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 0
  Blink
  http://www.keyestudio.com
*/
#include <Servo.h>
Servo myservo;  // Creating a servo object
int pos = 90;    // Stored at an angle of 90 degrees
void setup() {
  myservo.attach(10);  //Servo servo connected to digital pin 10
}
void loop() {
    myservo.write(pos);     // Rotate to pos angle position             
  }
