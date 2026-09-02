import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    hoverEnabled: true
    implicitHeight: 36
    implicitWidth: 126
    leftPadding: 12
    rightPadding: 30
    font.pixelSize: 11
    font.weight: Font.DemiBold

    delegate: ItemDelegate {
        id: delegateItem
        required property var modelData
        width: ListView.view ? ListView.view.width : control.width
        height: 36
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: control.textRole ? modelData[control.textRole] : modelData
            color: delegateItem.highlighted ? theme.colors.accent : theme.colors.textSecondary
            font.pixelSize: 10
            font.weight: delegateItem.highlighted ? Font.Bold : Font.Normal
            verticalAlignment: Text.AlignVCenter
            leftPadding: 10
        }
        background: Rectangle {
            color: delegateItem.highlighted ? theme.colors.selected : theme.colors.panel
        }
    }

    indicator: Item {
        x: control.width - width - 10
        y: (control.height - height) / 2
        width: 14
        height: 10
        Canvas {
            id: indicatorCanvas
            anchors.fill: parent
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.beginPath()
                ctx.moveTo(2, 3)
                ctx.lineTo(width / 2, height - 2)
                ctx.lineTo(width - 2, 3)
                ctx.lineWidth = 1.7
                ctx.strokeStyle = control.hovered ? theme.colors.accent : theme.colors.textMuted
                ctx.stroke()
            }
            Connections { target: control; function onHoveredChanged() { indicatorCanvas.requestPaint() } }
        }
    }

    contentItem: Text {
        leftPadding: 0
        rightPadding: 0
        text: control.displayText
        font: control.font
        color: theme.colors.textSecondary
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: 9
        color: control.down ? theme.colors.buttonPressed : (control.hovered ? theme.colors.buttonHover : theme.colors.panelRaised)
        border.width: 1
        border.color: control.activeFocus ? theme.colors.accent : (control.hovered ? theme.colors.borderStrong : theme.colors.border)
        Behavior on color { ColorAnimation { duration: 100 } }
        Behavior on border.color { ColorAnimation { duration: 100 } }
    }

    popup: Popup {
        y: control.height + 5
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 4, 250)
        padding: 2
        background: Rectangle {
            radius: 9
            color: theme.colors.panel
            border.width: 1
            border.color: theme.colors.borderStrong
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollBar.vertical: ThemedScrollBar { }
        }
    }
}
