import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    property var binData: ({})
    implicitHeight: 138
    radius: 14
    color: theme.colors.panelRaised
    border.width: root.binData.isSelected ? 2 : 1
    border.color: root.binData.isSelected ? theme.colors.accent : theme.colors.border

    function cargoPoint(targetItem) {
        return cargo.mapToItem(targetItem, cargo.width * 0.70, cargo.height * 0.50)
    }

    Behavior on border.color { ColorAnimation { duration: 160 } }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Image {
                source: Qt.resolvedUrl("../assets/truck.svg")
                sourceSize.width: 64
                sourceSize.height: 34
                Layout.preferredWidth: 58
                Layout.preferredHeight: 30
                fillMode: Image.PreserveAspectFit
                smooth: true
            }

            Text {
                text: i18n.strings.truck + " " + (Number(root.binData.id || 0) + 1)
                color: theme.colors.text
                font.pixelSize: 15
                font.weight: Font.Bold
            }
            Item { Layout.fillWidth: true }
            Text {
                text: (root.binData.usedCapacity || 0) + " / " + (root.binData.capacity || 0)
                color: theme.colors.textSecondary
                font.pixelSize: 12
            }
        }

        Rectangle {
            id: cargo
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: 9
            color: theme.colors.track
            border.width: 1
            border.color: root.binData.isSelected ? theme.colors.borderStrong : theme.colors.border
            clip: true

            Row {
                anchors.fill: parent
                Repeater {
                    model: root.binData.items || []
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        height: cargo.height
                        width: cargo.width * (Number(modelData.size || 0) / Math.max(1, Number(root.binData.capacity || 1)))
                        color: index % 2 === 0 ? theme.colors.bar : theme.colors.bar
                        border.width: 1
                        border.color: theme.colors.bar

                        Row {
                            anchors.centerIn: parent
                            spacing: 4
                            visible: parent.width > 34
                            ObjectIcon { assetId: modelData.assetId || "generic"; iconSize: 21 }
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: parent.parent.width > 118
                                      ? modelData.displayName + " · " + i18n.strings.volume_abbr + " " + modelData.size
                                      : i18n.strings.volume_abbr + " " + modelData.size
                                color: theme.colors.text
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                width: Math.max(12, parent.parent.width - 34)
                            }
                        }
                        HoverHandler { id: cargoHover }
                        ToolTip.visible: cargoHover.hovered
                        ToolTip.text: modelData.displayName + " · " + i18n.strings.volume + ": " + modelData.size + " / " + root.binData.capacity
                        ToolTip.delay: 250
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: !root.binData.items || root.binData.items.length === 0
                text: i18n.strings.empty_cargo
                color: theme.colors.textSubtle
                font.pixelSize: 12
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: i18n.strings.free_space + ": " + (root.binData.remainingCapacity || 0)
                color: theme.colors.textMuted
                font.pixelSize: 11
            }
            Item { Layout.fillWidth: true }
            Text {
                text: Math.round(Number(root.binData.utilization || 0) * 100) + "% " + i18n.strings.occupied
                color: root.binData.isSelected ? theme.colors.accent : theme.colors.textMuted
                font.pixelSize: 11
                font.weight: root.binData.isSelected ? Font.Bold : Font.Normal
            }
        }
    }
}
