from pathlib import Path

ROOT = Path(__file__).parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"


def test_v0131_hh_identity_uses_vertical_semantic_flow():
    qml = (QML / "components" / "HyperHeuristicIdentity.qml").read_text(encoding="utf-8")
    # The flow is state -> HH -> low-level heuristic -> truck.
    assert qml.index("hh_flow_input") < qml.index("hh_entity_name")
    assert qml.index("hh_entity_name") < qml.index("hh_flow_strategy")
    assert qml.index("hh_flow_strategy") < qml.index("text: i18n.strings.truck")
    # Identity text remains isolated in its own two-column card.
    assert "Layout.preferredWidth: 96" in qml
    assert "implicitHeight: identityRow.implicitHeight + 20" in qml


def test_v0131_comparison_panel_has_global_vertical_scroll():
    qml = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    assert "id: comparisonScroll" in qml
    assert "ScrollBar.vertical: ThemedScrollBar" in qml
    assert "width: comparisonScroll.availableWidth" in qml


def test_v0131_method_truck_grids_have_explicit_viewport():
    qml = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    assert "Layout.preferredHeight: 105" in qml
    assert "Layout.minimumHeight: 80" in qml


def test_v0131_best_fixed_section_is_responsive_and_content_sized():
    qml = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    assert "id: benchmarkContent" in qml
    assert "implicitHeight: visible ? benchmarkContent.implicitHeight + 22 : 0" in qml
    assert "columns: width >= 520 ? 2 : 1" in qml
