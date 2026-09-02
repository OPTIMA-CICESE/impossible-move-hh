import QtQuick
import QtQuick.Controls

ScrollBar {
    id: control

    policy: ScrollBar.AsNeeded
    interactive: true
    hoverEnabled: true
    padding: 2

    // Attached ScrollBars occasionally inherit only their implicit span from
    // nested layouts. Force the control to follow the complete viewport so the
    // track is distributed across the whole scrollable area.
    width: orientation === Qt.Horizontal && parent ? parent.width : implicitWidth
    height: orientation === Qt.Vertical && parent ? parent.height : implicitHeight

    minimumSize: {
        const span = control.orientation === Qt.Vertical ? control.height : control.width
        return span > 0 ? Math.min(1.0, Math.max(0.10, 42 / span)) : 0.10
    }

    implicitWidth: orientation === Qt.Vertical ? 10 : 80
    implicitHeight: orientation === Qt.Horizontal ? 10 : 80

    background: Rectangle {
        radius: 5
        color: theme.colors.track
        border.width: 1
        border.color: theme.colors.border
        opacity: control.size < 1.0 ? 0.62 : 0.0
    }

    contentItem: Rectangle {
        radius: 5
        color: control.pressed ? theme.colors.accent : theme.colors.bar
        opacity: control.size < 1.0 ? (control.active || control.hovered || control.pressed ? 1.0 : 0.82) : 0.0

        Behavior on color { ColorAnimation { duration: 110 } }
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }
}
