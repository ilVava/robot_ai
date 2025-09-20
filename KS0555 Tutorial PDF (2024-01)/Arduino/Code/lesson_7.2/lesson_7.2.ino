/*
  Keyestudio Mini Tank Robot V3 (Popular Edition)
  lesson 7.2
  IRremote
  http://www.keyestudio.com
*/
#include <IRremote.h>     //IRremote statement
int RECV_PIN = 3;        //define the pin of LED as pin 3
int LED = 9;
bool flag = 0;
IRrecv irrecv(RECV_PIN);
decode_results results;   //decode results exist in the“result” of “decode results
void setup() {
  Serial.begin(9600);
  pinMode(LED, OUTPUT);//set LED to output
  irrecv.enableIRIn();    //Enable receiver
}
void loop() {
  if (irrecv.decode(&results)) {
    if (results.value == 0xFF02FD & flag == 0) //The above key code, we use the OK button on the remote control, if you press the OK button

    {
      digitalWrite(LED, HIGH); //LED on
      flag = 1;
    }
    else if (results.value == 0xFF02FD & flag == 1) //press again
    {
      digitalWrite(LED, LOW); //LED off
      flag = 0;
    }
    irrecv.resume(); // Receive the next value
  }
}
//*******************************************************
