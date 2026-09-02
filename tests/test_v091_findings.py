from pathlib import Path

from impossible_move.domain.models import BinPackingInstance, Item
from impossible_move.engine import BinPackingEngine
from impossible_move.frontend.i18n import tr
from impossible_move.frontend.presenter import snapshot_to_view_model
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import ReplayCatalog, ReplayController


ROOT = Path(__file__).parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"
FRONTEND = ROOT / "src" / "impossible_move" / "frontend"


def _demo_controller():
    instance = BinPackingInstance(
        id="lb-demo",
        name="LB demo",
        capacity=10,
        items=(
            Item(id="a", size=8, display_name="Sofá", asset_id="sofa"),
            Item(id="b", size=7, display_name="Cama", asset_id="bed"),
            Item(id="c", size=5, display_name="Caja", asset_id="clothes_box"),
        ),
    )
    result = BinPackingEngine().solve(
        instance,
        ExplainableRuleBasedHH(),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        OriginalOrder(),
        run_id="lb-run",
    )
    catalog = ReplayCatalog.from_instance(instance)
    return ReplayController(result.trace, catalog=catalog), instance


def test_v091_research_group_head_is_localized_with_language_specific_degree_style():
    assert tr("responsible_professor", "es") == "Responsable del grupo OPTIMA"
    assert tr("responsible_professor", "en") == "Research Group Head"
    assert tr("responsible_professor_name", "es") == "Dr. Guillermo Falcón"
    assert tr("responsible_professor_name", "en") == "Guillermo Falcón, PhD"


def test_v091_about_exists_only_in_footer_not_title_bar():
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    title = (QML / "components" / "TitleBar.qml").read_text(encoding="utf-8")
    assert "aboutRequested" not in title
    assert "aboutButton" not in title
    assert "aboutPopup.open()" in main
    assert 'buttonText: "ⓘ  " + i18n.strings.about' in main


def test_v091_root_and_main_columns_have_responsive_width_constraints():
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    assert "Screen.desktopAvailableWidth" in main
    assert "Screen.desktopAvailableHeight" in main
    assert "Math.min(340, Math.max(250, root.width * 0.215))" in main
    assert "Math.min(500, Math.max(360, root.width * 0.295))" in main
    assert main.count("Layout.minimumWidth: 350") >= 2


def test_v091_truck_cards_reserve_space_for_scrollbar():
    trucks = (QML / "components" / "AdaptiveTruckView.qml").read_text(encoding="utf-8")
    assert "width: smallTruckList.width - 22" in trucks
    assert "id: smallTruckScroll" in trucks


def test_v091_optima_application_icon_is_packaged_and_windows_identity_is_set():
    ico = QML / "assets" / "branding" / "optima_app.ico"
    assert ico.is_file() and ico.stat().st_size > 1000
    app = (FRONTEND / "app.py").read_text(encoding="utf-8")
    assert "SetCurrentProcessExplicitAppUserModelID" in app
    assert "optima_app.ico" in app
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"qml/assets/branding/*.ico"' in pyproject


def test_v091_hyperheuristic_is_explicitly_presented_as_decision_entity():
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    identity = (QML / "components" / "HyperHeuristicIdentity.qml").read_text(encoding="utf-8")
    assert "HyperHeuristicIdentity" in main
    assert "i18n.strings.who_is_deciding" in main
    assert 'text: "HH"' in identity
    assert "i18n.strings.hh_entity_body" in identity
    assert "i18n.strings.hh_flow_state" in identity
    assert "i18n.strings.hh_flow_strategy" in identity


def test_v091_lower_bound_help_uses_total_instance_volume_and_capacity():
    controller, instance = _demo_controller()
    view = snapshot_to_view_model(controller.snapshot, controller.catalog, language="es")
    assert view["summary"]["totalItemSize"] == sum(item.size for item in instance.items)
    assert view["summary"]["lowerBound"] == 2

    main = (QML / "Main.qml").read_text(encoding="utf-8")
    metric = (QML / "components" / "MetricTile.qml").read_text(encoding="utf-8")
    assert "onHelpRequested: lowerBoundHelp.open()" in main
    assert "i18n.strings.lower_bound_formula_body" in main
    assert "totalItemSize" in main
    assert "signal helpRequested()" in metric
