import bluetooth
from micropython import const
from machine import Pin
import time

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_UUID      = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")   # Write
UART_TX_UUID      = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")   # Notify

UART_RX = (UART_RX_UUID, bluetooth.FLAG_WRITE)
UART_TX = (UART_TX_UUID, bluetooth.FLAG_NOTIFY)

UART_SERVICE = (UART_SERVICE_UUID, (UART_TX, UART_RX))

# Built-in LED on ESP32-C3 Super Mini = GPIO 8
led = Pin(8, Pin.OUT)

class BLEUART:
    def __init__(self, ble, name="ESP32C3-BLE"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((UART_SERVICE,))
        self._connections = set()
        self._rx_buffer = b""

        self._advertise(name)
        print("BLE UART ready")

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            print("Device connected")
            self._connections.add(conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print("Device disconnected")
            self._connections.remove(conn_handle)
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data

            if value_handle == self._rx_handle:
                self._rx_buffer = self._ble.gatts_read(self._rx_handle)

                # Print raw bytes
                print("Raw:", self._rx_buffer)

                # Handle command 0x01 → toggle LED
                if len(self._rx_buffer) > 0 and self._rx_buffer[0] == 0x01:
                    print("Command 0x01 received → TOGGLE LED")
                    led.value(not led.value())
                    self.send("LED toggled")

                # Try decoding for debugging
                try:
                    msg = self._rx_buffer.decode("utf-8")
                except:
                    msg = str(self._rx_buffer)

                print("Received:", msg)

    def send(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        for conn in self._connections:
            self._ble.gatts_notify(conn, self._tx_handle, data)

    def _advertise(self, name="ESP32C3-BLE"):
        name_bytes = bytes(name, "utf-8")
        adv = bytearray([
            len(name_bytes) + 1,
            0x09,
        ]) + name_bytes

        print("Advertising:", name)
        self._ble.gap_advertise(100, adv)


# ========== MAIN ==========
ble = bluetooth.BLE()
uart = BLEUART(ble, name="ESP32C3-WebBLE")

print("Waiting for Web-BLE or BLE app...")
while True:
    time.sleep(1)

