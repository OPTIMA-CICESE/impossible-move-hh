import QtQuick

Item {
    id: root
    property string assetId: "generic"
    property real iconSize: 36

    implicitWidth: iconSize
    implicitHeight: iconSize
    width: iconSize
    height: iconSize

    function assetSource(id) {
        const clean = (id && id.length > 0) ? id : "generic"
        return Qt.resolvedUrl("../assets/objects/" + clean + ".svg")
    }

    Image {
        id: iconImage
        anchors.fill: parent
        source: root.assetSource(root.assetId)
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
        asynchronous: true
        sourceSize.width: Math.max(64, root.iconSize * 2)
        sourceSize.height: Math.max(64, root.iconSize * 2)
    }

    Text {
        anchors.centerIn: parent
        visible: iconImage.status === Image.Error
        text: "◇"
        color: theme.colors.text
        font.pixelSize: root.iconSize * 0.72
        font.weight: Font.Bold
    }
}
