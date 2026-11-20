"""Desktop controller for the ESP32 BLE servo firmware (PySide6 + QML + Qt Bluetooth)."""
import sys
from pathlib import Path

from PySide6.QtBluetooth import (
    QBluetoothDeviceDiscoveryAgent,
    QBluetoothDeviceInfo,
    QBluetoothUuid,
    QLowEnergyController,
    QLowEnergyService,
)
from PySide6.QtCore import Property, QByteArray, QObject, QUuid, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
SERVO_UUIDS = [
    "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
    "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
]


class ServoBackend(QObject):
    devicesChanged = Signal()
    statusChanged = Signal()
    connectedChanged = Signal()
    scanningChanged = Signal()

    def __init__(self):
        super().__init__()
        self._devices: list[QBluetoothDeviceInfo] = []
        self._status = "Idle"
        self._connected = False
        self._scanning = False
        self._controller: QLowEnergyController | None = None
        self._service: QLowEnergyService | None = None
        self._pending: dict[int, int] = {}
        self._busy = False

        self._agent = QBluetoothDeviceDiscoveryAgent(self)
        self._agent.setLowEnergyDiscoveryTimeout(6000)
        self._agent.deviceDiscovered.connect(self._on_device)
        self._agent.finished.connect(self._on_scan_done)
        self._agent.errorOccurred.connect(self._on_scan_error)

    # ---- properties -------------------------------------------------
    @Property("QStringList", notify=devicesChanged)
    def deviceNames(self):
        return [f"{d.name()}  ({d.address().toString()})" for d in self._devices]

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property(bool, notify=connectedChanged)
    def connected(self):
        return self._connected

    @Property(bool, notify=scanningChanged)
    def scanning(self):
        return self._scanning

    def _set_status(self, text):
        self._status = text
        self.statusChanged.emit()

    def _set_connected(self, value):
        if self._connected != value:
            self._connected = value
            self.connectedChanged.emit()

    # ---- scanning ---------------------------------------------------
    @Slot()
    def scan(self):
        if self._scanning:
            return
        self._devices.clear()
        self.devicesChanged.emit()
        self._scanning = True
        self.scanningChanged.emit()
        self._set_status("Scanning for BLE devices...")
        self._agent.start(QBluetoothDeviceDiscoveryAgent.DiscoveryMethod.LowEnergyMethod)

    def _on_device(self, info: QBluetoothDeviceInfo):
        if not (info.coreConfigurations() & QBluetoothDeviceInfo.CoreConfiguration.LowEnergyCoreConfiguration):
            return
        if not info.name():
            return
        if any(d.address() == info.address() for d in self._devices):
            return
        self._devices.append(info)
        # ESP32 devices first
        self._devices.sort(key=lambda d: not d.name().startswith("ESP32"))
        self.devicesChanged.emit()

    def _on_scan_done(self):
        self._scanning = False
        self.scanningChanged.emit()
        self._set_status(f"Scan finished: {len(self._devices)} device(s)")

    def _on_scan_error(self, *_):
        self._scanning = False
        self.scanningChanged.emit()
        self._set_status(f"Scan error: {self._agent.errorString()}")

    # ---- connection -------------------------------------------------
    @Slot(int)
    def connectTo(self, index):
        if not 0 <= index < len(self._devices):
            return
        self.disconnectDevice()
        info = self._devices[index]
        self._set_status(f"Connecting to {info.name()}...")
        ctrl = QLowEnergyController.createCentral(info, self)
        ctrl.connected.connect(self._on_connected)
        ctrl.disconnected.connect(self._on_disconnected)
        ctrl.errorOccurred.connect(lambda *_: self._set_status(f"Error: {ctrl.errorString()}"))
        ctrl.serviceDiscovered.connect(self._on_service_found)
        ctrl.discoveryFinished.connect(self._on_discovery_finished)
        self._controller = ctrl
        ctrl.connectToDevice()

    @Slot()
    def disconnectDevice(self):
        if self._controller:
            ctrl, self._controller = self._controller, None
            ctrl.disconnectFromDevice()
            ctrl.deleteLater()
        self._service = None
        self._pending.clear()
        self._busy = False
        self._set_connected(False)

    def _on_connected(self):
        self._set_status("Connected, discovering services...")
        self._controller.discoverServices()

    def _on_disconnected(self):
        self._service = None
        self._set_connected(False)
        self._set_status("Disconnected")

    def _on_service_found(self, uuid: QBluetoothUuid):
        pass

    def _on_discovery_finished(self):
        if not self._controller:
            return
        service = self._controller.createServiceObject(QBluetoothUuid(QUuid(SERVICE_UUID)), self)
        if service is None:
            self._set_status("Servo service not found on this device")
            return
        service.stateChanged.connect(self._on_service_state)
        service.characteristicWritten.connect(self._on_written)
        service.errorOccurred.connect(lambda *_: self._on_write_error())
        self._service = service
        service.discoverDetails()

    def _on_service_state(self, state):
        if state == QLowEnergyService.ServiceState.RemoteServiceDiscovered:
            self._set_connected(True)
            self._set_status("Ready")

    # ---- writing ----------------------------------------------------
    @Slot(int, int)
    def setAngle(self, servo, angle):
        """Latest value per servo wins; sent one write at a time."""
        if not self._connected:
            return
        self._pending[servo] = max(0, min(180, int(angle)))
        self._flush()

    def _flush(self):
        if self._busy or not self._pending or not self._service:
            return
        servo = next(iter(self._pending))
        angle = self._pending.pop(servo)
        char = self._service.characteristic(QBluetoothUuid(QUuid(SERVO_UUIDS[servo])))
        if not char.isValid():
            self._set_status(f"Servo {servo + 1} characteristic missing")
            return
        self._busy = True
        self._service.writeCharacteristic(
            char, QByteArray(bytes([angle])), QLowEnergyService.WriteMode.WriteWithResponse
        )

    def _on_written(self, *_):
        self._busy = False
        self._flush()

    def _on_write_error(self):
        self._busy = False
        self._set_status("Write error")


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    backend = ServoBackend()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(Path(__file__).with_name("Main.qml"))
    if not engine.rootObjects():
        sys.exit(1)
    code = app.exec()
    backend.disconnectDevice()
    sys.exit(code)


if __name__ == "__main__":
    main()
