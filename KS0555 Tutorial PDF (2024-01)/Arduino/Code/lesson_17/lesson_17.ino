/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 17
  Bluetooth
  http://www.keyestudio.com
*/
int LED = 9;
char ble_val; //Integer variable used to store the value received by Bluetooth

void setup() {
  Serial.begin(9600);
  pinMode(LED, OUTPUT);
}
void loop() {
  if (Serial.available() > 0) //Determine whether there is data in the serial port buffer
  {
    ble_val = Serial.read();  //Read data from serial port buffer
    Serial.print("DATA RECEIVED:");
    Serial.println(ble_val);
    if (ble_val == 'a') {
      digitalWrite(LED, HIGH);
      Serial.println("led on");
    }
    if (ble_val == 'b') {
      digitalWrite(LED, LOW);
      Serial.println("led off");
    }
  }
}
//*******************************************
