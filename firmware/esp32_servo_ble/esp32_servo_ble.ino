// ESP32 BLE two-servo controller
// Libraries: "ESP32Servo" (Library Manager) + the BLE library bundled with the ESP32 Arduino core.
// Board: any ESP32 (classic or S3/C3 with BLE). Wiring: servo signal -> GPIO 18 / 19,
// servo V+ -> external 5 V supply (NOT the ESP32 3V3 pin), servo GND -> ESP32 GND (common ground).

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <ESP32Servo.h>

#define DEVICE_NAME   "ESP32-Servo"
#define SERVICE_UUID  "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define SERVO1_UUID   "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define SERVO2_UUID   "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

const int SERVO_PINS[2] = {18, 19};
const int PULSE_MIN_US = 500;
const int PULSE_MAX_US = 2400;

Servo servos[2];
BLECharacteristic *chars[2];

class AngleCallbacks : public BLECharacteristicCallbacks {
 public:
  explicit AngleCallbacks(int idx) : idx_(idx) {}
  void onWrite(BLECharacteristic *c) override {
    if (c->getLength() < 1) return;
    int angle = constrain((int)c->getData()[0], 0, 180);
    servos[idx_].write(angle);
    Serial.printf("servo %d -> %d\n", idx_ + 1, angle);
  }
 private:
  int idx_;
};

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *) override { Serial.println("client connected"); }
  void onDisconnect(BLEServer *) override {
    Serial.println("client disconnected, advertising again");
    BLEDevice::startAdvertising();
  }
};

void setup() {
  Serial.begin(115200);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  for (int i = 0; i < 2; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(SERVO_PINS[i], PULSE_MIN_US, PULSE_MAX_US);
    servos[i].write(90);
  }

  BLEDevice::init(DEVICE_NAME);
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  BLEService *service = server->createService(SERVICE_UUID);

  const char *uuids[2] = {SERVO1_UUID, SERVO2_UUID};
  for (int i = 0; i < 2; i++) {
    chars[i] = service->createCharacteristic(
        uuids[i], BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);
    chars[i]->setCallbacks(new AngleCallbacks(i));
    uint8_t initial = 90;
    chars[i]->setValue(&initial, 1);
  }
  service->start();

  BLEAdvertising *adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("advertising as " DEVICE_NAME);
}

void loop() { delay(1000); }
