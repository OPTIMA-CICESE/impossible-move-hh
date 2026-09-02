import QtQuick
import QtQuick.Controls

Button {
    id: root
    property bool accent: false
    property string buttonText: ""
    property int minimumButtonWidth: 104

    hoverEnabled: true
    implicitHeight: 42
    implicitWidth: Math.max(minimumButtonWidth, label.implicitWidth + 30)
    text: buttonText
    font.pixelSize: 14
    font.weight: Font.DemiBold

    contentItem: Text {
        id: label
        text: root.text
        font: root.font
        color: root.enabled ? (root.accent ? theme.colors.accentText : theme.colors.text) : theme.colors.textSubtle
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: 10
        color: {
            if (!root.enabled) return theme.colors.button
            if (root.accent) {
                if (root.down) return theme.colors.accentPressed
                if (root.hovered) return theme.colors.accentHover
                return theme.colors.accent
            }
            if (root.down) return theme.colors.buttonPressed
            if (root.hovered) return theme.colors.buttonHover
            return theme.colors.button
        }
        border.width: 1
        border.color: root.accent ? theme.colors.accent : (root.hovered ? theme.colors.borderStrong : theme.colors.border)
        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }
}
