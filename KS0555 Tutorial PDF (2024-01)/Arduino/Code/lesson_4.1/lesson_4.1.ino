/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 4.1
  Line Track sensor
  http://www.keyestudio.com
*/
//The wiring of line tracking sensors
#define L_pin  11  //left
#define M_pin  7  //middle
#define R_pin  8  //right

void setup()
{
  Serial.begin(9600); //Set the baud rate to 9600
  pinMode(L_pin, INPUT); //Set all pins of the line tracking sensors to input mode
  pinMode(M_pin, INPUT);
  pinMode(R_pin, INPUT);
}

void loop ()
{
  int L_val = digitalRead(L_pin); //Read the value of the left sensor 
  int M_val = digitalRead(M_pin); //Read the value of the middle sensor
  int R_val = digitalRead(R_pin); //Read the value of the right sensor
  Serial.print(L_val);
  Serial.print("  ");
  Serial.print(M_val);
  Serial.print("  ");
  Serial.print(R_val);
  Serial.println("  ");
  delay(100); //delay in 100ms
}
//******************************************************
