import QtQuick
import QtQuick.Controls

Item {
    id: root
    property var reasons: []
    property var scores: []
    property string selectedHeuristicId: ""
    property real animationPhase: 0
    readonly property real outerPadding: 4
    readonly property real columnGap: Math.max(10, Math.min(18, width * 0.035))
    readonly property real strategyWidth: Math.max(92, Math.min(118, width * 0.22))
    readonly property real strategyX: Math.max(outerPadding, width - outerPadding - strategyWidth)
    readonly property real questionWidth: Math.max(112, Math.min(190, width * 0.34))
    readonly property real questionX: outerPadding
    readonly property real evidenceX: questionX + questionWidth + columnGap
    readonly property real evidenceWidth: Math.max(72, strategyX - evidenceX - columnGap)

    implicitHeight: Math.max(300, 86 + Math.max(1, reasons ? reasons.length : 0) * 58)
    clip: true

    function heuristicIndex(heuristicId) {
        if (!scores) return -1
        for (let i = 0; i < scores.length; ++i) if (scores[i].id === heuristicId) return i
        return -1
    }
    function questionY(index) { return 52 + index * 58 + 22 }
    function heuristicY(index) {
        const usable = Math.max(190, height - 92)
        return 64 + (index + 0.5) * (usable / Math.max(1, scores ? scores.length : 1))
    }

    onReasonsChanged: graphCanvas.requestPaint()
    onScoresChanged: graphCanvas.requestPaint()
    onSelectedHeuristicIdChanged: graphCanvas.requestPaint()
    onAnimationPhaseChanged: graphCanvas.requestPaint()
    onWidthChanged: graphCanvas.requestPaint()
    onHeightChanged: graphCanvas.requestPaint()
    NumberAnimation on animationPhase { from: 0; to: 1; duration: 1200; loops: Animation.Infinite }

    Text { id: qHeader; x: root.questionX + (root.questionWidth - width) / 2; y: 6; text: i18n.strings.questions; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 0.8 }
    Text { id: eHeader; x: root.evidenceX + (root.evidenceWidth - width) / 2; y: 6; text: i18n.strings.evidence; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 0.8 }
    Text { id: sHeader; x: root.strategyX + (root.strategyWidth - width) / 2; y: 6; text: i18n.strings.strategies; color: theme.colors.textMuted; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 0.8 }

    Canvas {
        id: graphCanvas; anchors.fill: parent; antialiasing: true
        onPaint: {
            const ctx = getContext("2d"); ctx.clearRect(0, 0, width, height)
            if (!root.reasons || !root.scores) return
            const qRight = root.questionX + root.questionWidth
            const evLeft = root.evidenceX
            const evRight = root.evidenceX + root.evidenceWidth
            const hLeft = root.strategyX
            const pulse = 0.45 + 0.45 * Math.sin(root.animationPhase * Math.PI)
            for (let i = 0; i < root.reasons.length; ++i) {
                const reason = root.reasons[i]; const hi = root.heuristicIndex(reason.heuristicId); if (hi < 0) continue
                const y = root.questionY(i); const hy = root.heuristicY(hi); const active = reason.heuristicId === root.selectedHeuristicId
                ctx.beginPath(); ctx.moveTo(qRight, y); ctx.lineTo(evLeft, y); ctx.lineWidth = active ? 2.4 : 1.2; ctx.strokeStyle = active ? "rgba(246,196,83," + (0.72 + 0.22 * pulse) + ")" : "rgba(95,134,181,0.45)"; ctx.stroke()
                ctx.beginPath(); ctx.moveTo(evRight, y); ctx.bezierCurveTo(evRight + root.columnGap * 0.55, y, hLeft - root.columnGap * 1.4, hy, hLeft, hy); ctx.lineWidth = active ? 2.8 : 1.4; ctx.strokeStyle = active ? "rgba(246,196,83," + (0.72 + 0.22 * pulse) + ")" : "rgba(95,134,181,0.45)"; ctx.stroke()
                ctx.beginPath(); ctx.moveTo(hLeft, hy); ctx.lineTo(hLeft - 7, hy - 4); ctx.lineTo(hLeft - 7, hy + 4); ctx.closePath(); ctx.fillStyle = active ? "rgba(246,196,83,0.94)" : "rgba(95,134,181,0.60)"; ctx.fill()
            }
        }
    }

    Repeater {
        model: root.reasons || []
        delegate: Rectangle {
            required property var modelData; required property int index; property bool pinned: false
            x: root.questionX; y: 48 + index * 58; width: root.questionWidth; height: 44; radius: 10
            color: modelData.heuristicId === root.selectedHeuristicId ? theme.colors.selected : theme.colors.card
            border.width: modelData.heuristicId === root.selectedHeuristicId ? 2 : 1
            border.color: modelData.heuristicId === root.selectedHeuristicId ? theme.colors.accent : theme.colors.borderStrong
            Row { anchors.fill: parent; anchors.margins: 7; spacing: 6
                Rectangle { width: 27; height: 27; anchors.verticalCenter: parent.verticalCenter; radius: 14; color: theme.colors.card; border.width: 1; border.color: theme.colors.success; Text { anchors.centerIn: parent; text: modelData.answer || "?"; color: theme.colors.success; font.pixelSize: 10; font.weight: Font.Bold } }
                Text { anchors.verticalCenter: parent.verticalCenter; width: parent.width - 41; text: modelData.question || modelData.ruleLabel; color: theme.colors.textSecondary; font.pixelSize: 10; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight }
            }
            HoverHandler { id: qHover }
            TapHandler { onTapped: parent.pinned = !parent.pinned }
            ToolTip.visible: qHover.hovered || pinned
            ToolTip.text: modelData.question || modelData.ruleLabel
            ToolTip.delay: 250
        }
    }

    Repeater {
        model: root.reasons || []
        delegate: Rectangle {
            required property var modelData; required property int index; property bool pinned: false
            x: root.evidenceX; y: 54 + index * 58; width: root.evidenceWidth; height: 32; radius: 9
            color: modelData.heuristicId === root.selectedHeuristicId ? theme.colors.card : theme.colors.panelRaised
            border.width: 1; border.color: modelData.heuristicId === root.selectedHeuristicId ? theme.colors.accent : theme.colors.border; clip: true
            Text { anchors.fill: parent; anchors.leftMargin: 5; anchors.rightMargin: 5; text: "+" + Number(modelData.contribution).toFixed(2) + " → " + modelData.heuristicLabel; color: modelData.heuristicId === root.selectedHeuristicId ? theme.colors.accent : theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
            HoverHandler { id: eHover }
            TapHandler { onTapped: parent.pinned = !parent.pinned }
            ToolTip.visible: eHover.hovered || pinned
            ToolTip.text: modelData.question + "\n+" + Number(modelData.contribution).toFixed(2) + " → " + modelData.heuristicLabel
            ToolTip.delay: 250
        }
    }

    Repeater {
        model: root.scores || []
        delegate: Rectangle {
            required property var modelData; required property int index
            x: root.strategyX; y: root.heuristicY(index) - 22; width: root.strategyWidth; height: 44; radius: 11
            color: modelData.id === root.selectedHeuristicId ? theme.colors.card : theme.colors.card; border.width: modelData.id === root.selectedHeuristicId ? 2 : 1; border.color: modelData.id === root.selectedHeuristicId ? theme.colors.accent : theme.colors.borderStrong; scale: modelData.id === root.selectedHeuristicId ? 1.035 : 1.0
            Behavior on scale { NumberAnimation { duration: 150 } }
            Column { anchors.centerIn: parent; width: parent.width - 8; spacing: 1
                Text { width: parent.width; text: modelData.label; color: modelData.id === root.selectedHeuristicId ? theme.colors.accent : theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight }
                Text { width: parent.width; text: i18n.strings.score + " " + Number(modelData.score || 0).toFixed(2); color: theme.colors.textMuted; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }

    // Empty-state belongs exclusively to the EVIDENCE column. It can no longer cover strategies.
    Rectangle {
        x: root.evidenceX; y: 78; width: root.evidenceWidth; height: 112; radius: 12
        visible: !root.reasons || root.reasons.length === 0; color: theme.colors.panelRaised; border.width: 1; border.color: theme.colors.border; clip: true
        Column { anchors.fill: parent; anchors.margins: 10; spacing: 6
            Text { width: parent.width; text: root.selectedHeuristicId ? i18n.strings.base_scores_only : i18n.strings.no_active_decision; color: theme.colors.textSecondary; font.pixelSize: 10; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap }
            Text { width: parent.width; text: root.selectedHeuristicId ? i18n.strings.no_extra_questions : i18n.strings.play_to_see_evidence; color: theme.colors.textSubtle; font.pixelSize: 10; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap }
        }
    }
}
