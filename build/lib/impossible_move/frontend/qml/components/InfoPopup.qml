import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup
    property string titleText: ""
    property string introText: ""
    property var entries: []

    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(650, parent ? parent.width - 70 : 650)
    height: Math.min(600, parent ? parent.height - 80 : 600)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    background: Rectangle {
        radius: 18
        color: theme.colors.panelRaised
        border.width: 1
        border.color: theme.colors.borderStrong
    }

    contentItem: ColumnLayout {
        spacing: 0
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 68
            color: theme.colors.panelRaised
            radius: 18
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 14
                Text {
                    Layout.fillWidth: true
                    text: popup.titleText
                    color: theme.colors.text
                    font.pixelSize: 16
                    font.weight: Font.Bold
                    wrapMode: Text.Wrap
                }
                AppButton {
                    buttonText: i18n.strings.close
                    minimumButtonWidth: 78
                    onClicked: popup.close()
                }
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true
            ScrollBar.vertical: ThemedScrollBar { }
            ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }

            ColumnLayout {
                width: parent.width
                spacing: 12
                Text {
                    visible: popup.introText.length > 0
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    Layout.topMargin: 18
                    Layout.fillWidth: true
                    text: popup.introText
                    color: theme.colors.textMuted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                Repeater {
                    model: popup.entries || []
                    delegate: Rectangle {
                        required property var modelData
                        Layout.leftMargin: 20
                        Layout.rightMargin: 20
                        Layout.fillWidth: true
                        Layout.preferredHeight: bodyText.implicitHeight + titleText.implicitHeight + 27
                        radius: 11
                        color: theme.colors.panelRaised
                        border.width: 1
                        border.color: theme.colors.border
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 11
                            spacing: 4
                            Text { id: titleText; Layout.fillWidth: true; text: modelData.title || ""; color: theme.colors.accent; font.pixelSize: 11; font.weight: Font.Bold; wrapMode: Text.Wrap }
                            Text { id: bodyText; Layout.fillWidth: true; text: modelData.body || ""; color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap }
                        }
                    }
                }
                Item { Layout.preferredHeight: 10 }
            }
        }
    }
}
