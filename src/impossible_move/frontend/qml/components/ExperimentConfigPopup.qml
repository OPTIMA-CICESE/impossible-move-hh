import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: popup

    parent: Overlay.overlay
    modal: true
    focus: true
    width: Math.min(960, parent ? parent.width - 70 : 960)
    height: Math.min(790, parent ? parent.height - 60 : 790)
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    padding: 0
    closePolicy: experiment.resolving ? Popup.NoAutoClose : (Popup.CloseOnEscape | Popup.CloseOnPressOutside)

    background: Rectangle { radius: 18; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.borderStrong }

    Connections {
        target: experiment
        function onViewChanged() {
            if (capacityInput && !capacityInput.activeFocus)
                capacityInput.text = String(experiment.view.capacity || 10)
        }
    }

    contentItem: Item {
        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 76; color: theme.colors.panelRaised; radius: 18
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 22; anchors.rightMargin: 18; spacing: 12
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 1
                        Text { text: i18n.strings.configure_move; color: theme.colors.text; font.pixelSize: 18; font.weight: Font.Bold }
                        Text { text: i18n.strings.configure_move_subtitle; color: theme.colors.textMuted; font.pixelSize: 10 }
                    }
                    AppButton { buttonText: i18n.strings.close; minimumButtonWidth: 80; onClicked: popup.close(); enabled: !experiment.resolving }
                }
            }

            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
                ScrollBar.vertical: ThemedScrollBar { }
                ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }

                ColumnLayout {
                    width: parent.width
                    spacing: 17

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.topMargin: 18; Layout.fillWidth: true; spacing: 7
                        Text { text: i18n.strings.item_count; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                        HelpButton { onClicked: itemCountHelp.open() }
                        Item { Layout.fillWidth: true }
                    }
                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; spacing: 8
                        Repeater {
                            model: experiment.view.supportedItemCounts || []
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true; Layout.preferredHeight: 42; radius: 10
                                color: Number(modelData) === Number(experiment.view.itemCount) ? theme.colors.selected : theme.colors.panelRaised
                                border.width: 1
                                border.color: Number(modelData) === Number(experiment.view.itemCount) ? theme.colors.accent : theme.colors.border
                                Text { anchors.centerIn: parent; text: modelData; color: Number(modelData) === Number(experiment.view.itemCount) ? theme.colors.accent : theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                                MouseArea { anchors.fill: parent; enabled: !experiment.resolving; cursorShape: Qt.PointingHandCursor; onClicked: experiment.setItemCount(Number(modelData)) }
                            }
                        }
                    }

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; spacing: 18
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 8
                            RowLayout {
                                spacing: 7
                                Text { text: i18n.strings.truck_capacity; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                                HelpButton { onClicked: capacityHelp.open() }
                            }
                            RowLayout {
                                spacing: 7
                                AppButton { buttonText: "−"; minimumButtonWidth: 44; onClicked: experiment.setCapacity(Math.max(1, Number(experiment.view.capacity) - 1)); enabled: !experiment.resolving }
                                Rectangle {
                                    Layout.preferredWidth: 96; Layout.preferredHeight: 40; radius: 9; color: theme.colors.track; border.width: 1; border.color: capacityInput.activeFocus ? theme.colors.accent : theme.colors.borderStrong
                                    TextInput {
                                        id: capacityInput
                                        anchors.fill: parent; anchors.margins: 8
                                        text: String(experiment.view.capacity || 10); color: theme.colors.text; font.pixelSize: 14; font.weight: Font.Bold
                                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                                        inputMethodHints: Qt.ImhDigitsOnly; validator: IntValidator { bottom: 1; top: 10000 }
                                        onEditingFinished: { if (acceptableInput) experiment.setCapacity(Number(text)); else text = String(experiment.view.capacity || 10) }
                                    }
                                }
                                AppButton { buttonText: "+"; minimumButtonWidth: 44; onClicked: experiment.setCapacity(Number(experiment.view.capacity) + 1); enabled: !experiment.resolving }
                            }
                            RowLayout {
                                spacing: 6
                                Repeater {
                                    model: experiment.view.capacityPresets || []
                                    delegate: Rectangle {
                                        required property var modelData
                                        implicitWidth: 47; implicitHeight: 27; radius: 8
                                        color: Number(modelData) === Number(experiment.view.capacity) ? theme.colors.selected : theme.colors.panel
                                        border.width: 1; border.color: Number(modelData) === Number(experiment.view.capacity) ? theme.colors.bar : theme.colors.border
                                        Text { anchors.centerIn: parent; text: modelData; color: theme.colors.textMuted; font.pixelSize: 10 }
                                        MouseArea { anchors.fill: parent; enabled: !experiment.resolving; cursorShape: Qt.PointingHandCursor; onClicked: experiment.setCapacity(Number(modelData)) }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 420; Layout.preferredHeight: 126; radius: 13; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 13; spacing: 5
                                Text { text: i18n.strings.potential_space_size; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                                Text { text: i18n.strings.hh_sequences + ":  " + (experiment.view.potentialStatistics ? experiment.view.potentialStatistics.decisionSequencesDisplay : "—"); color: theme.colors.accent; font.pixelSize: 12; font.weight: Font.Bold }
                                Text { text: i18n.strings.theoretical_partitions + ":  " + (experiment.view.potentialStatistics ? experiment.view.potentialStatistics.theoreticalPartitionsDisplay : "—"); color: theme.colors.textSecondary; font.pixelSize: 11 }
                                Text { Layout.fillWidth: true; text: i18n.strings.hh_does_not_enumerate; color: theme.colors.textSubtle; font.pixelSize: 10; wrapMode: Text.Wrap }
                            }
                        }
                    }


                    Rectangle {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true
                        Layout.preferredHeight: 206; radius: 13; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 8
                            RowLayout {
                                Layout.fillWidth: true; spacing: 7
                                Text { text: i18n.strings.corpus_profile; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                                HelpButton { onClicked: profileHelp.open() }
                                Item { Layout.fillWidth: true }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                columns: 2
                                rowSpacing: 8
                                columnSpacing: 8
                                Repeater {
                                    model: experiment.view.profileOptions || []
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumHeight: 72; radius: 9
                                        color: modelData.selected ? theme.colors.selected : theme.colors.panel
                                        border.width: modelData.selected ? 2 : 1
                                        border.color: modelData.selected ? theme.colors.accent : theme.colors.border
                                        ColumnLayout {
                                            anchors.fill: parent; anchors.margins: 10; spacing: 4
                                            Text { Layout.fillWidth: true; text: modelData.label; color: modelData.selected ? theme.colors.accent : theme.colors.textSecondary; font.pixelSize: 11; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter }
                                            Text { Layout.fillWidth: true; Layout.fillHeight: true; text: modelData.description; color: theme.colors.textMuted; font.pixelSize: 10; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; maximumLineCount: 3 }
                                        }
                                        MouseArea {
                                            id: profileMouse
                                            anchors.fill: parent
                                            enabled: !experiment.resolving
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: experiment.setProfile(String(modelData.id))
                                            ToolTip.visible: containsMouse
                                            ToolTip.delay: 350
                                            ToolTip.timeout: 10000
                                            ToolTip.text: modelData.label + "\n\n" + modelData.description
                                        }
                                    }
                                }
                            }
                        }
                    }


                    Rectangle {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true
                        Layout.preferredHeight: 118; radius: 13; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 12; spacing: 7
                            Text { text: i18n.strings.comparison_methods; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                Repeater {
                                    model: experiment.view.policyOptions || []
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true; Layout.preferredHeight: 38; radius: 9
                                        color: modelData.selected ? theme.colors.selected : theme.colors.panel
                                        border.width: modelData.selected ? 2 : 1
                                        border.color: modelData.selected ? theme.colors.accent : theme.colors.border
                                        Row { anchors.centerIn: parent; spacing: 6
                                            Text { text: modelData.selected ? "✓" : "○"; color: modelData.selected ? theme.colors.success : theme.colors.textSubtle; font.pixelSize: 10 }
                                            Text { text: modelData.label; color: modelData.selected ? theme.colors.text : theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.DemiBold }
                                        }
                                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; enabled: !experiment.resolving; onClicked: experiment.setPolicySelected(modelData.id, !modelData.selected) }
                                    }
                                }
                            }
                            RowLayout {
                                visible: (experiment.view.selectedPolicies || []).indexOf("fixed") >= 0
                                spacing: 8
                                Text { text: i18n.strings.fixed_heuristic; color: theme.colors.textMuted; font.pixelSize: 10 }
                                ThemedComboBox {
                                    model: experiment.view.fixedHeuristicOptions || []
                                    textRole: "label"; valueRole: "id"; Layout.preferredWidth: 150
                                    currentIndex: {
                                        const rows = experiment.view.fixedHeuristicOptions || []
                                        for (let i = 0; i < rows.length; ++i) if (rows[i].id === experiment.view.fixedHeuristicId) return i
                                        return 1
                                    }
                                    onActivated: experiment.setFixedHeuristic(String(currentValue))
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; spacing: 7
                        Text { text: i18n.strings.instance; color: theme.colors.textSecondary; font.pixelSize: 12; font.weight: Font.Bold }
                        HelpButton { onClicked: instanceHelp.open() }
                        Text { text: i18n.strings.instance_select_instruction; color: theme.colors.textMuted; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                    }

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true; spacing: 8
                        Repeater {
                            model: experiment.view.candidates || []
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true; Layout.preferredHeight: 104; radius: 12
                                color: modelData.selected ? theme.colors.selected : theme.colors.panel
                                border.width: modelData.selected ? 2 : 1
                                border.color: modelData.selected ? theme.colors.accent : theme.colors.border
                                ColumnLayout {
                                    anchors.fill: parent; anchors.margins: 9; spacing: 3
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Text { text: modelData.label; color: modelData.selected ? theme.colors.accent : theme.colors.text; font.pixelSize: 19; font.weight: Font.Bold }
                                        Item { Layout.fillWidth: true }
                                        Text { visible: modelData.selected; text: "✓"; color: theme.colors.success; font.pixelSize: 13; font.weight: Font.Bold }
                                    }
                                    Text { text: i18n.strings.total_volume; color: theme.colors.textSubtle; font.pixelSize: 10 }
                                    Text { text: modelData.totalSize; color: theme.colors.textSecondary; font.pixelSize: 11; font.weight: Font.Bold }
                                    Text { text: i18n.strings.minimum_trucks + "  " + modelData.lowerBound; color: theme.colors.textSubtle; font.pixelSize: 10 }
                                }
                                MouseArea { anchors.fill: parent; enabled: !experiment.resolving; cursorShape: Qt.PointingHandCursor; onClicked: experiment.selectInstance(Number(modelData.index)) }
                            }
                        }
                    }

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: i18n.strings.selected_instance + ": " + (experiment.view.instanceLabel || "A") + " · " + experiment.view.itemCount + " " + i18n.strings.objects_word + " · " + i18n.strings.truck_capacity.toLowerCase() + " " + experiment.view.capacity
                            color: theme.colors.textMuted; font.pixelSize: 10; elide: Text.ElideRight
                        }
                        AppButton { buttonText: "↻  " + i18n.strings.generate_five; minimumButtonWidth: 164; onClicked: experiment.regenerate(); enabled: !experiment.resolving }
                    }

                    Rectangle {
                        visible: Boolean(experiment.view.error)
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.fillWidth: true
                        Layout.preferredHeight: errorText.implicitHeight + 22; radius: 10; color: theme.colors.card; border.width: 1; border.color: theme.colors.danger
                        Text { id: errorText; anchors.fill: parent; anchors.margins: 11; text: experiment.view.error || ""; color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap }
                    }

                    RowLayout {
                        Layout.leftMargin: 22; Layout.rightMargin: 22; Layout.bottomMargin: 22; Layout.fillWidth: true; spacing: 12
                        Item { Layout.fillWidth: true }
                        AppButton {
                            Layout.preferredWidth: 205
                            buttonText: experiment.resolving ? i18n.strings.resolving : i18n.strings.resolve_move
                            accent: true; enabled: !experiment.resolving; onClicked: experiment.resolveSelected()
                        }
                    }
                }
            }
        }

        Rectangle {
            anchors.fill: parent; visible: experiment.resolving; color: theme.colors.overlay; z: 50; radius: 18
            Column {
                anchors.centerIn: parent; spacing: 10
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: i18n.strings.preparing_move; color: theme.colors.text; font.pixelSize: 18; font.weight: Font.Bold }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: i18n.strings.build_trace; color: theme.colors.textMuted; font.pixelSize: 11 }
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter; width: 260; height: 5; radius: 3; color: theme.colors.track
                    Rectangle {
                        height: parent.height; width: parent.width * 0.36; radius: 3; color: theme.colors.accent
                        SequentialAnimation on x {
                            loops: Animation.Infinite
                            NumberAnimation { from: 0; to: 166; duration: 700; easing.type: Easing.InOutQuad }
                            NumberAnimation { from: 166; to: 0; duration: 700; easing.type: Easing.InOutQuad }
                        }
                    }
                }
            }
        }
    }

    InfoPopup {
        id: profileHelp
        titleText: i18n.strings.corpus_profile_help_title
        introText: i18n.strings.corpus_profile_help_intro
        entries: [
            {"title": i18n.strings.profile_natural, "body": i18n.strings.profile_natural_body},
            {"title": i18n.strings.profile_contrastive, "body": i18n.strings.profile_contrastive_body},
            {"title": i18n.strings.profile_challenge, "body": i18n.strings.profile_challenge_body},
            {"title": i18n.strings.profile_regime, "body": i18n.strings.profile_regime_body}
        ]
    }
    InfoPopup {
        id: itemCountHelp
        titleText: i18n.strings.item_count_help_title
        introText: i18n.strings.item_count_help_body
        entries: []
    }
    InfoPopup {
        id: capacityHelp
        titleText: i18n.strings.capacity_help_title
        introText: i18n.strings.capacity_help_body
        entries: []
    }
    InfoPopup {
        id: instanceHelp
        titleText: i18n.strings.instance_help_title
        introText: i18n.strings.instance_help_intro
        entries: [
            {"title": i18n.strings.instance_volume_title, "body": i18n.strings.instance_volume_body},
            {"title": i18n.strings.instance_bound_title, "body": i18n.strings.instance_bound_body}
        ]
    }
}
