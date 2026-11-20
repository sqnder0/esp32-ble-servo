import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: win
    visible: true
    width: 460
    height: 440
    minimumWidth: 400
    title: "ESP32 Servo Controller"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14

        GroupBox {
            title: "Connection"
            Layout.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                RowLayout {
                    Layout.fillWidth: true
                    ComboBox {
                        id: deviceBox
                        Layout.fillWidth: true
                        model: backend.deviceNames
                        enabled: !backend.connected
                        displayText: count === 0 ? "No devices - press Scan" : currentText
                    }
                    Button {
                        text: backend.scanning ? "Scanning..." : "Scan"
                        enabled: !backend.scanning && !backend.connected
                        onClicked: backend.scan()
                    }
                }
                Button {
                    Layout.fillWidth: true
                    text: backend.connected ? "Disconnect" : "Connect"
                    enabled: backend.connected || deviceBox.count > 0
                    onClicked: backend.connected
                        ? backend.disconnectDevice()
                        : backend.connectTo(deviceBox.currentIndex)
                }
            }
        }

        Repeater {
            model: 2
            GroupBox {
                required property int index
                title: "Servo " + (index + 1)
                Layout.fillWidth: true
                enabled: backend.connected

                RowLayout {
                    anchors.fill: parent
                    Slider {
                        id: slider
                        Layout.fillWidth: true
                        from: 0; to: 180; stepSize: 1; value: 90
                        onMoved: backend.setAngle(index, Math.round(value))
                    }
                    Label {
                        text: Math.round(slider.value) + "°"
                        Layout.preferredWidth: 44
                        horizontalAlignment: Text.AlignRight
                    }
                    Button {
                        text: "Center"
                        onClicked: { slider.value = 90; backend.setAngle(index, 90) }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        Label {
            Layout.fillWidth: true
            text: backend.status
            elide: Text.ElideRight
            opacity: 0.7
        }
    }
}
