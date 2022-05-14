#include <Adafruit_NeoPixel.h>
#include <math.h>
#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

const int LEDPin = 16;  /* GPIO16 */

int ledVal = 2;

/* Setting PWM Properties */
const int PWMFreq = 5000; /* 5 KHz */
const int PWMChannel = 0;
const int PWMResolution = 10;
const int MAX_DUTY_CYCLE = (int)(pow(2, PWMResolution) - 1);

const char *mqtt_server = "dekscope";

const char *ssid = "artdeco"; // Enter your WiFi name
const char *password = "Recurser";  // Enter WiFi password

// MQTT Broker


WiFiClient espClient;
PubSubClient client(espClient); //lib required for mqtt


void callback(char* topic, byte* payload, unsigned int length) {
  String _topic(topic);
  String message = String(std::string((const char*)payload, length).c_str());
  if (_topic == "dekscope/led") {
    ledVal = message.toInt();
  }
}

bool reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("arduinoClient")) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      Serial.println("publishing");
      // ... and resubscribe
      Serial.println("subscribing");

      client.subscribe("dekscope/led");
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

Adafruit_NeoPixel strip = Adafruit_NeoPixel(7, LEDPin, NEO_RGBW);

void setup_strip() {
  
  strip.begin();
  strip.setBrightness(ledVal);
  for(uint16_t i=0; i<strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(0, 0, 0, 255));
  }
  //strip.setPixelColor(0, strip.Color(0, 0, 0, 255));
  strip.show(); 

}

void setup_pwm() {

  ledcSetup(PWMChannel, PWMFreq, PWMResolution);
  // /* Attach the LED PWM Channel to the GPIO Pin */
  ledcAttachPin(LEDPin, PWMChannel);
}

void setup()
{
  setup_strip();
  Serial.begin(115200);
  Serial.setDebugOutput(true);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.println("Connecting to WiFi..");
  }

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop_strip() {
  strip.setBrightness(ledVal);
  strip.show();
}

void loop_pwm() {
  ledcWrite(PWMChannel, ledVal);
}

void loop()
{
  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  loop_strip();
}