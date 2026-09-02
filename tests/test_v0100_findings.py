from pathlib import Path

from impossible_move.experiments import ExperimentConfiguration, ExperimentService
from impossible_move.frontend.comparison import ComparisonReplayController, comparison_view
from impossible_move.frontend.presenter import grouped_decision_histories, snapshot_to_view_model, trace_decision_history
from impossible_move.replay import ReplayController
from impossible_move.trace.events import HeuristicSelected, RunStarted

ROOT = Path(__file__).parents[1]
QML = ROOT / "src" / "impossible_move" / "frontend" / "qml"


def _comparison():
    service = ExperimentService()
    cfg = ExperimentConfiguration(item_count=10, truck_capacity=10, instance_index=0, batch_seed=777)
    return service.resolve_comparison(
        cfg,
        selected_policies=("adaptive", "random", "fixed"),
        fixed_heuristic_id="best_fit",
    )


def test_r31_decision_history_is_extracted_and_grouped_without_future_rows():
    resolved = _comparison()
    run = resolved.runs["adaptive"]
    history = trace_decision_history(run.trace, run.catalog, "en")
    assert len(history) == 10
    assert history[0]["decision"] == 1
    assert history[0]["displayName"]
    assert history[0]["heuristicLabel"]
    assert history[0]["truckLabel"].startswith("Truck")
    grouped = grouped_decision_histories(run.trace, run.catalog, "en", limit=3)
    assert sum(row["count"] for row in grouped) == 3
    assert sum(len(row["decisions"]) for row in grouped) == 3


def test_r32_relevant_feedback_is_large_only_in_qml():
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    assert 'replay.view.presentationScale === "large" && replay.view.interestingInfo' in main


def test_r33_object_volume_is_explicit_in_truck_and_item_cards():
    truck = (QML / "components" / "TruckCard.qml").read_text(encoding="utf-8")
    item = (QML / "components" / "ObjectCard.qml").read_text(encoding="utf-8")
    assert "i18n.strings.volume_abbr" in truck
    assert "i18n.strings.volume" in truck
    assert "i18n.strings.volume" in item


def test_r34_decision_counter_never_counts_run_finished_as_extra_decision():
    resolved = _comparison()
    run = resolved.runs["adaptive"]
    controller = ReplayController(run.trace, catalog=run.catalog)
    controller.jump_to_end()
    view = snapshot_to_view_model(controller.snapshot, run.catalog, language="es")
    assert view["decisionCount"] == 10
    assert view["decisionTotal"] == 10
    assert view["decisionProgress"] == 1.0


def test_r35_identity_explains_observe_select_place_semantics():
    identity = (QML / "components" / "HyperHeuristicIdentity.qml").read_text(encoding="utf-8")
    assert "i18n.strings.hh_flow_input" in identity
    assert "i18n.strings.hh_flow_observes" in identity
    assert "i18n.strings.hh_flow_selects" in identity
    assert "i18n.strings.hh_flow_places" in identity
    assert "First Fit · Best Fit · Worst Fit · Next Fit" in identity


def test_r36_truncated_decision_nodes_have_hover_and_pin_tooltips():
    graph = (QML / "components" / "DecisionGraph.qml").read_text(encoding="utf-8")
    assert "ToolTip.visible: qHover.hovered || pinned" in graph
    assert "ToolTip.visible: eHover.hovered || pinned" in graph
    assert "TapHandler" in graph


def test_r37_headers_are_centered_from_actual_column_geometry():
    graph = (QML / "components" / "DecisionGraph.qml").read_text(encoding="utf-8")
    assert "root.questionX + (root.questionWidth - width) / 2" in graph
    assert "root.evidenceX + (root.evidenceWidth - width) / 2" in graph
    assert "root.strategyX + (root.strategyWidth - width) / 2" in graph


def test_r38_comparison_runs_same_instance_and_fixed_policy_is_really_fixed():
    resolved = _comparison()
    starts = {}
    for policy_id, run in resolved.runs.items():
        starts[policy_id] = next(e for e in run.trace.events if isinstance(e, RunStarted))
    assert len({start.instance_id for start in starts.values()}) == 1
    assert len({start.item_order for start in starts.values()}) == 1
    fixed_selected = [e.heuristic_id for e in resolved.runs["fixed"].trace.events if isinstance(e, HeuristicSelected)]
    assert fixed_selected == ["best_fit"] * 10
    assert starts["adaptive"].hyper_heuristic_id != starts["random"].hyper_heuristic_id


def test_r38_comparison_replay_advances_all_policies_by_same_decision():
    resolved = _comparison()
    controller = ComparisonReplayController(resolved)
    controller.advance_decision()
    controller.advance_decision()
    view = comparison_view(controller, "en")
    assert view["decision"] == 2
    assert view["totalDecisions"] == 10
    assert len(view["methods"]) == 3
    assert all(sum(row["count"] for row in method["heuristicCounts"]) == 2 for method in view["methods"] if method["id"] != "fixed")
    assert next(method for method in view["methods"] if method["id"] == "fixed")["heuristicCounts"] == []


def test_r38_configuration_and_comparison_layout_are_present():
    config = (QML / "components" / "ExperimentConfigPopup.qml").read_text(encoding="utf-8")
    comparison = (QML / "components" / "ComparisonPanel.qml").read_text(encoding="utf-8")
    main = (QML / "Main.qml").read_text(encoding="utf-8")
    assert "experiment.view.policyOptions" in config
    assert "experiment.setPolicySelected" in config
    assert "experiment.setFixedHeuristic" in config
    assert "ComparisonPanel" in main
    assert "comparison.nextDecision()" in main
    assert "modelData.id !== \"fixed\"" in comparison
    assert "comparison_truck_curve" in comparison
