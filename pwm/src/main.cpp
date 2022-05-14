#include <math.h>
#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

const int LEDPin = 16;  /* GPIO16 */

int ledVal = 32;

/* Setting PWM Properties */
const int PWMFreq = 5000; /* 5 KHz */
const int PWMChannel = 0;
const int PWMResolution = 10;
const int MAX_DUTY_CYCLE = (int)(pow(2, PWMResolution) - 1);

const char *mqtt_server = "dekscope";
const char *client_name = "testclient";
const char *ssid = "artdeco"; // Enter your WiFi name
const char *password = "";  // Enter WiFi password

// MQTT Broker


WiFiClient espClient;
PubSubClient client(espClient); //lib required for mqtt


void callback(char* topic, byte* payload, unsigned int length) {
  String _topic(topic);
  String message = String(std::string((const char*)payload, length).c_str());
  Serial.println(topic);
  Serial.println(message);
  if (_topic == "led") {
    ledVal = message.toInt();
    Serial.print("Led value set to: ");
    Serial.println(ledVal);
  }
}

bool reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(client_name)) {
      Serial.println("connected");
      delay(1000);
      client.subscribe("led");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
      return false;
    }
  }
  return true;
}

void setup()
{
  Serial.begin(115200);
  Serial.setDebugOutput(true);


  ledcSetup(PWMChannel, PWMFreq, PWMResolution);
  /* Attach the LED PWM Channel to the GPIO Pin */
  ledcAttachPin(LEDPin, PWMChannel);
  ledcWrite(PWMChannel, ledVal);


  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.println("Connecting to WiFi..");
  }



  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  
  client.loop();
  ledcWrite(PWMChannel, ledVal);
}