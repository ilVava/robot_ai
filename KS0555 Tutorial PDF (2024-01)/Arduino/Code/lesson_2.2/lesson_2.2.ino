/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 2.2
  pwm-slow
  http://www.keyestudio.com
*/
int LED = 9;  //Define the pin of the LED as 9

void setup () {
  pinMode (LED, OUTPUT); //Set the pin of the LED to OUTPUT
}
void loop () {
  for (int value = 0; value < 255; value = value + 1) {
    analogWrite (LED, value); // LED ON
    delay (30); // delay in 30ms
  }
  for (int value = 255; value > 0; value = value - 1) {
    analogWrite (LED, value); //LED gets dim
    delay (30); // delay in 30ms
  }
}
//**********************************************************
