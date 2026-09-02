import QtQuick

Item {
    id: root
    property var objectData: ({})
    property real replaySpeed: 1.0
    property real endX: 0
    property real endY: 0
    property bool active: flight.running

    function fly(data, startX, startY, targetX, targetY) {
        objectData = data || ({})
        endX = targetX
        endY = targetY
        bubble.x = startX - bubble.width / 2
        bubble.y = startY - bubble.height / 2
        bubble.opacity = 1
        bubble.scale = 1.0
        bubble.visible = true
        flight.restart()
    }

    Rectangle {
        id: bubble
        visible: false
        width: 74
        height: 74
        radius: 20
        color: theme.colors.card
        border.width: 2
        border.color: theme.colors.accent
        z: 1000

        Rectangle {
            anchors.fill: parent
            anchors.margins: -7
            radius: 25
            color: "transparent"
            border.width: 1
            border.color: theme.colors.card
            opacity: 0.55
        }

        ObjectIcon {
            anchors.centerIn: parent
            assetId: root.objectData.assetId || "generic"
            iconSize: 50
        }
    }

    ParallelAnimation {
        id: flight
        NumberAnimation {
            target: bubble
            property: "x"
            to: root.endX - bubble.width / 2
            duration: Math.max(90, 560 / Math.max(0.5, root.replaySpeed))
            easing.type: Easing.InOutCubic
        }
        NumberAnimation {
            target: bubble
            property: "y"
            to: root.endY - bubble.height / 2
            duration: Math.max(90, 560 / Math.max(0.5, root.replaySpeed))
            easing.type: Easing.InOutCubic
        }
        SequentialAnimation {
            NumberAnimation {
                target: bubble
                property: "scale"
                to: 1.18
                duration: Math.max(45, 240 / Math.max(0.5, root.replaySpeed))
                easing.type: Easing.OutQuad
            }
            NumberAnimation {
                target: bubble
                property: "scale"
                to: 0.82
                duration: Math.max(45, 320 / Math.max(0.5, root.replaySpeed))
                easing.type: Easing.InQuad
            }
        }
        onFinished: {
            bubble.opacity = 0
            bubble.visible = false
        }
    }
}
