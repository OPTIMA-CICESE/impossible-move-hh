import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property string scale: "small"
    property var fullBins: []
    property var compactBins: []
    property var focusedBin: ({})

    function targetPoint(targetItem) {
        if (focusTruckLoader.item && focusTruckLoader.item.cargoPoint)
            return focusTruckLoader.item.cargoPoint(targetItem)
        if (smallTruckList.visible && root.focusedBin && root.focusedBin.id !== undefined) {
            const idx = Number(root.focusedBin.id)
            const truck = smallTruckList.itemAtIndex(idx)
            if (truck && truck.cargoPoint)
                return truck.cargoPoint(targetItem)
        }
        return root.mapToItem(targetItem, root.width * 0.5, root.height * 0.35)
    }

    ListView {
        id: smallTruckList
        anchors.fill: parent
        visible: root.scale === "small"
        spacing: 9
        clip: true
        model: root.fullBins || []
        delegate: TruckCard {
            required property var modelData
            width: smallTruckList.width - 22
            binData: modelData
        }
        ScrollBar.vertical: ThemedScrollBar { id: smallTruckScroll }
        footer: Rectangle {
            width: smallTruckList.width - 22
            height: 104
            radius: 14
            color: theme.colors.track
            border.width: 1
            border.color: theme.colors.card
            visible: smallTruckList.count === 0
            Column {
                anchors.centerIn: parent
                spacing: 6
                Image { anchors.horizontalCenter: parent.horizontalCenter; source: Qt.resolvedUrl("../assets/truck.svg"); width: 90; height: 42; fillMode: Image.PreserveAspectFit; opacity: 0.58 }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: i18n.strings.trucks_appear; color: theme.colors.textSubtle; font.pixelSize: 11 }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        visible: root.scale !== "small"
        spacing: 9

        RowLayout {
            Layout.fillWidth: true
            Text { text: root.scale === "large" ? i18n.strings.focus_truck : i18n.strings.current_truck; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
            Item { Layout.fillWidth: true }
            Text { text: root.compactBins.length + " " + i18n.strings.open_trucks; color: theme.colors.textSubtle; font.pixelSize: 10 }
        }

        Loader {
            id: focusTruckLoader
            Layout.fillWidth: true
            Layout.preferredHeight: 142
            active: root.focusedBin && root.focusedBin.id !== undefined
            sourceComponent: TruckCard {
                width: focusTruckLoader.width
                binData: root.focusedBin
            }
        }

        Rectangle {
            visible: !focusTruckLoader.active
            Layout.fillWidth: true
            Layout.preferredHeight: 108
            radius: 13
            color: theme.colors.track
            border.width: 1
            border.color: theme.colors.card
            Text { anchors.centerIn: parent; text: i18n.strings.trucks_replay; color: theme.colors.textSubtle; font.pixelSize: 10 }
        }

        RowLayout {
            Layout.fillWidth: true
            Text { text: root.scale === "large" ? i18n.strings.global_occupancy_map : i18n.strings.truck_summary; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
            Item { Layout.fillWidth: true }
            Text { visible: root.scale === "large"; text: i18n.strings.cell_one_truck; color: theme.colors.textSubtle; font.pixelSize: 10 }
        }

        GridView {
            id: compactGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.compactBins || []
            cellWidth: root.scale === "large" ? 43 : 108
            cellHeight: root.scale === "large" ? 43 : 66
            delegate: Rectangle {
                required property var modelData
                width: compactGrid.cellWidth - 6
                height: compactGrid.cellHeight - 6
                radius: root.scale === "large" ? 7 : 9
                color: modelData.selected ? theme.colors.card : theme.colors.panelRaised
                border.width: modelData.selected ? 2 : 1
                border.color: modelData.selected ? theme.colors.accent : theme.colors.border

                Rectangle {
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: Math.max(3, parent.height * Number(modelData.utilization || 0))
                    radius: parent.radius
                    color: Number(modelData.utilization || 0) >= 0.95 ? theme.colors.bar : theme.colors.bar
                    opacity: 0.58
                }

                Column {
                    anchors.centerIn: parent
                    spacing: root.scale === "large" ? 0 : 2
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.id + 1; color: theme.colors.text; font.pixelSize: root.scale === "large" ? 9 : 10; font.weight: Font.Bold }
                    Text { visible: root.scale !== "large"; anchors.horizontalCenter: parent.horizontalCenter; text: Math.round(Number(modelData.utilization || 0) * 100) + "%"; color: theme.colors.textMuted; font.pixelSize: 10 }
                    Text { visible: root.scale !== "large"; anchors.horizontalCenter: parent.horizontalCenter; text: modelData.itemCount + " " + i18n.strings.objects_abbr; color: theme.colors.textSubtle; font.pixelSize: 10 }
                }

                ToolTip.visible: hover.hovered
                ToolTip.text: i18n.strings.truck + " " + (modelData.id + 1) + " · " + Math.round(Number(modelData.utilization || 0) * 100) + "% · " + modelData.itemCount + " " + i18n.strings.objects_word
                HoverHandler { id: hover }
            }
            ScrollBar.vertical: ThemedScrollBar { id: compactTruckScroll }
        }
    }
}
