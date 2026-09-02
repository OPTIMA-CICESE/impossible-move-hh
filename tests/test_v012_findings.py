from pathlib import Path

from impossible_move.frontend.comparison import ComparisonReplayController, comparison_view, move_explorer_view
from impossible_move.frontend.i18n import strings
from impossible_move.experiments import ExperimentCache, ExperimentConfiguration, ExperimentService

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"


def test_v012_theme_adapter_and_titlebar_controls_exist():
    adapter = (ROOT / "src" / "impossible_move" / "frontend" / "theme_adapter.py").read_text(encoding="utf-8")
    title = (QML / "components" / "TitleBar.qml").read_text(encoding="utf-8")
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    assert 'SUPPORTED_THEMES = ("dark", "light")' in adapter
    assert 'theme.setTheme(modelData)' in title
    assert 'theme.colors.window' in main


def test_v012_instruction_strings_are_bilingual():
    for language in ("es", "en"):
        values = strings(language)
        for key in (
            "instructions", "instructions_title", "instructions_goal_title",
            "instructions_config_title", "instructions_methods_title",
            "instructions_solve_title", "instructions_hh_title",
            "instructions_compare_title", "instructions_explore_title",
        ):
            assert values[key]


def test_v012_move_explorer_is_lazy_and_grouped_for_large_instances(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    cfg = ExperimentConfiguration(item_count=200, truck_capacity=10, instance_index=0, batch_seed=42, profile="natural")
    resolved = service.resolve_comparison(cfg, selected_policies=("adaptive", "random"), fixed_heuristic_id="best_fit")
    controller = ComparisonReplayController(resolved)
    basic = comparison_view(controller, "es")
    assert "moveItems" not in basic
    explorer = move_explorer_view(controller, "es")
    assert explorer["itemCount"] == 200
    assert len(explorer["items"]) == 200
    assert sum(row["total"] for row in explorer["groups"]) == 200
    assert all("totalSize" in row for row in explorer["groups"])


def test_v012_move_explorer_qml_uses_summary_category_detail_flow():
    qml = (QML / "components" / "MoveExplorerPopup.qml").read_text(encoding="utf-8")
    assert "largeInstance" in qml
    assert "selectedGroupKey" in qml
    assert "filteredItems()" in qml
    assert "explorer_select_category" in qml
    assert "comparison.releaseMoveExplorer()" in qml


def test_v012_comparison_adapter_caps_visual_fps():
    source = (ROOT / "src" / "impossible_move" / "frontend" / "comparison_adapter.py").read_text(encoding="utf-8")
    assert "MAX_VISUAL_FPS = 30" in source
    assert "decisions_per_tick" in source
    assert "prepareMoveExplorer" in source
    assert "releaseMoveExplorer" in source


def test_v012_qml_has_no_hardcoded_hex_colors_outside_assets():
    for path in QML.rglob("*.qml"):
        text = path.read_text(encoding="utf-8")
        assert "#" not in text, f"hard-coded color remains in {path.name}"
