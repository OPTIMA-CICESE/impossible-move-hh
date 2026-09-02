from pathlib import Path

from impossible_move.experiments import (
    ExperimentCache,
    ExperimentConfiguration,
    ExperimentService,
    MovingInstanceGenerator,
    SUPPORTED_PROFILES,
)
from impossible_move.frontend.comparison import ComparisonReplayController, comparison_view

ROOT = Path(__file__).parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"


def test_v013_regime_profile_is_supported_reproducible_and_distinct():
    assert "regime" in SUPPORTED_PROFILES
    gen = MovingInstanceGenerator()
    a = gen.generate_set(item_count=100, capacity=10, batch_seed=20260831, profile="regime")
    b = gen.generate_set(item_count=100, capacity=10, batch_seed=20260831, profile="regime")
    natural = gen.generate_set(item_count=100, capacity=10, batch_seed=20260831, profile="natural")
    assert a == b
    assert tuple(i.size for i in a.candidates[0].instance.items) != tuple(
        i.size for i in natural.candidates[0].instance.items
    )


def test_v013_regime_contains_both_adaptive_opportunity_and_fixed_friendly_cases(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    deltas = []
    # The corpus must expose adaptation opportunities without forcing an adaptive win.
    for index in (2, 3):
        cfg = ExperimentConfiguration(
            item_count=100,
            truck_capacity=10,
            instance_index=index,
            batch_seed=20260831,
            profile="regime",
        )
        resolved = service.resolve_comparison(
            cfg,
            selected_policies=("adaptive", "random", "fixed"),
            fixed_heuristic_id="best_fit",
        )
        deltas.append(resolved.adaptive_delta_to_best_fixed)
    assert any(delta < 0 for delta in deltas)
    assert any(delta > 0 for delta in deltas)


def test_v013_best_fixed_benchmark_covers_all_four_heuristics(tmp_path):
    service = ExperimentService(cache=ExperimentCache(tmp_path))
    cfg = ExperimentConfiguration(
        item_count=50,
        truck_capacity=10,
        instance_index=1,
        batch_seed=20260831,
        profile="regime",
    )
    resolved = service.resolve_comparison(
        cfg,
        selected_policies=("adaptive", "random"),
        fixed_heuristic_id="best_fit",
    )
    assert set(resolved.fixed_benchmarks) == {"first_fit", "best_fit", "worst_fit", "next_fit"}
    assert resolved.best_fixed_bins == min(resolved.fixed_benchmarks.values())
    assert resolved.best_fixed_heuristic_id in resolved.fixed_benchmarks

    controller = ComparisonReplayController(resolved)
    controller.jump_to_end()
    view = comparison_view(controller, "es")
    assert view["bestFixed"]["bins"] == resolved.best_fixed_bins
    assert len(view["bestFixed"]["benchmarks"]) == 4


def test_v013_profile_cards_expose_full_description_on_hover_and_regime_help():
    qml = (QML / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    assert "profile_regime" in qml
    assert "ToolTip.text: modelData.label" in qml
    assert "columns: 2" in qml
    assert "maximumLineCount: 3" in qml


def test_v013_hh_identity_reserves_separate_role_column():
    qml = (QML / "components" / "HyperHeuristicIdentity.qml").read_text(encoding="utf-8")
    assert "Layout.preferredWidth: 96" in qml
    assert "text: i18n.strings.hh_entity_role" in qml
    assert "implicitHeight: content.implicitHeight + 26" in qml


def test_v013_themed_scrollbar_spans_parent_viewport():
    qml = (QML / "components" / "ThemedScrollBar.qml").read_text(encoding="utf-8")
    assert "parent.height" in qml
    assert "parent.width" in qml


def test_v013_all_explicit_scrollbar_attachments_use_themed_component():
    offenders = []
    for path in QML.rglob("*.qml"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "ScrollBar.vertical:" in line and "ThemedScrollBar" not in line:
                offenders.append((path.name, line.strip()))
            if "ScrollBar.horizontal:" in line and "ThemedScrollBar" not in line:
                offenders.append((path.name, line.strip()))
    assert offenders == []


def test_v013_comparison_panel_shows_posthoc_best_fixed_benchmark():
    qml = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    assert "best_fixed_benchmark" in qml
    assert "root.comparisonView.finished" in qml
    assert "root.comparisonView.bestFixed" in qml
