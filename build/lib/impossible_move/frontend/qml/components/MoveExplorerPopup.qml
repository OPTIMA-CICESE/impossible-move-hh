import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup
    property var explorerView: ({})
    property string selectedGroupKey: ""
    readonly property bool largeInstance: Number(explorerView.itemCount || 0) > 100

    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(1080, parent ? parent.width - 70 : 1080)
    height: Math.min(790, parent ? parent.height - 70 : 790)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function filteredItems() {
        const rows = explorerView.items || []
        if (!largeInstance || !selectedGroupKey) return largeInstance ? [] : rows
        const result = []
        for (let i = 0; i < rows.length; ++i) {
            const row = rows[i]
            const key = row.assetId || row.category
            if (key === selectedGroupKey) result.push(row)
        }
        return result
    }

    onOpened: selectedGroupKey = ""
    onClosed: comparison.releaseMoveExplorer()

    background: Rectangle { radius: 18; color: theme.colors.panel; border.width: 1; border.color: theme.colors.borderStrong }

    contentItem: ColumnLayout {
        spacing: 0

        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 82; radius: 18; color: theme.colors.panelRaised
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 22; anchors.rightMargin: 18; spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 3
                    Text { text: i18n.strings.move_contents; color: theme.colors.text; font.pixelSize: 20; font.weight: Font.Bold }
                    Text { Layout.fillWidth: true; text: i18n.strings.move_contents_intro; color: theme.colors.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
                AppButton { buttonText: i18n.strings.close; minimumButtonWidth: 88; onClicked: popup.close() }
            }
        }

        RowLayout {
            Layout.fillWidth: true; Layout.leftMargin: 20; Layout.rightMargin: 20; Layout.topMargin: 15; spacing: 9
            Repeater {
                model: [
                    {label: i18n.strings.total_items, value: explorerView.itemCount || 0, accent: false},
                    {label: i18n.strings.processed_items, value: explorerView.decision || 0, accent: false},
                    {label: i18n.strings.remaining_items, value: Math.max(0, Number(explorerView.itemCount || 0) - Number(explorerView.decision || 0)), accent: true},
                    {label: i18n.strings.total_volume, value: explorerView.totalSize || 0, accent: false}
                ]
                delegate: MetricTile { required property var modelData; Layout.fillWidth: true; label: modelData.label; value: String(modelData.value); accent: modelData.accent }
            }
        }

        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; Layout.margins: 20; spacing: 14

            Rectangle {
                Layout.preferredWidth: Math.min(360, popup.width * 0.34)
                Layout.minimumWidth: 280
                Layout.fillHeight: true
                radius: 13; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 13; spacing: 9
                    Text { text: i18n.strings.explorer_all_categories; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                    Text { Layout.fillWidth: true; visible: popup.largeInstance; text: i18n.strings.explorer_select_category; color: theme.colors.textMuted; font.pixelSize: 10; wrapMode: Text.Wrap }
                    ListView {
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7; rightMargin: 12
                        model: explorerView.groups || []
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width - 14; height: 66; radius: 10
                            color: popup.selectedGroupKey === modelData.key ? theme.colors.selected : theme.colors.card
                            border.width: popup.selectedGroupKey === modelData.key ? 2 : 1
                            border.color: popup.selectedGroupKey === modelData.key ? theme.colors.accent : theme.colors.border
                            RowLayout { anchors.fill: parent; anchors.margins: 9; spacing: 9
                                ObjectIcon { assetId: modelData.assetId || "generic"; iconSize: 32 }
                                ColumnLayout { Layout.fillWidth: true; spacing: 2
                                    Text { Layout.fillWidth: true; text: modelData.displayName; color: theme.colors.text; font.pixelSize: 10; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                    Text { text: modelData.processed + " / " + modelData.total + " " + i18n.strings.processed.toLowerCase(); color: theme.colors.textMuted; font.pixelSize: 10 }
                                    Text { text: i18n.strings.total_volume + ": " + modelData.totalSize; color: theme.colors.textSubtle; font.pixelSize: 10 }
                                }
                                Text { text: "×" + modelData.total; color: theme.colors.accent; font.pixelSize: 12; font.weight: Font.Bold }
                            }
                            HoverHandler { id: groupHover }
                            TapHandler { onTapped: popup.selectedGroupKey = modelData.key }
                        }
                        ScrollBar.vertical: ThemedScrollBar { }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true; Layout.fillHeight: true; radius: 13
                color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 13; spacing: 9
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: popup.largeInstance
                                  ? (popup.selectedGroupKey ? i18n.strings.explorer_category_detail : i18n.strings.explorer_select_category)
                                  : i18n.strings.all_items
                            color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold
                        }
                        AppButton {
                            visible: popup.largeInstance && popup.selectedGroupKey !== ""
                            buttonText: i18n.strings.explorer_back_summary
                            minimumButtonWidth: 130; implicitHeight: 34
                            onClicked: popup.selectedGroupKey = ""
                        }
                    }

                    Rectangle {
                        visible: popup.largeInstance && popup.selectedGroupKey === ""
                        Layout.fillWidth: true; Layout.fillHeight: true; radius: 12
                        color: theme.colors.cardDark; border.width: 1; border.color: theme.colors.border
                        Column {
                            anchors.centerIn: parent; width: Math.min(parent.width - 60, 460); spacing: 10
                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "☰"; color: theme.colors.accent; font.pixelSize: 34 }
                            Text { width: parent.width; horizontalAlignment: Text.AlignHCenter; text: i18n.strings.explorer_select_category; color: theme.colors.textSecondary; font.pixelSize: 14; font.weight: Font.DemiBold; wrapMode: Text.Wrap }
                        }
                    }

                    ListView {
                        visible: !popup.largeInstance || popup.selectedGroupKey !== ""
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 7; rightMargin: 12
                        model: popup.filteredItems()
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width - 14; height: 92; radius: 10
                            color: modelData.current ? theme.colors.selected : theme.colors.card
                            border.width: modelData.current ? 2 : 1
                            border.color: modelData.current ? theme.colors.accent : theme.colors.border
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 9; spacing: 6
                                RowLayout {
                                    Layout.fillWidth: true; spacing: 9
                                    Text { Layout.preferredWidth: 22; text: modelData.processed ? "✓" : (modelData.current ? "→" : "○"); color: modelData.processed ? theme.colors.success : (modelData.current ? theme.colors.accent : theme.colors.textSubtle); font.pixelSize: 13; font.weight: Font.Bold }
                                    ObjectIcon { assetId: modelData.assetId || "generic"; iconSize: 30 }
                                    ColumnLayout { Layout.fillWidth: true; spacing: 1
                                        Text { Layout.fillWidth: true; text: modelData.displayName; color: theme.colors.text; font.pixelSize: 11; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                        Text { text: i18n.strings.volume + ": " + modelData.size; color: theme.colors.textMuted; font.pixelSize: 10 }
                                    }
                                    Rectangle {
                                        radius: 7; color: theme.colors.cardDark; border.width: 1; border.color: theme.colors.border
                                        implicitWidth: stateText.implicitWidth + 16; implicitHeight: 25
                                        Text { id: stateText; anchors.centerIn: parent; text: modelData.processed ? i18n.strings.status_processed : (modelData.current ? i18n.strings.status_current : i18n.strings.status_pending); color: modelData.processed ? theme.colors.success : (modelData.current ? theme.colors.accent : theme.colors.textMuted); font.pixelSize: 10; font.weight: Font.Bold }
                                    }
                                }
                                RowLayout {
                                    Layout.fillWidth: true; spacing: 6
                                    Repeater {
                                        model: modelData.placements || []
                                        delegate: Rectangle {
                                            required property var modelData
                                            Layout.fillWidth: true; Layout.preferredHeight: 32; radius: 7
                                            color: theme.colors.cardDark; border.width: 1; border.color: theme.colors.border
                                            RowLayout { anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8; spacing: 5
                                                Text { Layout.fillWidth: true; text: modelData.policyLabel; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold; elide: Text.ElideRight }
                                                Text { text: modelData.binId ? i18n.strings.truck + " " + modelData.binId : "—"; color: modelData.binId ? theme.colors.text : theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.DemiBold }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        ScrollBar.vertical: ThemedScrollBar { }
                    }
                }
            }
        }
    }
}
