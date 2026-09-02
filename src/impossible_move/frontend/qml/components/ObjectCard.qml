import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property var itemData: ({})
    property bool highlighted: false

    radius: 12
    color: highlighted ? theme.colors.selected : theme.colors.card
    border.width: highlighted ? 2 : 1
    border.color: highlighted ? theme.colors.accent : theme.colors.border
    implicitWidth: 118
    implicitHeight: 94

    Behavior on color { ColorAnimation { duration: 160 } }
    Behavior on border.color { ColorAnimation { duration: 160 } }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 9
        spacing: 3

        ObjectIcon {
            Layout.alignment: Qt.AlignHCenter
            assetId: root.itemData.assetId || "generic"
            iconSize: 28
        }

        Text {
            Layout.fillWidth: true
            text: root.itemData.displayName || i18n.strings.object_generic
            color: theme.colors.text
            font.pixelSize: 12
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }

        Text {
            Layout.fillWidth: true
            text: i18n.strings.volume + ": " + (root.itemData.size || "–")
            color: theme.colors.textSecondary
            font.pixelSize: 11
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
