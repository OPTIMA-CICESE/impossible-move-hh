from impossible_move.domain.models import BinPackingInstance, Item
from impossible_move.engine import BinPackingEngine
from impossible_move.frontend.presenter import snapshot_to_view_model
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import ReplayCatalog, ReplayController, ReplayMode


def build_run():
    instance = BinPackingInstance(
        id="presenter-demo",
        name="Presenter demo",
        capacity=10,
        items=(
            Item(id="a", size=8, display_name="Sofá", asset_id="sofa"),
            Item(id="b", size=2, display_name="Caja", asset_id="clothes_box"),
            Item(id="c", size=6, display_name="Cama", asset_id="bed"),
            Item(id="d", size=4, display_name="TV", asset_id="tv"),
        ),
    )
    result = BinPackingEngine().solve(
        instance,
        ExplainableRuleBasedHH(),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        OriginalOrder(),
        run_id="presenter-run",
    )
    return instance, result


def test_presenter_exposes_pending_items_after_run_started():
    instance, result = build_run()
    controller = ReplayController(
        result.trace,
        catalog=ReplayCatalog.from_instance(instance),
        mode=ReplayMode.PRESENTATION,
    )
    controller.seek_sequence(0)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert [item["displayName"] for item in view["pendingItems"]] == ["Sofá", "Caja", "Cama", "TV"]
    assert view["bins"] == []
    assert view["binCapacity"] == 10
    assert view["summary"]["lowerBound"] == 2
    assert view["currentItem"] == {}


def test_presenter_exposes_current_decision_scores_and_reasons():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    controller.seek_sequence(0)
    controller.advance()  # ItemSelected
    controller.advance()  # StateObserved
    controller.advance()  # HeuristicSelected
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert view["currentItem"]["id"] == "a"
    assert len(view["heuristicScores"]) == 4
    assert any(score["selected"] for score in view["heuristicScores"])
    assert view["decisionReasons"]
    assert all("ruleLabel" in reason for reason in view["decisionReasons"])


def test_presenter_exposes_final_trucks_and_summary():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    controller.jump_to_end()
    view = snapshot_to_view_model(controller.snapshot, controller.catalog, last_action="run_finished")
    assert view["summary"]["finished"] is True
    assert view["summary"]["binsUsed"] == result.solution.bins_used
    assert sum(len(bin_["items"]) for bin_ in view["bins"]) == 4
    assert view["pendingItems"] == []
    assert view["lastAction"] == "run_finished"


def test_score_normalization_uses_current_maximum():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    # seek to the first heuristic selection
    sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "HeuristicSelected")
    controller.seek_sequence(sequence)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert max(entry["normalized"] for entry in view["heuristicScores"]) == 1.0


def test_unfinished_summary_uses_total_capacity_of_open_bins():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    # First item: RunStarted, ItemSelected, StateObserved, HeuristicSelected,
    # PlacementSelected, BinCreated, ItemPlaced. Seek to the first ItemPlaced.
    sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "ItemPlaced")
    controller.seek_sequence(sequence)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert view["summary"]["binsUsed"] == 1
    assert view["summary"]["totalCapacity"] == 10
    assert view["summary"]["usedCapacity"] == 8
    assert view["summary"]["unusedCapacity"] == 2
    assert view["summary"]["utilization"] == 0.8


def test_presenter_exposes_graph_reasons_without_base_rule():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "HeuristicSelected")
    controller.seek_sequence(sequence)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert all(reason["ruleId"] != "base" for reason in view["decisionGraphReasons"])


def test_v07_initial_copy_explains_how_to_start_instead_of_waiting_for_decision():
    instance, result = build_run()
    controller = ReplayController(
        result.trace,
        catalog=ReplayCatalog.from_instance(instance),
        mode=ReplayMode.PRESENTATION,
    )
    controller.seek_sequence(0)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert view["statusMessage"] == "Lista para comenzar"
    assert "Presiona Reproducir" in view["decisionNarrative"]
    assert "Esperando la primera decisión" not in view["decisionNarrative"]


def test_v07_mode_information_makes_presentation_and_detailed_semantics_explicit():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    controller.set_mode(ReplayMode.PRESENTATION)
    presentation = snapshot_to_view_model(controller.snapshot, controller.catalog)
    controller.set_mode(ReplayMode.DETAILED)
    detailed = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert presentation["modeInfo"]["label"] == "Vista divulgativa"
    assert "Prioriza" in presentation["modeInfo"]["description"]
    assert detailed["modeInfo"]["label"] == "Vista detallada"
    assert "características" in detailed["modeInfo"]["description"]


def test_v07_decision_reasons_are_exposed_as_questions_for_the_graph():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "HeuristicSelected")
    controller.seek_sequence(sequence)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    active = view["decisionGraphReasons"]
    assert active
    assert all(reason["question"].startswith("¿") for reason in active)
    assert all(reason["answer"] == "SÍ" for reason in active)
    assert view["ruleLegend"]
    assert all("meaning" in entry for entry in view["ruleLegend"])


def test_v07_detailed_data_exposes_features_and_bin_evaluations():
    instance, result = build_run()
    controller = ReplayController(
        result.trace,
        catalog=ReplayCatalog.from_instance(instance),
        mode=ReplayMode.DETAILED,
    )
    evaluation_sequence = next(
        e.sequence for e in result.trace.events if e.__class__.__name__ == "PlacementEvaluated"
    )
    controller.seek_sequence(evaluation_sequence)
    view = snapshot_to_view_model(controller.snapshot, controller.catalog)
    assert view["featureRows"]
    assert view["placementEvaluations"]
    assert {"binLabel", "feasible", "remainingBefore", "remainingAfter"} <= set(
        view["placementEvaluations"][0]
    )


def test_v090_english_presentation_localizes_objects_questions_and_narrative_without_changing_trace():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    controller.seek_sequence(0)
    cursor_before = controller.snapshot.cursor
    english = snapshot_to_view_model(controller.snapshot, controller.catalog, language="en")
    spanish = snapshot_to_view_model(controller.snapshot, controller.catalog, language="es")

    assert english["language"] == "en"
    assert spanish["language"] == "es"
    assert english["pendingItems"][0]["displayName"] == "Sofa"
    assert spanish["pendingItems"][0]["displayName"] == "Sofá"
    assert "Press Play" in english["decisionNarrative"]
    assert "Presiona Reproducir" in spanish["decisionNarrative"]
    assert controller.snapshot.cursor == cursor_before


def test_v090_english_decision_questions_are_localized_from_semantic_rule_ids():
    instance, result = build_run()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    sequence = next(e.sequence for e in result.trace.events if e.__class__.__name__ == "HeuristicSelected")
    controller.seek_sequence(sequence)
    english = snapshot_to_view_model(controller.snapshot, controller.catalog, language="en")
    spanish = snapshot_to_view_model(controller.snapshot, controller.catalog, language="es")

    assert english["decisionGraphReasons"]
    assert spanish["decisionGraphReasons"]
    assert english["decisionGraphReasons"][0]["question"] != spanish["decisionGraphReasons"][0]["question"]
    assert all(row["answer"] == "YES" for row in english["decisionGraphReasons"])
    assert all(row["answer"] == "SÍ" for row in spanish["decisionGraphReasons"])
