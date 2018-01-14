#include <PubSubClient.h>
#include <ESP8266WiFi.h>
// #include <ESP8266WiFiAP.h>
// #include <ESP8266WiFiGeneric.h>
//#include <ESP8266WiFiMulti.h>
//#include <ESP8266WiFiScan.h>
//#include <ESP8266WiFiSTA.h>
//#include <ESP8266WiFiType.h>
//#include <WiFiClient.h>
//#include <WiFiClientSecure.h>
// #include <WiFiServer.h>
//#include <WiFiUdp.h>

#define LED     D0
#define PREVIEW D1
#define SHUTTER D2
#define APPROVE D5
#define REJECT  D6

#define BRIGHT    350     //max led intensity (1-500)
#define INHALE    1250    //Inhalation time in milliseconds.
#define PULSE     INHALE*1000/BRIGHT
#define REST      1000    //Rest Between Inhalations.

//const char ssid[] = "The Future";
//const char pass[] = "VerySecurity!";

// const char ssid[] = "HitachiMagicWand";
// const char pass[] = "happyplace";

const char ssid[] = "photobooth";
const char pass[] = "saycheese";


IPAddress mqtt_server(192,168,2,1);
IPAddress google(216,58,192,132);
IPAddress myip (192,168,2,2);

int mqtt_port = 1883;
const char username[] = "remote";
const char password[] = "remote";

WiFiClient espClient;
WiFiClient httpClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;

bool preview = true;
bool shutter = true;
bool approve = true;
bool reject  = true;

int status = WL_IDLE_STATUS;

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void setup() {
  // put your setup code here, to run once:
  pinMode(LED, OUTPUT);

  // setup switches
  pinMode (PREVIEW, INPUT_PULLUP);
  pinMode (SHUTTER, INPUT_PULLUP);
  pinMode (APPROVE, INPUT_PULLUP);
  pinMode (REJECT , INPUT_PULLUP);
  
  Serial.begin(9600);
  Serial.println("attempting to connect to the network.");
  WiFi.config(myip, IPAddress(192,168,2,1), IPAddress(255,255,255,0));
  status = WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
   delay(500);
   Serial.print(".");
  }
  Serial.println("connected!");
  Serial.println(WiFi.localIP());
#if 0
  if (httpClient.connect(google, 80)) {
      Serial.println("connected to google");
      // Make a HTTP request:
      httpClient.println("GET /search?q=arduino HTTP/1.0");
      httpClient.println();
      delay(300);
      int c = httpClient.read();
      while (c > -1) {
        Serial.print(c);
        c = httpClient.read();
      }
    }
#endif    
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "joystick";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(), username, password )) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      // client.publish("outTopic", "hello world");
      // ... and resubscribe
      // client.subscribe("photobooth");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void handleButton(int pin, bool &state, const char *msg)
{
    // shutter
  if (!digitalRead(pin)) {
    if (state) {
      state = false;
      client.publish("photobooth", msg);
      Serial.print("Publish message: ");
      Serial.println(msg);
      delay(250);
    }
  } else {
    if (!state) {
      state = true;
    }
  }

}

void loop() {
  // put your main code here, to run repeatedly:
  //ramp increasing intensity, Inhalation: 
#if 0 
  for (int i=1;i<BRIGHT;i++){
    digitalWrite(LED, LOW);          // turn the LED on.
    delayMicroseconds(i*10);         // wait
    digitalWrite(LED, HIGH);         // turn the LED off.
    delayMicroseconds(PULSE-i*10);   // wait
    delay(0);                        //to prevent watchdog firing.
  }
  //ramp decreasing intensity, Exhalation (half time):
  for (int i=BRIGHT-1;i>0;i--){
    digitalWrite(LED, LOW);          // turn the LED on.
    delayMicroseconds(i*10);          // wait
    digitalWrite(LED, HIGH);         // turn the LED off.
    delayMicroseconds(PULSE-i*10);  // wait
    i--;
    delay(0);                        //to prevent watchdog firing.
  }
  delay(REST);                       //take a rest...
#endif

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  handleButton(PREVIEW, preview, "preview");
  handleButton(SHUTTER, shutter, "shutter");
  handleButton(APPROVE, approve, "approve");
  handleButton(REJECT , reject , "reject" );

}
