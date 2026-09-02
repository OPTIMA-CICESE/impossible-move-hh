import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup
    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(690, parent ? parent.width - 70 : 690)
    height: Math.min(650, parent ? parent.height - 70 : 650)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    background: Rectangle { radius: 18; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.borderStrong }

    contentItem: ColumnLayout {
        spacing: 0
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 68; color: theme.colors.panelRaised; radius: 18
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 14
                Text { Layout.fillWidth: true; text: i18n.strings.about_title; color: theme.colors.text; font.pixelSize: 16; font.weight: Font.Bold }
                AppButton { buttonText: i18n.strings.close; minimumButtonWidth: 78; onClicked: popup.close() }
            }
        }
        ScrollView {
            Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
            ScrollBar.vertical: ThemedScrollBar { }
            ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }
            ColumnLayout {
                width: parent.width; spacing: 13
                RowLayout {
                    Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.topMargin: 18; Layout.fillWidth: true
                    Image { source: Qt.resolvedUrl("../assets/branding/optima_full.png"); Layout.preferredWidth: 175; Layout.preferredHeight: 62; fillMode: Image.PreserveAspectFit }
                    Item { Layout.fillWidth: true }
                    Image { source: Qt.resolvedUrl("../assets/branding/cicese.png"); Layout.preferredWidth: 140; Layout.preferredHeight: 55; fillMode: Image.PreserveAspectFit }
                }
                Text { Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; text: i18n.strings.app_name_upper; color: theme.colors.accent; font.pixelSize: 19; font.weight: Font.Bold }
                Text { Layout.leftMargin: 22; text: i18n.strings.public_version; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.DemiBold }
                Text { Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; text: i18n.strings.about_description; color: theme.colors.textSecondary; font.pixelSize: 11; wrapMode: Text.Wrap }

                GridLayout {
                    Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; columns: 2; columnSpacing: 14; rowSpacing: 9
                    Text { text: i18n.strings.author; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text { text: "Ricardo Desales"; color: theme.colors.textSecondary; font.pixelSize: 10 }
                    Text { text: i18n.strings.responsible_professor; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text { text: i18n.strings.responsible_professor_name; color: theme.colors.textSecondary; font.pixelSize: 10 }
                    Text { text: i18n.strings.research_group; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text { text: "OPTIMA · CICESE"; color: theme.colors.textSecondary; font.pixelSize: 10 }
                    Text { text: i18n.strings.license; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text { text: i18n.strings.license_name; color: theme.colors.accent; font.pixelSize: 10; font.weight: Font.Bold }
                }
                Rectangle {
                    Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true
                    Layout.preferredHeight: licenseBody.implicitHeight + 24
                    radius: 11; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                    Text { id: licenseBody; anchors.fill: parent; anchors.margins: 12; text: i18n.strings.license_summary; color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap }
                }
                Text { Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; text: i18n.strings.copyright_holder; color: theme.colors.textSubtle; font.pixelSize: 10; wrapMode: Text.Wrap }
                Item { Layout.preferredHeight: 12 }
            }
        }
    }
}
