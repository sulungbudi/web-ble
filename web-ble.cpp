#include <Arduino.h>
// ESP32 BLE peripheral: writeable characteristic example
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

int led = 8;

#define SERVICE_UUID        "a12f0001-0000-1000-8000-00805f9b34fb"
#define CHARACTERISTIC_UUID "a12f0002-0000-1000-8000-00805f9b34fb"

BLECharacteristic *pCharacteristic;

class MyCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) {
    std::string value = characteristic->getValue();
    Serial.print("Received (len=");
    Serial.print(value.length());
    Serial.print("): ");
    // Print as ASCII text if printable
    for (size_t i = 0; i < value.length(); ++i) {
      Serial.print((char)value[i]);
    }
    Serial.println();

    // Example: interpret first byte as a command
    if (value.length() > 0) {
      uint8_t cmd = (uint8_t)value[0];
      if (cmd == 0x01) {
        Serial.println("Command 0x01 received: toggle LED");
        digitalWrite(led, !digitalRead(led)); // enable if an LED connected
      }
    }

    // If you want to reply via notifications:
    // pCharacteristic->setValue("ACK");
    // pCharacteristic->notify();
  }
};

void setup() {
  Serial.begin(115200);
  pinMode(led, OUTPUT); // optional onboard LED

  BLEDevice::init("ESP32-WebBLE"); // device name
  BLEServer *pServer = BLEDevice::createServer();

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );

  pCharacteristic->setCallbacks(new MyCallbacks());

  pService->start();

  // Advertise service
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // functions that help with iPhone connections
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("BLE Peripheral ready. Waiting for connections...");
}

void loop() {
  // nothing else required; onWrite callback handles incoming data
  delay(1000);
}
