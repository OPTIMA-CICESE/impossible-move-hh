import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var hostWindow

    color: theme.colors.titleBar
    border.width: 1
    border.color: theme.colors.border
    implicitHeight: 38

    DragHandler {
        target: null
        acceptedButtons: Qt.LeftButton
        onActiveChanged: if (active) root.hostWindow.startSystemMove()
    }
    TapHandler {
        acceptedButtons: Qt.LeftButton
        onDoubleTapped: {
            if (root.hostWindow.visibility === Window.Maximized) root.hostWindow.showNormal()
            else root.hostWindow.showMaximized()
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        spacing: 8

        Image {
            source: Qt.resolvedUrl("../assets/branding/optima_mark.png")
            Layout.preferredWidth: 25
            Layout.preferredHeight: 25
            sourceSize.width: 25
            sourceSize.height: 25
            fillMode: Image.PreserveAspectFit
        }
        Text {
            text: i18n.strings.app_name
            color: theme.colors.textSecondary
            font.pixelSize: 10
            font.weight: Font.DemiBold
        }

        Item { Layout.fillWidth: true }

        RowLayout {
            spacing: 4
            Text { text: i18n.strings.language; color: theme.colors.textSubtle; font.pixelSize: 10 }
            Rectangle {
                Layout.preferredWidth: 68
                Layout.preferredHeight: 26
                radius: 8
                color: theme.colors.panelRaised
                border.width: 1
                border.color: theme.colors.border
                Row {
                    anchors.centerIn: parent
                    spacing: 2
                    Repeater {
                        model: ["es", "en"]
                        delegate: Rectangle {
                            required property var modelData
                            width: 30; height: 22; radius: 6
                            color: i18n.language === modelData ? theme.colors.selected : "transparent"
                            border.width: i18n.language === modelData ? 1 : 0
                            border.color: theme.colors.accent
                            Text { anchors.centerIn: parent; text: modelData.toUpperCase(); color: i18n.language === modelData ? theme.colors.accent : theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                            MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: i18n.setLanguage(modelData) }
                        }
                    }
                }
            }
        }

        RowLayout {
            spacing: 4
            Text { text: i18n.strings.theme; color: theme.colors.textSubtle; font.pixelSize: 10 }
            Rectangle {
                Layout.preferredWidth: 68; Layout.preferredHeight: 26; radius: 8
                color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                Row {
                    anchors.centerIn: parent; spacing: 2
                    Repeater {
                        model: ["light", "dark"]
                        delegate: Rectangle {
                            required property var modelData
                            width: 30; height: 22; radius: 6
                            color: theme.mode === modelData ? theme.colors.selected : "transparent"
                            border.width: theme.mode === modelData ? 1 : 0
                            border.color: theme.colors.accent
                            Text { anchors.centerIn: parent; text: modelData === "light" ? "☀" : "☾"; color: theme.mode === modelData ? theme.colors.accent : theme.colors.textMuted; font.pixelSize: 11; font.weight: Font.Bold }
                            ToolTip.visible: themeHover.hovered
                            ToolTip.text: modelData === "light" ? i18n.strings.theme_light : i18n.strings.theme_dark
                            HoverHandler { id: themeHover }
                            TapHandler { onTapped: theme.setTheme(modelData) }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: 1; Layout.preferredHeight: 22; color: theme.colors.border
        }

        Button {
            id: minimizeButton
            implicitWidth: 38; implicitHeight: 30; hoverEnabled: true
            ToolTip.visible: hovered; ToolTip.text: i18n.strings.minimize
            contentItem: Text { text: "—"; color: theme.colors.textSecondary; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: minimizeButton.hovered ? theme.colors.buttonHover : "transparent" }
            onClicked: root.hostWindow.showMinimized()
        }
        Button {
            id: maximizeButton
            implicitWidth: 38; implicitHeight: 30; hoverEnabled: true
            ToolTip.visible: hovered; ToolTip.text: root.hostWindow.visibility === Window.Maximized ? i18n.strings.restore : i18n.strings.maximize
            contentItem: Text { text: root.hostWindow.visibility === Window.Maximized ? "❐" : "□"; color: theme.colors.textSecondary; font.pixelSize: 13; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: maximizeButton.hovered ? theme.colors.buttonHover : "transparent" }
            onClicked: root.hostWindow.visibility === Window.Maximized ? root.hostWindow.showNormal() : root.hostWindow.showMaximized()
        }
        Button {
            id: closeButton
            implicitWidth: 44; implicitHeight: 30; hoverEnabled: true
            ToolTip.visible: hovered; ToolTip.text: i18n.strings.close
            contentItem: Text { text: "×"; color: closeButton.hovered ? theme.colors.text : theme.colors.textSecondary; font.pixelSize: 16; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: closeButton.hovered ? theme.colors.danger : "transparent" }
            onClicked: root.hostWindow.close()
        }
    }
}
