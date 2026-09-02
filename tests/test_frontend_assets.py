from pathlib import Path
from xml.etree import ElementTree

from impossible_move.domain.models import BinPackingInstance, Item
from impossible_move.engine import BinPackingEngine
from impossible_move.frontend.presenter import action_to_transition
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import ReplayCatalog, ReplayController


QML_ROOT = Path(__file__).parents[1] / "src" / "impossible_move" / "frontend" / "qml"
ASSET_ROOT = QML_ROOT / "assets"


def build_run():
    instance = BinPackingInstance(
        id="asset-demo",
        name="Asset demo",
        capacity=10,
        items=(
            Item(id="a", size=8, display_name="Sofá", asset_id="sofa"),
            Item(id="b", size=2, display_name="Caja", asset_id="clothes_box"),
        ),
    )
    result = BinPackingEngine().solve(
        instance,
        ExplainableRuleBasedHH(),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        OriginalOrder(),
        run_id="asset-run",
    )
    return instance, result


def test_all_svg_assets_are_well_formed():
    files = sorted(ASSET_ROOT.rglob("*.svg"))
    assert files
    for path in files:
        root = ElementTree.parse(path).getroot()
        assert root.tag.endswith("svg")
        assert root.attrib.get("viewBox")


def test_demo_catalog_asset_ids_have_matching_svg_files():
    import json

    catalog_path = Path(__file__).parents[1] / "examples" / "demo_rule_catalog.json"
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    for item in data["items"]:
        assert (ASSET_ROOT / "objects" / f"{item['asset_id']}.svg").is_file()
    assert (ASSET_ROOT / "truck.svg").is_file()


def test_place_item_action_builds_visual_transition_packet():
    instance, result = build_run()
    catalog = ReplayCatalog.from_instance(instance)
    controller = ReplayController(result.trace, catalog=catalog)
    placed_sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "ItemPlaced")
    frame = controller.seek_sequence(placed_sequence)
    assert frame is not None
    transition = action_to_transition(frame.action, frame.snapshot, catalog)
    assert transition["type"] == "place_item"
    assert transition["item"]["assetId"] == "sofa"
    assert transition["binId"] == 0
    assert transition["binIndex"] == 0


def test_qml_contains_visual_components_and_transition_hook():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    assert "DecisionGraph" in main
    assert "FlyingObject" in main
    assert "onFrameAdvanced" in main
    assert "adaptiveTruckView.targetPoint" in main


def test_v07_branding_assets_are_packaged_and_referenced_by_qml():
    branding = ASSET_ROOT / "branding"
    expected = {"optima_full.png", "optima_mark.png", "optima_white.png", "cicese.png"}
    assert expected <= {path.name for path in branding.glob("*.png")}
    for name in expected:
        data = (branding / name).read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")

    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    assert "assets/branding/optima_mark.png" in main
    assert "assets/branding/cicese.png" in main
    assert "OPTIMA Research Group" in main


def test_v07_ui_has_real_presentation_detailed_separation_and_relocated_metrics():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    assert 'readonly property bool detailedMode: replay.mode === "detailed"' in main
    assert main.count("visible: root.detailedMode") >= 6
    assert "viewHelp.open()" in main
    assert "decisionNarrative" in main
    assert main.count("MetricTile {") == 3
    assert "i18n.strings.moving_trucks" in main


def test_v07_decision_graph_uses_three_stage_pedagogical_structure():
    graph = (QML_ROOT / "components" / "DecisionGraph.qml").read_text(encoding="utf-8")
    assert "i18n.strings.questions" in graph
    assert "i18n.strings.evidence" in graph
    assert "i18n.strings.strategies" in graph
    assert "modelData.question" in graph
    assert "modelData.answer" in graph
    assert "modelData.contribution" in graph

    help_popup = (QML_ROOT / "components" / "RuleHelpPopup.qml").read_text(encoding="utf-8")
    assert "i18n.strings.how_read_questions" in help_popup
    assert "i18n.strings.questions_help_intro" in help_popup


def test_v071_decision_graph_reserves_three_non_overlapping_columns():
    graph = (QML_ROOT / "components" / "DecisionGraph.qml").read_text(encoding="utf-8")
    assert "readonly property real strategyX" in graph
    assert "readonly property real questionWidth" in graph
    assert "readonly property real evidenceX" in graph
    assert "readonly property real evidenceWidth" in graph
    assert "x: root.evidenceX" in graph
    assert "width: root.evidenceWidth" in graph
    assert "i18n.strings.no_active_decision" in graph
    assert "anchors.centerIn: parent" not in graph.split("// Empty-state belongs exclusively", 1)[1]
    assert "clip: true" in graph


