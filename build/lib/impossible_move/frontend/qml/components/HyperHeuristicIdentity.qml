import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property string stateLabel: i18n.strings.hh_flow_state

    radius: 14
    color: theme.colors.panelRaised
    border.width: 1
    border.color: theme.colors.border
    implicitHeight: content.implicitHeight + 26

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 13
        spacing: 7

        // The observed state comes first: this makes the semantic direction
        // explicit instead of trying to fit the whole flow in one row.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            radius: 9
            color: theme.colors.card
            border.width: 1
            border.color: theme.colors.borderStrong

            Text {
                anchors.centerIn: parent
                width: parent.width - 18
                text: i18n.strings.hh_flow_input
                color: theme.colors.textSecondary
                font.pixelSize: 11
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Text {
                Layout.fillWidth: true
                text: i18n.strings.hh_flow_observes
                color: theme.colors.textSubtle
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                Layout.fillWidth: true
                text: "↓"
                color: theme.colors.textSubtle
                font.pixelSize: 15
                font.weight: Font.Bold
                horizontalAlignment: Text.AlignHCenter
            }
        }

        // The HH is the central decision entity.  Identity and explanatory
        // text have independent layout regions, so neither can overlap.
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: identityRow.implicitHeight + 20
            radius: 11
            color: theme.colors.selected
            border.width: 1
            border.color: theme.colors.accent

            RowLayout {
                id: identityRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 14

                ColumnLayout {
                    Layout.preferredWidth: 96
                    Layout.minimumWidth: 96
                    spacing: 4

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 62
                        Layout.preferredHeight: 62
                        radius: 31
                        color: theme.colors.panelRaised
                        border.width: 2
                        border.color: theme.colors.accent

                        Text {
                            anchors.centerIn: parent
                            text: "HH"
                            color: theme.colors.accent
                            font.pixelSize: 20
                            font.weight: Font.Bold
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.hh_entity_role
                        color: theme.colors.textMuted
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 5

                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.hh_entity_name
                        color: theme.colors.text
                        font.pixelSize: 13
                        font.weight: Font.Bold
                        wrapMode: Text.Wrap
                    }

                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.hh_entity_body
                        color: theme.colors.textSecondary
                        font.pixelSize: 11
                        lineHeight: 1.15
                        wrapMode: Text.Wrap
                    }
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Text {
                Layout.fillWidth: true
                text: i18n.strings.hh_flow_selects
                color: theme.colors.textSubtle
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                Layout.fillWidth: true
                text: "↓"
                color: theme.colors.textSubtle
                font.pixelSize: 15
                font.weight: Font.Bold
                horizontalAlignment: Text.AlignHCenter
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            radius: 9
            color: theme.colors.card
            border.width: 1
            border.color: theme.colors.borderStrong

            Column {
                anchors.centerIn: parent
                width: parent.width - 20
                spacing: 3

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: i18n.strings.hh_flow_strategy
                    color: theme.colors.textSecondary
                    font.pixelSize: 11
                    font.weight: Font.Bold
                }
                Text {
                    width: parent.width
                    text: "First Fit · Best Fit · Worst Fit · Next Fit"
                    color: theme.colors.textMuted
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Text {
                Layout.fillWidth: true
                text: i18n.strings.hh_flow_places
                color: theme.colors.textSubtle
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                Layout.fillWidth: true
                text: "↓"
                color: theme.colors.textSubtle
                font.pixelSize: 15
                font.weight: Font.Bold
                horizontalAlignment: Text.AlignHCenter
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            radius: 9
            color: theme.colors.card
            border.width: 1
            border.color: theme.colors.borderStrong

            Text {
                anchors.centerIn: parent
                text: i18n.strings.truck
                color: theme.colors.textSecondary
                font.pixelSize: 11
                font.weight: Font.Bold
            }
        }
    }
}
