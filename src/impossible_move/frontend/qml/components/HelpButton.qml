import QtQuick
import QtQuick.Controls

Button {
    id: root
    property int diameter: 26
    hoverEnabled: true
    implicitWidth: diameter
    implicitHeight: diameter
    text: "?"
    font.pixelSize: 12
    font.weight: Font.Bold

    contentItem: Text {
        text: root.text
        color: root.down ? theme.colors.accentText : (root.hovered ? theme.colors.accent : theme.colors.textMuted)
        font: root.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: root.diameter / 2
        color: root.down ? theme.colors.accent : (root.hovered ? theme.colors.selected : theme.colors.card)
        border.width: 1
        border.color: root.hovered ? theme.colors.accent : theme.colors.borderStrong
        Behavior on color { ColorAnimation { duration: 110 } }
        Behavior on border.color { ColorAnimation { duration: 110 } }
    }
}
