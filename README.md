# ESP32 BLE servo controller

## 1. Flash the ESP32
1. Arduino IDE → Boards Manager: install **esp32** (by Espressif). Library Manager: install **ESP32Servo**.
2. Open `firmware/esp32_servo_ble/esp32_servo_ble.ino`, pick your ESP32 board, upload.
3. Wiring: servo 1 signal → GPIO 18, servo 2 signal → GPIO 19, servo V+ → external 5 V,
   servo GND → ESP32 GND (shared ground). Don't power servos from the ESP32 3V3 pin.

The ESP32 advertises as `ESP32-Servo` with one service and two characteristics
(1 byte each, angle 0–180): servo 1 `6e400002-…`, servo 2 `6e400003-…`.

## 2. Run the desktop app
```bash
pip install PySide6
python app/main.py
```
Press **Scan**, choose `ESP32-Servo`, **Connect**, then use the sliders.
Needs the `bluetooth` service running (`systemctl start bluetooth`).
