/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 1.2
  Blink
  http://www.keyestudio.com
*/
int LED = 9;  //Define the pin of the LED as 9
void setup()
{
  pinMode(LED, OUTPUT); //Set the pin of the LED to OUTPUT
}
void loop() //Infinite loop
{
  digitalWrite(LED, HIGH); //output high levels, light up LED
  delay(100);  //Wait for 0.1s
  digitalWrite(LED, LOW);  //LED output low levels, turn off LED
  delay(100);  //Wait for 0.1s
}
//****************************************************************
