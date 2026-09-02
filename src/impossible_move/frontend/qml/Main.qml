import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"

ApplicationWindow {
    id: root
    width: Math.min(1580, Screen.desktopAvailableWidth)
    height: Math.min(960, Screen.desktopAvailableHeight)
    minimumWidth: Math.min(1100, Screen.desktopAvailableWidth)
    minimumHeight: Math.min(720, Screen.desktopAvailableHeight)
    visible: true
    title: i18n.strings.app_name
    flags: Qt.Window | Qt.FramelessWindowHint
    color: theme.colors.window

    readonly property bool detailedMode: replay.mode === "detailed"
    readonly property bool comparisonMode: comparison.view && comparison.view.active

    function pct(value) { return Math.round(Number(value || 0) * 100) + "%" }
    function historyFor(heuristicId) {
        const rows = replay.view.heuristicHistories || []
        for (let i = 0; i < rows.length; ++i) if (rows[i].id === heuristicId) return rows[i]
        return {"decisions": [], "count": 0}
    }
    function historyPreview(heuristicId) {
        const h = historyFor(heuristicId)
        if (!h.decisions || h.decisions.length === 0) return i18n.strings.history_no_entries
        let text = h.label + " · " + h.count + "
"
        const start = Math.max(0, h.decisions.length - 3)
        for (let i = start; i < h.decisions.length; ++i) {
            const d = h.decisions[i]
            text += i18n.strings.decision_number + " " + d.decision + " · " + d.displayName + " → " + d.truckLabel
            if (i + 1 < h.decisions.length) text += "
"
        }
        return text
    }

    function featureValue(row) {
        if (!row) return "—"
        const value = Number(row.value || 0)
        if (row.id === "utilization" || row.id === "item_ratio" || row.id === "feasible_ratio" || row.id === "residual_spread")
            return root.pct(value)
        if (row.id === "last_bin_feasible")
            return value > 0.5 ? i18n.strings.yes : (i18n.language === "es" ? "No" : "No")
        return Math.abs(value - Math.round(value)) < 0.00001 ? String(Math.round(value)) : value.toFixed(2)
    }

    header: Column {
        width: parent.width
        height: 114

        TitleBar {
            width: parent.width
            height: 38
            hostWindow: root
        }

        Rectangle {
            width: parent.width
            height: 76
            color: theme.colors.panel
            border.color: theme.colors.card
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                spacing: 14

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Text {
                        text: i18n.strings.app_name_upper
                        color: theme.colors.text
                        font.pixelSize: 23
                        font.weight: Font.Bold
                        font.letterSpacing: 1.0
                    }
                    Text {
                        text: i18n.strings.app_subtitle
                        color: theme.colors.textMuted
                        font.pixelSize: 12
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 184
                    Layout.preferredHeight: 48
                    radius: 12
                    color: root.detailedMode ? theme.colors.button : theme.colors.card
                    border.width: 1
                    border.color: root.detailedMode ? theme.colors.borderStrong : theme.colors.success
                    Column {
                        anchors.centerIn: parent
                        spacing: 1
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: root.comparisonMode ? i18n.strings.comparison_mode : (replay.view.modeInfo ? replay.view.modeInfo.label : i18n.strings.mode_presentation_label); color: root.detailedMode ? theme.colors.textSecondary : theme.colors.success; font.pixelSize: 11; font.weight: Font.Bold }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: root.comparisonMode ? (comparison.view.methodCount + " " + i18n.strings.comparison_methods.toLowerCase()) : (root.detailedMode ? i18n.strings.detailed_view : i18n.strings.presentation_view); color: theme.colors.textMuted; font.pixelSize: 10 }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 176
                    Layout.preferredHeight: 48
                    radius: 12
                    color: theme.colors.panelRaised
                    border.width: 1
                    border.color: replay.status === "finished" ? theme.colors.borderStrong : theme.colors.border
                    Column {
                        anchors.centerIn: parent
                        spacing: 1
                        Text { text: i18n.strings.status; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                        Text { text: root.comparisonMode ? (comparison.view.finished ? i18n.strings.status_finished : i18n.strings.comparison_ready) : (replay.view.statusMessage || i18n.strings.status_ready); color: replay.status === "finished" ? theme.colors.accent : theme.colors.text; font.pixelSize: 11; font.weight: Font.DemiBold }
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.topMargin: 14
        anchors.bottomMargin: 10
        spacing: 11

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            radius: 13
            color: theme.colors.panel
            border.width: 1
            border.color: theme.colors.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 12
                spacing: 12

                ColumnLayout {
                    Layout.preferredWidth: Math.min(252, root.width * 0.18)
                    Layout.minimumWidth: 170
                    spacing: 2
                    Text { text: i18n.strings.selected_move; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: experiment.view.active && experiment.view.active.label ? experiment.view.active.label : i18n.strings.loaded_trace_hint
                        color: theme.colors.text
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }

                Rectangle { width: 1; Layout.fillHeight: true; Layout.topMargin: 10; Layout.bottomMargin: 10; color: theme.colors.border }

                ColumnLayout {
                    Layout.preferredWidth: Math.min(190, root.width * 0.14)
                    Layout.minimumWidth: 135
                    spacing: 2
                    Text { text: i18n.strings.hh_potential_sequences; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text {
                        text: experiment.view.active && experiment.view.active.statistics ? experiment.view.active.statistics.decisionSequencesDisplay : experiment.view.potentialStatistics.decisionSequencesDisplay
                        color: theme.colors.accent; font.pixelSize: 11; font.weight: Font.Bold
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: Math.min(178, root.width * 0.13)
                    Layout.minimumWidth: 125
                    spacing: 2
                    Text { text: i18n.strings.theoretical_groups; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text {
                        text: experiment.view.active && experiment.view.active.statistics ? experiment.view.active.statistics.theoreticalPartitionsDisplay : experiment.view.potentialStatistics.theoreticalPartitionsDisplay
                        color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.DemiBold
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 150
                    spacing: 2
                    Text { text: i18n.strings.this_run; color: theme.colors.textSubtle; font.pixelSize: 10; font.weight: Font.Bold }
                    Text {
                        Layout.fillWidth: true
                        text: experiment.view.active && experiment.view.active.statistics
                              ? experiment.view.active.statistics.heuristicOptionsNotSelected + " " + i18n.strings.strategy_alternatives + " · " + experiment.view.active.statistics.placementEvaluations + " " + i18n.strings.placements_evaluated
                              : i18n.strings.one_trajectory
                        color: theme.colors.textMuted
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }

                AppButton {
                    Layout.preferredWidth: 148
                    Layout.minimumWidth: 136
                    buttonText: "⚙  " + i18n.strings.change_move
                    minimumButtonWidth: 156
                    onClicked: experimentConfig.open()
                }
            }
        }

        ComparisonPanel {
            visible: root.comparisonMode
            Layout.fillWidth: true
            Layout.fillHeight: true
            comparisonView: comparison.view || ({})
        }

        RowLayout {
            visible: !root.comparisonMode
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // LEFT · objetos pendientes y objeto actual
            Rectangle {
                Layout.preferredWidth: Math.min(340, Math.max(250, root.width * 0.215))
                Layout.minimumWidth: 240
                Layout.fillHeight: true
                radius: 16
                color: theme.colors.panel
                border.width: 1
                border.color: theme.colors.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 11

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: i18n.strings.objects_to_move
                            color: theme.colors.text
                            font.pixelSize: 14
                            font.weight: Font.Bold
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            radius: 10
                            color: theme.colors.card
                            implicitWidth: pendingCount.implicitWidth + 18
                            implicitHeight: 25
                            Text {
                                id: pendingCount
                                anchors.centerIn: parent
                                text: ((replay.view.activity && replay.view.activity.pendingItems !== undefined) ? replay.view.activity.pendingItems : 0) + " " + i18n.strings.pending
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: replay.view.currentItem && replay.view.currentItem.id ? 116 : 126
                        radius: 14
                        color: replay.view.currentItem && replay.view.currentItem.id ? theme.colors.cardSoft : theme.colors.panel
                        border.width: replay.view.currentItem && replay.view.currentItem.id ? 2 : 1
                        border.color: replay.view.currentItem && replay.view.currentItem.id ? theme.colors.accent : theme.colors.border

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 13
                            spacing: 12

                            ObjectIcon {
                                id: currentObjectIcon
                                visible: replay.view.currentItem && replay.view.currentItem.id
                                assetId: replay.view.currentItem.assetId || "generic"
                                iconSize: 56
                            }

                            Rectangle {
                                visible: !currentObjectIcon.visible
                                Layout.preferredWidth: 54
                                Layout.preferredHeight: 54
                                radius: 27
                                color: theme.colors.cardSoft
                                border.width: 1
                                border.color: theme.colors.borderStrong
                                Text {
                                    anchors.centerIn: parent
                                    text: replay.status === "finished" ? "✓" : "▶"
                                    color: replay.status === "finished" ? theme.colors.accent : theme.colors.success
                                    font.pixelSize: 22
                                    font.weight: Font.Bold
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Text {
                                    text: replay.view.currentItem && replay.view.currentItem.id ? i18n.strings.current_object : i18n.strings.simulation
                                    color: replay.view.currentItem && replay.view.currentItem.id ? theme.colors.accent : theme.colors.success
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: replay.view.currentItem && replay.view.currentItem.id
                                          ? replay.view.currentItem.displayName
                                          : (replay.view.statusMessage || i18n.strings.status_ready)
                                    color: theme.colors.text
                                    font.pixelSize: 16
                                    font.weight: Font.Bold
                                    elide: Text.ElideRight
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: replay.view.currentItem && replay.view.currentItem.id
                                          ? i18n.strings.volume + ": " + replay.view.currentItem.size + " / " + replay.view.binCapacity
                                          : (replay.status === "finished"
                                             ? i18n.strings.final_solution_ready
                                             : i18n.strings.press_play_first)
                                    color: theme.colors.textMuted
                                    font.pixelSize: 10
                                    wrapMode: Text.Wrap
                                }
                            }
                        }
                    }

                    AdaptivePendingView {
                        id: adaptivePendingView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        scale: replay.view.presentationScale || "small"
                        individualItems: replay.view.pendingItems || []
                        groups: replay.view.pendingGroups || []
                        categories: replay.view.categoryGroups || []
                        activity: replay.view.activity || ({})
                    }
                }
            }

            // CENTER · fenómeno físico de la mudanza + métricas
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 350
                radius: 16
                color: theme.colors.panel
                border.width: 1
                border.color: theme.colors.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: i18n.strings.moving_trucks
                            color: theme.colors.text
                            font.pixelSize: 14
                            font.weight: Font.Bold
                        }
                        Item { Layout.fillWidth: true }
                        Rectangle {
                            radius: 8
                            color: theme.colors.card
                            border.width: 1
                            border.color: theme.colors.border
                            implicitWidth: scaleLabel.implicitWidth + 16
                            implicitHeight: 24
                            Text { id: scaleLabel; anchors.centerIn: parent; text: replay.view.presentationScaleLabel || i18n.strings.scale_small; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold }
                        }
                        Text {
                            text: replay.view.binCapacity > 0 ? i18n.strings.capacity_per_truck + ": " + replay.view.binCapacity : i18n.strings.truck_capacity
                            color: theme.colors.textMuted
                            font.pixelSize: 11
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        MetricTile {
                            Layout.fillWidth: true
                            label: i18n.strings.trucks_used
                            value: String(replay.view.summary.binsUsed || 0)
                            accent: true
                        }
                        MetricTile {
                            Layout.fillWidth: true
                            label: i18n.strings.utilization
                            value: root.pct(replay.view.summary.utilization)
                        }
                        MetricTile {
                            Layout.fillWidth: true
                            label: i18n.strings.lower_bound
                            value: replay.view.summary.lowerBound > 0 ? "≥ " + replay.view.summary.lowerBound : "—"
                            helpVisible: true
                            onHelpRequested: lowerBoundHelp.open()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        radius: 10
                        color: theme.colors.panel
                        border.width: 1
                        border.color: theme.colors.border

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 9
                            Text {
                                text: i18n.strings.key_idea
                                color: theme.colors.accent
                                font.pixelSize: 10
                                font.weight: Font.Bold
                            }
                            Text {
                                Layout.fillWidth: true
                                text: replay.view.summary.finished
                                      ? i18n.strings.key_idea_finished
                                      : i18n.strings.key_idea_running
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                                wrapMode: Text.Wrap
                            }
                        }
                    }

                    AdaptiveTruckView {
                        id: adaptiveTruckView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        scale: replay.view.presentationScale || "small"
                        fullBins: replay.view.bins || []
                        compactBins: replay.view.compactBins || []
                        focusedBin: replay.view.focusedBin || ({})
                    }
                }
            }

            // RIGHT · inteligencia / hiper-heurística
            Rectangle {
                Layout.preferredWidth: Math.min(500, Math.max(360, root.width * 0.295))
                Layout.minimumWidth: 350
                Layout.fillHeight: true
                radius: 16
                color: theme.colors.panel
                border.width: 1
                border.color: theme.colors.border

                ScrollView {
                    anchors.fill: parent
                    contentWidth: availableWidth
                    clip: true
                    ScrollBar.vertical: ThemedScrollBar { }
                    ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }

                    ColumnLayout {
                        width: parent.width
                        spacing: 12

                        RowLayout {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.topMargin: 15
                            Layout.fillWidth: true
                            Text {
                                text: i18n.strings.who_is_deciding
                                color: theme.colors.text
                                font.pixelSize: 14
                                font.weight: Font.Bold
                            }
                            Item { Layout.fillWidth: true }
                        }

                        HyperHeuristicIdentity {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            Text {
                                text: i18n.strings.how_hh_decides
                                color: theme.colors.text
                                font.pixelSize: 12
                                font.weight: Font.Bold
                            }
                            Item { Layout.fillWidth: true }
                        }

                        Rectangle {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            Layout.preferredHeight: 132
                            radius: 14
                            color: theme.colors.panelRaised
                            border.width: 1
                            border.color: replay.view.selectedHeuristicId ? theme.colors.accent : theme.colors.border

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 13
                                spacing: 5

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: i18n.strings.current_decision
                                        color: theme.colors.textMuted
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        text: replay.view.decisionCount > 0 ? i18n.strings.decision_number + " " + replay.view.decisionCount + " / " + replay.view.decisionTotal : i18n.strings.start
                                        color: theme.colors.textSubtle
                                        font.pixelSize: 10
                                    }
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: replay.view.selectedHeuristicLabel || (replay.status === "finished" ? i18n.strings.move_finished : i18n.strings.no_strategy)
                                    color: replay.view.selectedHeuristicId ? theme.colors.accent : theme.colors.textSecondary
                                    font.pixelSize: 19
                                    font.weight: Font.Bold
                                    wrapMode: Text.Wrap
                                }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    text: replay.view.decisionNarrative || ""
                                    color: theme.colors.textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.Wrap
                                    verticalAlignment: Text.AlignTop
                                }
                            }
                        }

                        RowLayout {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            spacing: 7
                            Text {
                                text: i18n.strings.how_read_questions
                                color: theme.colors.textSecondary
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                            }
                            HelpButton { diameter: 24; onClicked: ruleHelp.open() }
                            Item { Layout.fillWidth: true }
                        }

                        DecisionGraph {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            Layout.preferredHeight: implicitHeight
                            reasons: replay.view.decisionGraphReasons || []
                            scores: replay.view.heuristicScores || []
                            selectedHeuristicId: replay.view.selectedHeuristicId || ""
                        }

                        // The following sections intentionally only exist in Detailed mode.
                        Rectangle {
                            visible: root.detailedMode
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            height: 1
                            color: theme.colors.card
                        }

                        Text {
                            visible: root.detailedMode && replay.view.featureDetailsAvailable
                            Layout.leftMargin: 16
                            text: i18n.strings.observed_features
                            color: theme.colors.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }

                        GridLayout {
                            visible: root.detailedMode && replay.view.featureDetailsAvailable
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 7
                            rowSpacing: 7

                            Repeater {
                                model: replay.view.featureRows || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 48
                                    radius: 9
                                    color: theme.colors.panel
                                    border.width: 1
                                    border.color: theme.colors.border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 6
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.label
                                            color: theme.colors.textMuted
                                            font.pixelSize: 10
                                            wrapMode: Text.Wrap
                                        }
                                        Text {
                                            text: root.featureValue(modelData)
                                            color: theme.colors.textSecondary
                                            font.pixelSize: 10
                                            font.weight: Font.Bold
                                        }
                                    }
                                }
                            }
                        }

                        Text {
                            visible: root.detailedMode
                            Layout.leftMargin: 16
                            text: i18n.strings.decision_scores
                            color: theme.colors.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }

                        ColumnLayout {
                            visible: root.detailedMode
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            spacing: 0
                            Repeater {
                                model: replay.view.heuristicScores || []
                                delegate: ScoreBar {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    scoreData: modelData
                                }
                            }
                        }

                        Text {
                            visible: root.detailedMode
                            Layout.leftMargin: 16
                            text: i18n.strings.active_rules
                            color: theme.colors.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }

                        ColumnLayout {
                            visible: root.detailedMode
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            spacing: 6

                            Repeater {
                                model: replay.view.decisionReasons || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 46
                                    radius: 9
                                    color: theme.colors.panelRaised
                                    border.width: 1
                                    border.color: theme.colors.border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 8
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.ruleLabel
                                            color: theme.colors.textSecondary
                                            font.pixelSize: 10
                                            wrapMode: Text.Wrap
                                        }
                                        Text {
                                            text: modelData.heuristicLabel + "  +" + Number(modelData.contribution).toFixed(2)
                                            color: theme.colors.accent
                                            font.pixelSize: 10
                                            font.weight: Font.Bold
                                        }
                                    }
                                }
                            }
                        }

                        Text {
                            visible: root.detailedMode && replay.view.placementDetailsAvailable
                            Layout.leftMargin: 16
                            text: i18n.strings.truck_evaluation
                            color: theme.colors.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }

                        ColumnLayout {
                            visible: root.detailedMode && replay.view.placementDetailsAvailable
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.fillWidth: true
                            spacing: 5

                            Repeater {
                                model: replay.view.placementEvaluations || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 40
                                    radius: 8
                                    color: modelData.selected ? theme.colors.card : theme.colors.panel
                                    border.width: modelData.selected ? 2 : 1
                                    border.color: modelData.selected ? theme.colors.accent : theme.colors.border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 9
                                        anchors.rightMargin: 9
                                        spacing: 7
                                        Text { text: modelData.binLabel; color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold }
                                        Text {
                                            text: modelData.feasible ? i18n.strings.feasible : i18n.strings.does_not_fit
                                            color: modelData.feasible ? theme.colors.success : theme.colors.danger
                                            font.pixelSize: 10
                                        }
                                        Item { Layout.fillWidth: true }
                                        Text {
                                            text: modelData.feasible ? i18n.strings.free + ": " + modelData.remainingBefore + " → " + modelData.remainingAfter : i18n.strings.free + ": " + modelData.remainingBefore
                                            color: theme.colors.textMuted
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                            }

                            Text {
                                visible: !replay.view.placementEvaluations || replay.view.placementEvaluations.length === 0
                                text: i18n.strings.evaluations_placeholder
                                color: theme.colors.textSubtle
                                font.pixelSize: 10
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                        }

                        Text {
                            Layout.leftMargin: 16
                            Layout.topMargin: 3
                            text: i18n.strings.selection_distribution
                            color: theme.colors.textSecondary
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                        }

                        ColumnLayout {
                            Layout.leftMargin: 16
                            Layout.rightMargin: 16
                            Layout.bottomMargin: 17
                            Layout.fillWidth: true
                            spacing: 7

                            Text {
                                Layout.fillWidth: true
                                text: i18n.strings.selection_history_hint
                                color: theme.colors.textSubtle
                                font.pixelSize: 10
                                wrapMode: Text.Wrap
                            }
                            Repeater {
                                model: replay.view.heuristicCounts || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 27
                                    radius: 7
                                    color: historyHover.hovered ? theme.colors.selected : "transparent"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 3
                                        anchors.rightMargin: 3
                                        spacing: 7
                                        Text { Layout.preferredWidth: 72; text: modelData.label; color: theme.colors.textSecondary; font.pixelSize: 10; elide: Text.ElideRight }
                                        Rectangle {
                                            Layout.fillWidth: true; Layout.preferredHeight: 8; radius: 4; color: theme.colors.track
                                            Rectangle { height: parent.height; width: parent.width * Number(modelData.fraction || 0); radius: 4; color: historyHover.hovered ? theme.colors.bar : theme.colors.bar; Behavior on width { NumberAnimation { duration: 180 } } }
                                        }
                                        Text { Layout.preferredWidth: 26; text: modelData.count; color: theme.colors.textSecondary; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                                    }
                                    HoverHandler { id: historyHover }
                                    TapHandler { onTapped: decisionHistoryPopup.openFor(modelData.id) }
                                    ToolTip.visible: historyHover.hovered
                                    ToolTip.text: root.historyPreview(modelData.id)
                                    ToolTip.delay: 280
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            visible: !root.comparisonMode && replay.view.presentationScale === "large" && replay.view.interestingInfo && replay.view.interestingInfo.visible
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            radius: 12
            color: theme.colors.cardSoft
            border.width: 1
            border.color: theme.colors.borderStrong
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 13
                anchors.rightMargin: 13
                spacing: 10
                Text { text: "★"; color: theme.colors.accent; font.pixelSize: 15 }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Text {
                        text: i18n.strings.relevant_decision + " · " + Number(replay.view.interestingInfo.skippedDecisions || 0) + " " + i18n.strings.skipped_decisions
                        color: theme.colors.accent; font.pixelSize: 10; font.weight: Font.Bold
                    }
                    Text { text: i18n.strings.why_relevant + " " + (replay.view.interestingInfo.reason || ""); color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 78
            radius: 15
            color: theme.colors.panel
            border.width: 1
            border.color: theme.colors.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 7

                AppButton { buttonText: (root.comparisonMode ? comparison.view.playing : replay.playing) ? "❚❚  " + i18n.strings.pause : "▶  " + i18n.strings.play; accent: true; minimumButtonWidth: 112; onClicked: root.comparisonMode ? comparison.togglePlayback() : replay.togglePlayback() }
                AppButton { visible: !root.comparisonMode; buttonText: i18n.strings.single_step; minimumButtonWidth: 70; onClicked: replay.step() }
                AppButton { buttonText: i18n.strings.decision; minimumButtonWidth: 82; onClicked: root.comparisonMode ? comparison.nextDecision() : replay.nextDecision() }
                AppButton {
                    visible: !root.comparisonMode && replay.view.presentationScale === "large" // visible: replay.view.presentationScale === "large"
                    buttonText: "★ " + i18n.strings.next_relevant
                    minimumButtonWidth: 194
                    onClicked: replay.nextInteresting()
                }
                AppButton { buttonText: i18n.strings.final; minimumButtonWidth: 66; onClicked: root.comparisonMode ? comparison.jumpToEnd() : replay.jumpToEnd() }
                AppButton { buttonText: i18n.strings.restart; minimumButtonWidth: 88; onClicked: root.comparisonMode ? comparison.reset() : replay.reset() }
                HelpButton { diameter: 27; onClicked: controlsHelp.open() }

                Item { Layout.preferredWidth: 4 }

                ColumnLayout {
                    spacing: 2
                    Text { text: i18n.strings.speed; color: theme.colors.textMuted; font.pixelSize: 10 }
                    ThemedComboBox {
                        id: speedBox
                        model: replay.view.speedOptions || []
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: {
                            const rows = replay.view.speedOptions || []
                            for (let i = 0; i < rows.length; ++i)
                                if (Number(rows[i].value) === Number(root.comparisonMode ? comparison.view.speed : replay.speed)) return i
                            return 0
                        }
                        Layout.preferredWidth: 92
                        onActivated: root.comparisonMode ? comparison.setSpeed(Number(currentValue)) : replay.setSpeed(Number(currentValue))
                    }
                }

                ColumnLayout {
                    visible: !root.comparisonMode
                    spacing: 2
                    RowLayout {
                        spacing: 4
                        Text { text: i18n.strings.view; color: theme.colors.textMuted; font.pixelSize: 10 }
                        HelpButton { diameter: 20; onClicked: viewHelp.open() }
                    }
                    ThemedComboBox {
                        model: [i18n.strings.presentation_view, i18n.strings.detailed_view]
                        currentIndex: replay.mode === "presentation" ? 0 : 1
                        Layout.preferredWidth: 126
                        onActivated: replay.setMode(currentIndex === 0 ? "presentation" : "detailed")
                    }
                }

                Item { Layout.fillWidth: true }

                ColumnLayout {
                    Layout.preferredWidth: 190
                    spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: root.comparisonMode ? (comparison.view.decision > 0 ? i18n.strings.decision_number + " " + comparison.view.decision + " / " + comparison.view.totalDecisions : i18n.strings.start) : (replay.view.decisionCount > 0 ? (replay.view.summary.finished ? i18n.strings.decisions_completed.replace("{count}", replay.view.decisionCount) : i18n.strings.decision_number + " " + replay.view.decisionCount + " / " + replay.view.decisionTotal) : i18n.strings.start); color: theme.colors.textSecondary; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: Math.round(Number(root.comparisonMode ? comparison.view.progress : replay.view.decisionProgress || 0) * 100) + "%"; color: theme.colors.text; font.pixelSize: 10; font.weight: Font.Bold }
                    }
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 7; radius: 4; color: theme.colors.track
                        Rectangle { height: parent.height; width: parent.width * Number(root.comparisonMode ? comparison.view.progress : replay.view.decisionProgress || 0); radius: 4; color: theme.colors.accent; Behavior on width { NumberAnimation { duration: 160 } } }
                    }
                }
            }
        }

        // Institutional footer / branding.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            radius: 12
            color: theme.colors.titleBar
            border.width: 1
            border.color: theme.colors.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 10

                Image {
                    source: Qt.resolvedUrl("assets/branding/optima_mark.png")
                    sourceSize.width: 34
                    sourceSize.height: 34
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }
                ColumnLayout {
                    spacing: -1
                    Text { text: "OPTIMA Research Group"; color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold }
                    Text { text: "Optimization, Intelligence and Multiobjective Algorithms"; color: theme.colors.textSubtle; font.pixelSize: 10 }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: i18n.strings.outreach_activity
                    color: theme.colors.textSubtle
                    font.pixelSize: 10
                }

                AppButton {
                    buttonText: "?  " + i18n.strings.instructions
                    minimumButtonWidth: 112
                    implicitHeight: 34
                    onClicked: instructionsPopup.open()
                }

                AppButton {
                    buttonText: "ⓘ  " + i18n.strings.about
                    minimumButtonWidth: 92
                    implicitHeight: 34
                    onClicked: aboutPopup.open()
                }

                Image {
                    source: Qt.resolvedUrl("assets/branding/cicese.png")
                    sourceSize.width: 118
                    sourceSize.height: 42
                    Layout.preferredWidth: 118
                    Layout.preferredHeight: 38
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }
        }
    }

    RuleHelpPopup {
        id: ruleHelp
        entries: replay.view.ruleLegend || []
    }

    ExperimentConfigPopup {
        id: experimentConfig
    }

    AboutPopup { id: aboutPopup }

    InfoPopup {
        id: instructionsPopup
        titleText: i18n.strings.instructions_title
        introText: i18n.strings.instructions_intro
        entries: [
            {"title": i18n.strings.instructions_goal_title, "body": i18n.strings.instructions_goal_body},
            {"title": i18n.strings.instructions_config_title, "body": i18n.strings.instructions_config_body},
            {"title": i18n.strings.instructions_methods_title, "body": i18n.strings.instructions_methods_body},
            {"title": i18n.strings.instructions_solve_title, "body": i18n.strings.instructions_solve_body},
            {"title": i18n.strings.instructions_hh_title, "body": i18n.strings.instructions_hh_body},
            {"title": i18n.strings.instructions_compare_title, "body": i18n.strings.instructions_compare_body},
            {"title": i18n.strings.instructions_explore_title, "body": i18n.strings.instructions_explore_body}
        ]
    }

    DecisionHistoryPopup {
        id: decisionHistoryPopup
        histories: replay.view.heuristicHistories || []
        allHistory: replay.view.decisionHistory || []
    }

    InfoPopup {
        id: viewHelp
        titleText: i18n.strings.view_help_title
        introText: i18n.strings.view_help_intro
        entries: [
            {"title": i18n.strings.view_help_presentation_title, "body": i18n.strings.view_help_presentation_body},
            {"title": i18n.strings.view_help_detailed_title, "body": i18n.strings.view_help_detailed_body}
        ]
    }

    InfoPopup {
        id: lowerBoundHelp
        titleText: i18n.strings.lower_bound_help_title
        introText: i18n.strings.lower_bound_help_intro
        entries: [
            {
                "title": i18n.strings.lower_bound_formula_title,
                "body": i18n.strings.lower_bound_formula_body
                    .replace("{volume}", String(replay.view.summary.totalItemSize || 0))
                    .replace("{capacity}", String(replay.view.binCapacity || 0))
                    .replace("{bound}", String(replay.view.summary.lowerBound || 0))
            },
            {
                "title": i18n.strings.lower_bound_meaning_title,
                "body": i18n.strings.lower_bound_meaning_body
                    .replace("{bound}", String(replay.view.summary.lowerBound || 0))
            },
            {
                "title": i18n.strings.lower_bound_caveat_title,
                "body": i18n.strings.lower_bound_caveat_body
            }
        ]
    }

    InfoPopup {
        id: controlsHelp
        titleText: i18n.strings.controls_help_title
        introText: i18n.strings.controls_help_intro
        entries: [
            {"title": i18n.strings.control_play_title, "body": i18n.strings.control_play_body},
            {"title": i18n.strings.control_step_title, "body": i18n.strings.control_step_body},
            {"title": i18n.strings.control_decision_title, "body": i18n.strings.control_decision_body},
            {"title": i18n.strings.control_relevant_title, "body": i18n.strings.control_relevant_body},
            {"title": i18n.strings.control_final_title, "body": i18n.strings.control_final_body},
            {"title": i18n.strings.control_restart_title, "body": i18n.strings.control_restart_body}
        ]
    }

    Connections {
        target: experiment
        function onRunReady() { experimentConfig.close() }
    }

    Item {
        id: animationOverlay
        anchors.fill: parent
        z: 2000

        FlyingObject {
            id: flyingObject
            anchors.fill: parent
            replaySpeed: replay.speed
        }
    }

    Connections {
        target: replay

        function onFrameAdvanced(frame) {
            if (!frame || frame.type !== "place_item" || !frame.item)
                return

            const sourcePoint = currentObjectIcon.mapToItem(
                        animationOverlay,
                        currentObjectIcon.width / 2,
                        currentObjectIcon.height / 2)

            let targetX = animationOverlay.width * 0.52
            let targetY = animationOverlay.height * 0.50
            const cargoPoint = adaptiveTruckView.targetPoint(animationOverlay)
            if (cargoPoint) {
                targetX = cargoPoint.x
                targetY = cargoPoint.y
            }

            flyingObject.fly(frame.item, sourcePoint.x, sourcePoint.y, targetX, targetY)
        }
    }

    WindowResizeHandles { hostWindow: root }

}
