import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup
    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(860, parent ? parent.width - 80 : 860)
    height: Math.min(720, parent ? parent.height - 70 : 720)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property var histories: []
    property var allHistory: []
    property string selectedHeuristicId: ""
    property var currentRows: []
    property int currentIndex: 0

    function openFor(heuristicId) {
        selectedHeuristicId = heuristicId || ""
        if (!heuristicId) {
            currentRows = allHistory || []
        } else {
            currentRows = []
            for (let i = 0; i < histories.length; ++i) {
                if (histories[i].id === heuristicId) {
                    currentRows = histories[i].decisions || []
                    break
                }
            }
        }
        currentIndex = Math.max(0, currentRows.length - 1)
        open()
    }

    function currentRow() {
        return currentRows && currentRows.length > 0 ? currentRows[Math.min(currentIndex, currentRows.length - 1)] : null
    }

    background: Rectangle { radius: 17; color: theme.colors.cardDark; border.width: 1; border.color: theme.colors.borderStrong }

    contentItem: ColumnLayout {
        spacing: 0
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 70; color: theme.colors.panelRaised; radius: 17
            RowLayout { anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 16
                ColumnLayout { Layout.fillWidth: true; spacing: 1
                    Text { text: i18n.strings.history_title; color: theme.colors.text; font.pixelSize: 17; font.weight: Font.Bold }
                    Text { text: popup.selectedHeuristicId ? (popup.currentRows.length + " · " + (popup.currentRows.length === 1 ? i18n.strings.decision_number : i18n.strings.decision_number)) : i18n.strings.history_all; color: theme.colors.textMuted; font.pixelSize: 10 }
                }
                AppButton { buttonText: i18n.strings.close; minimumButtonWidth: 80; onClicked: popup.close() }
            }
        }

        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
            ScrollBar.vertical: ThemedScrollBar { }
            ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }
            ColumnLayout {
                width: parent.width; spacing: 12
                Text {
                    Layout.leftMargin: 18; Layout.rightMargin: 18; Layout.topMargin: 14; Layout.fillWidth: true
                    text: i18n.strings.selection_history_hint; color: theme.colors.textMuted; font.pixelSize: 10; wrapMode: Text.Wrap
                }

                Flow {
                    Layout.leftMargin: 18; Layout.rightMargin: 18; Layout.fillWidth: true
                    spacing: 4
                    Repeater {
                        model: popup.allHistory || []
                        delegate: Rectangle {
                            required property var modelData; required property int index
                            width: 26; height: 22; radius: 5
                            color: modelData.heuristic_id === "best_fit" ? theme.colors.card : modelData.heuristic_id === "first_fit" ? theme.colors.card : modelData.heuristic_id === "worst_fit" ? theme.colors.card : theme.colors.card
                            border.width: (!popup.selectedHeuristicId && popup.currentRows === popup.allHistory && popup.currentIndex === index) ? 2 : 1
                            border.color: theme.colors.borderStrong
                            Text { anchors.centerIn: parent; text: modelData.heuristicLabel.substring(0, 2); color: theme.colors.text; font.pixelSize: 10; font.weight: Font.Bold }
                            ToolTip.visible: hover.hovered
                            ToolTip.text: i18n.strings.decision_number + " " + modelData.decision + " · " + modelData.heuristicLabel + " · " + modelData.displayName
                            HoverHandler { id: hover }
                            TapHandler { onTapped: { popup.selectedHeuristicId = ""; popup.currentRows = popup.allHistory; popup.currentIndex = index } }
                        }
                    }
                }

                Rectangle {
                    Layout.leftMargin: 18; Layout.rightMargin: 18; Layout.fillWidth: true
                    Layout.preferredHeight: popup.currentRow() ? 330 : 100
                    radius: 13; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 14; spacing: 8
                        Text { visible: !popup.currentRow(); text: i18n.strings.history_no_entries; color: theme.colors.textMuted; font.pixelSize: 11 }
                        RowLayout {
                            visible: Boolean(popup.currentRow()); Layout.fillWidth: true
                            Text { text: popup.currentRow() ? i18n.strings.decision_number + " " + popup.currentRow().decision : ""; color: theme.colors.accent; font.pixelSize: 14; font.weight: Font.Bold }
                            Item { Layout.fillWidth: true }
                            Text { text: popup.currentRow() ? popup.currentRow().heuristicLabel : ""; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                        }
                        Text { visible: Boolean(popup.currentRow()); text: popup.currentRow() ? popup.currentRow().displayName + " · " + i18n.strings.volume_abbr + " " + popup.currentRow().item_size : ""; color: theme.colors.textSecondary; font.pixelSize: 11 }
                        Text { visible: Boolean(popup.currentRow()); text: i18n.strings.history_reasons; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                        Repeater {
                            model: popup.currentRow() ? popup.currentRow().reasons : []
                            delegate: Text { required property var modelData; Layout.fillWidth: true; text: "• " + modelData.question + "  ( +" + Number(modelData.contribution).toFixed(2) + " → " + modelData.heuristicLabel + " )"; color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap }
                        }
                        Text { visible: Boolean(popup.currentRow()); text: i18n.strings.history_scores; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                        RowLayout {
                            visible: Boolean(popup.currentRow()); Layout.fillWidth: true; spacing: 6
                            Repeater {
                                model: popup.currentRow() ? popup.currentRow().scoreRows : []
                                delegate: Rectangle { required property var modelData; Layout.fillWidth: true; Layout.preferredHeight: 38; radius: 8; color: theme.colors.card; border.width: 1; border.color: theme.colors.border; Column { anchors.centerIn: parent; Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.label; color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold }
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: Number(modelData.score).toFixed(2); color: theme.colors.textMuted; font.pixelSize: 10 } } }
                            }
                        }
                        Text { visible: Boolean(popup.currentRow()); text: i18n.strings.history_result; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                        Text { visible: Boolean(popup.currentRow()); text: popup.currentRow() ? popup.currentRow().truckLabel + " · " + popup.currentRow().used_before + " → " + popup.currentRow().used_after : ""; color: theme.colors.textSecondary; font.pixelSize: 10 }
                    }
                }

                RowLayout {
                    Layout.leftMargin: 18; Layout.rightMargin: 18; Layout.bottomMargin: 18; Layout.fillWidth: true
                    AppButton { buttonText: "←"; minimumButtonWidth: 58; enabled: popup.currentIndex > 0; onClicked: popup.currentIndex-- }
                    Item { Layout.fillWidth: true }
                    Text { text: popup.currentRows.length ? (popup.currentIndex + 1) + " / " + popup.currentRows.length : "0 / 0"; color: theme.colors.textMuted; font.pixelSize: 10 }
                    Item { Layout.fillWidth: true }
                    AppButton { buttonText: "→"; minimumButtonWidth: 58; enabled: popup.currentIndex + 1 < popup.currentRows.length; onClicked: popup.currentIndex++ }
                }
            }
        }
    }
}
