import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    property var comparisonView: ({})

    radius: 16
    color: theme.colors.panel
    border.width: 1
    border.color: theme.colors.border

    function pct(value) {
        return Math.round(Number(value || 0) * 100) + "%"
    }

    ScrollView {
        id: comparisonScroll
        anchors.fill: parent
        anchors.margins: 14
        contentWidth: availableWidth
        clip: true
        ScrollBar.vertical: ThemedScrollBar { }
        ScrollBar.horizontal: ThemedScrollBar { policy: ScrollBar.AlwaysOff }

        ColumnLayout {
            width: comparisonScroll.availableWidth
            spacing: 10

            RowLayout {
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        text: i18n.strings.comparison_same_problem
                        color: theme.colors.text
                        font.pixelSize: 15
                        font.weight: Font.Bold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.comparison_same_problem_body
                        color: theme.colors.textMuted
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 195
                    Layout.preferredHeight: 58
                    radius: 11
                    color: currentItemMouse.containsMouse ? theme.colors.selected : theme.colors.card
                    border.width: 1
                    border.color: currentItemMouse.containsMouse ? theme.colors.accent : theme.colors.borderStrong

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        ObjectIcon {
                            assetId: root.comparisonView.currentItem ? root.comparisonView.currentItem.assetId || "generic" : "generic"
                            iconSize: 34
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text {
                                Layout.fillWidth: true
                                text: root.comparisonView.currentItem ? root.comparisonView.currentItem.displayName || "—" : "—"
                                color: theme.colors.text
                                font.pixelSize: 10
                                font.weight: Font.Bold
                                elide: Text.ElideRight
                            }
                            Text {
                                text: root.comparisonView.currentItem && root.comparisonView.currentItem.size
                                      ? i18n.strings.volume_abbr + " " + root.comparisonView.currentItem.size
                                      : ""
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                            }
                            Text {
                                text: i18n.strings.view_move + " ›"
                                color: theme.colors.accent
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                            }
                        }
                    }

                    MouseArea {
                        id: currentItemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            comparison.prepareMoveExplorer()
                            moveExplorer.open()
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 360
                Layout.minimumHeight: 330
                spacing: 9

                Repeater {
                    model: root.comparisonView.methods || []

                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 210
                        radius: 13
                        color: modelData.id === "adaptive" ? theme.colors.selected : theme.colors.panel
                        border.width: 1
                        border.color: modelData.id === "adaptive" ? theme.colors.borderStrong : theme.colors.border

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 11
                            spacing: 7

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                color: modelData.id === "adaptive" ? theme.colors.accent : theme.colors.text
                                font.pixelSize: 13
                                font.weight: Font.Bold
                                wrapMode: Text.Wrap
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.id === "adaptive"
                                      ? i18n.strings.comparison_adaptive_note
                                      : (modelData.id === "random"
                                         ? i18n.strings.comparison_random_note
                                         : i18n.strings.comparison_always_uses.replace("{heuristic}", modelData.fixedHeuristicLabel))
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                                wrapMode: Text.Wrap
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 5

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 56
                                    radius: 9
                                    color: theme.colors.cardDark
                                    Column {
                                        anchors.centerIn: parent
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: i18n.strings.trucks_used
                                            color: theme.colors.textSubtle
                                            font.pixelSize: 10
                                            font.weight: Font.Bold
                                        }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: modelData.binsUsed
                                            color: theme.colors.text
                                            font.pixelSize: 17
                                            font.weight: Font.Bold
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 56
                                    radius: 9
                                    color: theme.colors.cardDark
                                    Column {
                                        anchors.centerIn: parent
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: i18n.strings.utilization
                                            color: theme.colors.textSubtle
                                            font.pixelSize: 10
                                            font.weight: Font.Bold
                                        }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: root.pct(modelData.utilization)
                                            color: theme.colors.textSecondary
                                            font.pixelSize: 14
                                            font.weight: Font.Bold
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 56
                                    radius: 9
                                    color: theme.colors.cardDark
                                    Column {
                                        anchors.centerIn: parent
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: i18n.strings.comparison_gap
                                            color: theme.colors.textSubtle
                                            font.pixelSize: 10
                                            font.weight: Font.Bold
                                        }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: "+" + Math.max(0, Number(modelData.gap))
                                            color: Number(modelData.gap) <= 2 ? theme.colors.success : theme.colors.accent
                                            font.pixelSize: 14
                                            font.weight: Font.Bold
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 54
                                radius: 9
                                color: theme.colors.card
                                border.width: 1
                                border.color: theme.colors.border

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 2
                                    Text {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: i18n.strings.comparison_current_choice
                                        color: theme.colors.textSubtle
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                    }
                                    Text {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: modelData.id === "fixed"
                                              ? modelData.fixedHeuristicLabel
                                              : (modelData.selectedHeuristicLabel || "—")
                                        color: modelData.id === "adaptive" ? theme.colors.accent : theme.colors.textSecondary
                                        font.pixelSize: 11
                                        font.weight: Font.Bold
                                    }
                                }
                            }

                            Text {
                                visible: modelData.id !== "fixed"
                                text: i18n.strings.selection_distribution
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                                font.weight: Font.Bold
                            }

                            ColumnLayout {
                                visible: modelData.id !== "fixed"
                                Layout.fillWidth: true
                                spacing: 3

                                Repeater {
                                    model: modelData.heuristicCounts || []
                                    delegate: RowLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: 4
                                        Text {
                                            Layout.preferredWidth: 58
                                            text: modelData.label
                                            color: theme.colors.textMuted
                                            font.pixelSize: 10
                                            elide: Text.ElideRight
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 5
                                            radius: 3
                                            color: theme.colors.track
                                            Rectangle {
                                                width: parent.width * Number(modelData.fraction || 0)
                                                height: parent.height
                                                radius: 3
                                                color: theme.colors.bar
                                            }
                                        }
                                        Text {
                                            Layout.preferredWidth: 20
                                            text: modelData.count
                                            color: theme.colors.textSecondary
                                            font.pixelSize: 10
                                            horizontalAlignment: Text.AlignRight
                                        }
                                    }
                                }
                            }

                            Text {
                                text: i18n.strings.truck_summary
                                color: theme.colors.textMuted
                                font.pixelSize: 10
                                font.weight: Font.Bold
                            }

                            GridView {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 105
                                Layout.minimumHeight: 80
                                clip: true
                                model: modelData.compactBins || []
                                cellWidth: 31
                                cellHeight: 31

                                delegate: Rectangle {
                                    required property var modelData
                                    width: 26
                                    height: 26
                                    radius: 5
                                    color: theme.colors.card
                                    border.width: 1
                                    border.color: theme.colors.border

                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width
                                        height: parent.height * Number(modelData.utilization || 0)
                                        radius: 5
                                        color: theme.colors.bar
                                        opacity: 0.65
                                    }
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.id + 1
                                        color: theme.colors.text
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                    }
                                }
                                ScrollBar.vertical: ThemedScrollBar { }
                            }
                        }
                    }
                }
            }

            Rectangle {
                visible: Boolean(root.comparisonView.finished
                                 && root.comparisonView.bestFixed
                                 && root.comparisonView.bestFixed.heuristicId)
                Layout.fillWidth: true
                implicitHeight: visible ? benchmarkContent.implicitHeight + 22 : 0
                Layout.preferredHeight: implicitHeight
                radius: 11
                color: theme.colors.card
                border.width: 1
                border.color: theme.colors.borderStrong

                ColumnLayout {
                    id: benchmarkContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 11
                    spacing: 8

                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.best_fixed_benchmark
                        color: theme.colors.textMuted
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        wrapMode: Text.Wrap
                    }

                    Text {
                        Layout.fillWidth: true
                        text: i18n.strings.best_fixed_explanation
                        color: theme.colors.textSecondary
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: width >= 520 ? 2 : 1
                        columnSpacing: 10
                        rowSpacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 62
                            radius: 9
                            color: theme.colors.cardDark
                            border.width: 1
                            border.color: theme.colors.border
                            Column {
                                anchors.centerIn: parent
                                width: parent.width - 16
                                spacing: 2
                                Text {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: root.comparisonView.bestFixed
                                          ? root.comparisonView.bestFixed.heuristicLabel || "—"
                                          : "—"
                                    color: theme.colors.text
                                    font.pixelSize: 11
                                    font.weight: Font.Bold
                                    wrapMode: Text.Wrap
                                }
                                Text {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: (root.comparisonView.bestFixed ? root.comparisonView.bestFixed.bins : "—")
                                          + " " + i18n.strings.trucks_used.toLowerCase()
                                    color: theme.colors.textSecondary
                                    font.pixelSize: 10
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 62
                            radius: 9
                            color: theme.colors.selected
                            border.width: 1
                            border.color: theme.colors.accent
                            Column {
                                anchors.centerIn: parent
                                width: parent.width - 16
                                spacing: 2
                                Text {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: {
                                        const d = Number(root.comparisonView.bestFixed ? root.comparisonView.bestFixed.delta : 0)
                                        return d < 0
                                                ? i18n.strings.adaptive_advantage
                                                : (d > 0 ? i18n.strings.fixed_advantage : i18n.strings.adaptive_tie)
                                    }
                                    color: theme.colors.accent
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                    wrapMode: Text.Wrap
                                }
                                Text {
                                    width: parent.width
                                    horizontalAlignment: Text.AlignHCenter
                                    text: i18n.strings.trucks_difference + ": "
                                          + (root.comparisonView.bestFixed ? root.comparisonView.bestFixed.delta : 0)
                                    color: theme.colors.textSecondary
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 118
                radius: 11
                color: theme.colors.cardDark
                border.width: 1
                border.color: theme.colors.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 4

                    Text {
                        text: i18n.strings.comparison_truck_curve
                        color: theme.colors.textMuted
                        font.pixelSize: 10
                        font.weight: Font.Bold
                    }

                    Canvas {
                        id: curveCanvas
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        property var methods: root.comparisonView.methods || []
                        property int upto: Number(root.comparisonView.decision || 0)

                        onMethodsChanged: requestPaint()
                        onUptoChanged: requestPaint()
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()

                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            const colors = [theme.colors.accent, theme.colors.bar, theme.colors.success]
                            let maxY = 1
                            for (let m = 0; m < methods.length; ++m) {
                                const c = methods[m].curve || []
                                for (let j = 0; j < c.length; ++j)
                                    maxY = Math.max(maxY, c[j])
                            }
                            ctx.strokeStyle = "rgba(90,115,145,0.25)"
                            ctx.lineWidth = 1
                            ctx.beginPath()
                            ctx.moveTo(26, height - 12)
                            ctx.lineTo(width - 8, height - 12)
                            ctx.stroke()

                            for (let m = 0; m < methods.length; ++m) {
                                const curve = methods[m].curve || []
                                const n = Math.min(upto, curve.length)
                                if (!n)
                                    continue
                                ctx.strokeStyle = colors[m % colors.length]
                                ctx.lineWidth = 2
                                ctx.beginPath()
                                for (let i = 0; i < n; ++i) {
                                    const x = 28 + (width - 40) * (i / Math.max(1, root.comparisonView.totalDecisions - 1))
                                    const y = (height - 14) - (height - 22) * (curve[i] / maxY)
                                    if (i === 0)
                                        ctx.moveTo(x, y)
                                    else
                                        ctx.lineTo(x, y)
                                }
                                ctx.stroke()
                            }
                        }
                    }
                }
            }
        }
    }

    MoveExplorerPopup {
        id: moveExplorer
        explorerView: comparison.moveExplorer || ({})
    }
}
