import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property var scoreData: ({})
    implicitHeight: 48

    RowLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            Layout.preferredWidth: 82
            text: root.scoreData.label || ""
            color: root.scoreData.selected ? theme.colors.accent : theme.colors.textSecondary
            font.pixelSize: 12
            font.weight: root.scoreData.selected ? Font.Bold : Font.Medium
            elide: Text.ElideRight
        }

        Rectangle {
            id: track
            Layout.fillWidth: true
            Layout.preferredHeight: 12
            radius: 6
            color: theme.colors.track

            Rectangle {
                height: parent.height
                width: Math.max(0, parent.width * (root.scoreData.normalized || 0))
                radius: 6
                color: root.scoreData.selected ? theme.colors.accent : theme.colors.bar
                Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                Behavior on color { ColorAnimation { duration: 160 } }
            }
        }

        Text {
            Layout.preferredWidth: 38
            text: Number(root.scoreData.score || 0).toFixed(2)
            color: root.scoreData.selected ? theme.colors.accent : theme.colors.textMuted
            font.pixelSize: 11
            horizontalAlignment: Text.AlignRight
        }
    }
}
