import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property string scale: "small"
    property var individualItems: []
    property var groups: []
    property var categories: []
    property var activity: ({})

    Loader {
        anchors.fill: parent
        sourceComponent: root.scale === "small" ? smallView : (root.scale === "medium" ? mediumView : largeView)
    }

    Component {
        id: smallView
        GridView {
            clip: true
            cellWidth: 122
            cellHeight: 100
            model: root.individualItems || []
            delegate: ObjectCard {
                required property var modelData
                width: 112
                height: 90
                itemData: modelData
            }
            ScrollBar.vertical: ThemedScrollBar { }
        }
    }

    Component {
        id: mediumView
        ListView {
            clip: true
            spacing: 7
            model: root.groups || []
            delegate: Rectangle {
                required property var modelData
                width: ListView.view.width - 6
                height: 66
                radius: 11
                color: theme.colors.panel
                border.width: 1
                border.color: theme.colors.border
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 10
                    ObjectIcon { assetId: modelData.assetId || "generic"; iconSize: 36 }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        RowLayout {
                            Layout.fillWidth: true
                            Text { Layout.fillWidth: true; text: modelData.label; color: theme.colors.text; font.pixelSize: 10; font.weight: Font.Bold; elide: Text.ElideRight }
                            Text { text: "×" + modelData.count; color: theme.colors.accent; font.pixelSize: 12; font.weight: Font.Bold }
                        }
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 6; radius: 3; color: theme.colors.cardSoft
                            Rectangle { width: parent.width * Number(modelData.fraction || 0); height: parent.height; radius: 3; color: theme.colors.bar }
                        }
                        Text { text: i18n.strings.pending_volume + ": " + modelData.totalSize; color: theme.colors.textSubtle; font.pixelSize: 10 }
                    }
                }
            }
            ScrollBar.vertical: ThemedScrollBar { }
        }
    }

    Component {
        id: largeView
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 74
                    radius: 12
                    color: theme.colors.panelRaised
                    border.width: 1
                    border.color: theme.colors.border
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: i18n.strings.object_progress; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                            Item { Layout.fillWidth: true }
                            Text { text: (root.activity.processedItems || 0) + " / " + (root.activity.totalItems || 0); color: theme.colors.text; font.pixelSize: 10; font.weight: Font.Bold }
                        }
                        Rectangle {
                            Layout.fillWidth: true; Layout.preferredHeight: 9; radius: 5; color: theme.colors.cardSoft
                            Rectangle { width: parent.width * Number(root.activity.processedFraction || 0); height: parent.height; radius: 5; color: theme.colors.accent; Behavior on width { NumberAnimation { duration: 160 } } }
                        }
                        Text { text: (root.activity.pendingItems || 0) + " " + i18n.strings.objects_still_pending; color: theme.colors.textSubtle; font.pixelSize: 10 }
                    }
                }

                Text { text: i18n.strings.pending_by_category; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: root.categories || []
                    delegate: Rectangle {
                        required property var modelData
                        width: ListView.view.width - 6
                        height: 54
                        radius: 10
                        color: theme.colors.panel
                        border.width: 1
                        border.color: theme.colors.border
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 9
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text { text: modelData.label; color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold }
                                Rectangle {
                                    Layout.fillWidth: true; Layout.preferredHeight: 5; radius: 3; color: theme.colors.cardSoft
                                    Rectangle { width: parent.width * Number(modelData.fraction || 0); height: parent.height; radius: 3; color: theme.colors.bar }
                                }
                            }
                            Text { text: modelData.count; color: theme.colors.accent; font.pixelSize: 15; font.weight: Font.Bold }
                        }
                    }
                    ScrollBar.vertical: ThemedScrollBar { }
                }
            }
        }
    }
}
