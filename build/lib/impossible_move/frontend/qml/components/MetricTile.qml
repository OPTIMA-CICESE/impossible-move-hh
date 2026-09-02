import QtQuick

Rectangle {
    id: root
    property string label: ""
    property string value: "—"
    property bool accent: false
    property bool helpVisible: false
    signal helpRequested()

    implicitWidth: 126
    implicitHeight: 58
    radius: 11
    color: theme.colors.panelRaised
    border.width: 1
    border.color: root.accent ? theme.colors.borderStrong : theme.colors.border

    Column {
        anchors.centerIn: parent
        spacing: 2
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.label
            color: theme.colors.textMuted
            font.pixelSize: 10
            font.weight: Font.Bold
            font.letterSpacing: 0.4
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.value
            color: root.accent ? theme.colors.accent : theme.colors.text
            font.pixelSize: 18
            font.weight: Font.Bold
        }
    }

    Rectangle {
        visible: root.helpVisible
        width: 20
        height: 20
        radius: 10
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 6
        anchors.rightMargin: 6
        color: helpHover.hovered ? theme.colors.selected : theme.colors.cardSoft
        border.width: 1
        border.color: helpHover.hovered ? theme.colors.accent : theme.colors.borderStrong
        Text {
            anchors.centerIn: parent
            text: "?"
            color: helpHover.hovered ? theme.colors.accent : theme.colors.textMuted
            font.pixelSize: 10
            font.weight: Font.Bold
        }
        HoverHandler { id: helpHover }
        TapHandler { onTapped: root.helpRequested() }
    }
}
