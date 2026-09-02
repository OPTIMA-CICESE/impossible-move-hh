import QtQuick
import QtQuick.Window

Item {
    id: root
    required property var hostWindow
    anchors.fill: parent
    z: 10000
    visible: hostWindow.visibility !== Window.Maximized

    function edgeDrag(edge) { return edge }

    Item {
        width: 5; anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        DragHandler { target: null; cursorShape: Qt.SizeHorCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.LeftEdge) }
    }
    Item {
        width: 5; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        DragHandler { target: null; cursorShape: Qt.SizeHorCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.RightEdge) }
    }
    Item {
        height: 5; anchors.top: parent.top; anchors.left: parent.left; anchors.right: parent.right
        DragHandler { target: null; cursorShape: Qt.SizeVerCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.TopEdge) }
    }
    Item {
        height: 5; anchors.bottom: parent.bottom; anchors.left: parent.left; anchors.right: parent.right
        DragHandler { target: null; cursorShape: Qt.SizeVerCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.BottomEdge) }
    }
    Item {
        width: 8; height: 8; anchors.left: parent.left; anchors.top: parent.top
        DragHandler { target: null; cursorShape: Qt.SizeFDiagCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.LeftEdge | Qt.TopEdge) }
    }
    Item {
        width: 8; height: 8; anchors.right: parent.right; anchors.top: parent.top
        DragHandler { target: null; cursorShape: Qt.SizeBDiagCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.RightEdge | Qt.TopEdge) }
    }
    Item {
        width: 8; height: 8; anchors.left: parent.left; anchors.bottom: parent.bottom
        DragHandler { target: null; cursorShape: Qt.SizeBDiagCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.LeftEdge | Qt.BottomEdge) }
    }
    Item {
        width: 8; height: 8; anchors.right: parent.right; anchors.bottom: parent.bottom
        DragHandler { target: null; cursorShape: Qt.SizeFDiagCursor; onActiveChanged: if (active) root.hostWindow.startSystemResize(Qt.RightEdge | Qt.BottomEdge) }
    }
}