def test_v071_uses_themed_scrollbars_in_all_scrollable_main_regions():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    pending = (QML_ROOT / "components" / "AdaptivePendingView.qml").read_text(encoding="utf-8")
    trucks = (QML_ROOT / "components" / "AdaptiveTruckView.qml").read_text(encoding="utf-8")
    config = (QML_ROOT / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    themed = (QML_ROOT / "components" / "ThemedScrollBar.qml").read_text(encoding="utf-8")
    combined = main + pending + trucks + config
    assert combined.count("ScrollBar.vertical: ThemedScrollBar") >= 6
    assert "ScrollBar.horizontal: ThemedScrollBar" in combined
    assert "ScrollBar.vertical: ScrollBar { }" not in combined
    assert 'color: control.pressed' in themed
    assert "theme.colors.accent" in themed
    assert "theme.colors.bar" in themed
    assert "Behavior on opacity" in themed


def test_v080_replaces_permanent_question_legend_with_popup_trigger():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    help_popup = (QML_ROOT / "components" / "RuleHelpPopup.qml").read_text(encoding="utf-8")
    assert "DecisionLegend {" not in main
    assert "i18n.strings.how_read_questions" in main
    assert "ruleHelp.open()" in main
    assert "i18n.strings.questions_help_intro" in help_popup
    assert "DETALLE TÉCNICO" not in main


def test_v080_has_experiment_configuration_popup_and_search_space_strip():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    config_popup = (QML_ROOT / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    assert "ExperimentConfigPopup" in main
    assert "i18n.strings.change_move" in main
    assert "i18n.strings.hh_potential_sequences" in main
    assert "i18n.strings.theoretical_groups" in main
    assert "supportedItemCounts" in config_popup
    assert "i18n.strings.generate_five" in config_popup
    assert "i18n.strings.resolve_move" in config_popup
    assert "setCapacity" in config_popup


def test_v081_has_adaptive_multiscale_views_and_large_replay_controls():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    pending = (QML_ROOT / "components" / "AdaptivePendingView.qml").read_text(encoding="utf-8")
    trucks = (QML_ROOT / "components" / "AdaptiveTruckView.qml").read_text(encoding="utf-8")
    assert "AdaptivePendingView" in main
    assert "AdaptiveTruckView" in main
    assert 'presentationScale' in main
    assert "i18n.strings.next_relevant" in main
    assert 'visible: replay.view.presentationScale === "large"' in main
    assert 'root.scale === "small"' in pending
    assert 'root.scale === "medium"' in pending
    assert "i18n.strings.pending_by_category" in pending
    assert "i18n.strings.global_occupancy_map" in trucks
    assert "i18n.strings.cell_one_truck" in trucks


def test_v090_closes_findings_with_custom_chrome_help_and_themed_controls():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    config = (QML_ROOT / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    titlebar = (QML_ROOT / "components" / "TitleBar.qml").read_text(encoding="utf-8")
    combo = (QML_ROOT / "components" / "ThemedComboBox.qml").read_text(encoding="utf-8")
    about = (QML_ROOT / "components" / "AboutPopup.qml").read_text(encoding="utf-8")
    assert "Qt.FramelessWindowHint" in main
    assert "TitleBar" in main and "WindowResizeHandles" in main
    assert "ThemedComboBox" in main
    assert "\n                    ComboBox {" not in main
    assert "viewHelp.open()" in main and "controlsHelp.open()" in main
    assert 'tracePolicy !== "full"' not in main
    assert "Preguntas → evidencia → estrategia" not in main
    assert "Semilla reproducible" not in config
    assert "itemCountHelp.open()" in config
    assert "capacityHelp.open()" in config
    assert "instanceHelp.open()" in config
    assert "i18n.setLanguage" in titlebar
    assert "BSD 3-Clause" not in main  # About dialog owns legal copy.
    assert "i18n.strings.license_name" in about
    assert "popup:" in combo


def test_v090_header_avoids_duplicate_optima_branding():
    main = (QML_ROOT / "Main.qml").read_text(encoding="utf-8")
    titlebar = (QML_ROOT / "components" / "TitleBar.qml").read_text(encoding="utf-8")
    header_end = main.index("    ColumnLayout {\n        anchors.fill: parent")
    header = main[:header_end]
    assert "optima_mark.png" in titlebar
    assert "assets/branding/optima_mark.png" not in header
    assert "OPTIMA · Optimización" not in main
    # Full institutional branding intentionally remains in the footer.
    assert "OPTIMA Research Group" in main
    assert "assets/branding/cicese.png" in main


def test_v090_license_file_is_bsd_3_clause():
    license_text = (Path(__file__).parents[1] / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("BSD 3-Clause License")
    assert "OPTIMA Research Group / CICESE" in license_text
    assert "Neither the name of the copyright holder" in license_text
