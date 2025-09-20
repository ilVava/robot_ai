/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 16
  Bluetooth
  http://www.keyestudio.com
*/
char ble_val; //Character variable(used to store the value received by Bluetooth)


void setup() {
  Serial.begin(9600);
}
void loop() {
  if (Serial.available() > 0) //Determine whether there is data in the serial port buffer
  {
    ble_val = Serial.read();  //Read the data in the serial port buffer
    Serial.println(ble_val);  //Print out
  }
}
//*******************************************
