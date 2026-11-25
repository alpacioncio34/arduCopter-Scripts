// ESP32: 7 pulsadores -> mensajes WebSocket al servidor Python.
// Libreria: "WebSockets" de Markus Sattler (links2004)
// Cableado: un pin del pulsador a GPIO, el opuesto a GND (pull-up interno).

#include <WiFi.h>
#include <WebSocketsClient.h>

const char* WIFI_SSID = "REDWIFI";
const char* WIFI_PASS = "CONTRASEÑA";
const char* WS_HOST   = "IDENTIFICADOR";
const uint16_t WS_PORT = 8765;

const uint8_t PINS[8] = {13, 14, 25, 26, 27, 32, 33, 12};  // botones 1..7
const uint32_t DEBOUNCE_MS = 25;

WebSocketsClient ws;
const int NUM_BTN = sizeof(PINS) / sizeof(PINS[0]);
bool lastState[NUM_BTN];
uint32_t lastChange[NUM_BTN];
;uint32_t seq = 0;
int64_t sentAt[256];  // micros() del envio, indexado por seq % 256

void onEvent(WStype_t type, uint8_t* payload, size_t len) {
  switch (type) {
    case WStype_CONNECTED:    Serial.println("WS conectado"); break;
    case WStype_DISCONNECTED: Serial.println("WS desconectado"); break;
    case WStype_TEXT: {
      // Ack del servidor: "A,<seq>"
      if (len > 2 && payload[0] == 'A') {
        uint32_t s = atoi((char*)payload + 2);
        uint32_t rtt = (uint32_t)(esp_timer_get_time() - sentAt[s % 256]);
        Serial.printf("seq %u RTT %u us\n", s, rtt);
        char buf[48];
        snprintf(buf, sizeof(buf), "L,%u,%u", s, rtt);
        ws.sendTXT(buf);
      }
      break;
    }
    default: break;
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_BTN; i++) {
    pinMode(PINS[i], INPUT_PULLUP);
    lastState[i] = HIGH;
  }
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // clave para baja latencia / poco jitter
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(200);
  Serial.println(WiFi.localIP());

  ws.begin(WS_HOST, WS_PORT, "/");
  ws.onEvent(onEvent);
  ws.setReconnectInterval(2000);
  pinMode(12, INPUT_PULLUP);
}

void loop() {
  ws.loop();
  uint32_t now = millis();
  for (int i = 0; i < NUM_BTN; i++) {
    bool s = digitalRead(PINS[i]);
    if (s != lastState[i] && now - lastChange[i] > DEBOUNCE_MS) {
      lastChange[i] = now;
      lastState[i] = s;
      if (ws.isConnected()) {  // pulsacion (1) y suelta (0)
        seq++;
        char buf[32];
        snprintf(buf, sizeof(buf), "B,%d,%u,%d", i + 1, seq, s == LOW ? 1 : 0);
        sentAt[seq % 256] = esp_timer_get_time();
        ws.sendTXT(buf);
      }
    }
  }
}
