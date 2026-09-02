import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup
    property var entries: []

    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(720, parent ? parent.width - 80 : 720)
    height: Math.min(650, parent ? parent.height - 80 : 650)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    background: Rectangle { radius: 18; color: theme.colors.panel; border.width: 1; border.color: theme.colors.borderStrong }

    contentItem: ColumnLayout {
        spacing: 0
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 72; color: theme.colors.panelRaised; radius: 18
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 16; spacing: 12
                Rectangle {
                    Layout.preferredWidth: 34; Layout.preferredHeight: 34; radius: 17; color: theme.colors.card; border.width: 1; border.color: theme.colors.success
                    Text { anchors.centerIn: parent; text: "?"; color: theme.colors.success; font.pixelSize: 17; font.weight: Font.Bold }
                }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 1
                    Text { Layout.fillWidth: true; text: i18n.strings.how_read_questions; color: theme.colors.text; font.pixelSize: 17; font.weight: Font.Bold; wrapMode: Text.Wrap }
                    Text { Layout.fillWidth: true; text: i18n.strings.questions_help_subtitle; color: theme.colors.textMuted; font.pixelSize: 10; wrapMode: Text.Wrap }
                }
                AppButton { buttonText: i18n.strings.close; minimumButtonWidth: 78; onClicked: popup.close() }
            }
        }

        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
            ScrollBar.vertical: ThemedScrollBar { }
            ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }
            ColumnLayout {
                width: parent.width; spacing: 12
                Rectangle {
                    Layout.leftMargin: 20; Layout.rightMargin: 20; Layout.topMargin: 18; Layout.fillWidth: true
                    Layout.preferredHeight: introText.implicitHeight + 28; radius: 12; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                    Text { id: introText; anchors.fill: parent; anchors.margins: 14; text: i18n.strings.questions_help_intro; color: theme.colors.textSecondary; font.pixelSize: 11; wrapMode: Text.Wrap }
                }
                Repeater {
                    model: popup.entries || []
                    delegate: Rectangle {
                        required property var modelData
                        Layout.leftMargin: 20; Layout.rightMargin: 20; Layout.fillWidth: true
                        Layout.preferredHeight: questionColumn.implicitHeight + 22; radius: 11; color: theme.colors.panel; border.width: 1; border.color: theme.colors.border
                        ColumnLayout {
                            id: questionColumn
                            anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11; spacing: 4
                            Text { Layout.fillWidth: true; text: modelData.question; color: theme.colors.textSecondary; font.pixelSize: 11; font.weight: Font.Bold; wrapMode: Text.Wrap }
                            Text { Layout.fillWidth: true; text: modelData.meaning; color: theme.colors.textMuted; font.pixelSize: 10; wrapMode: Text.Wrap }
                        }
                    }
                }
                Item { Layout.preferredHeight: 10 }
            }
        }
    }
}
