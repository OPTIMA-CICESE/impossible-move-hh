from impossible_move.domain.models import BinPackingInstance, Item, ItemCategory
from impossible_move.engine import BinPackingEngine
from impossible_move.frontend.adaptive import PresentationScale, category_groups, pending_groups, speed_options
from impossible_move.frontend.presenter import snapshot_to_view_model
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import ReplayCatalog, ReplayController
from impossible_move.trace.events import PlacementEvaluated, StateObserved
from impossible_move.trace.policy import TracePolicy


def make_instance(n: int) -> BinPackingInstance:
    return BinPackingInstance(
        id=f"n{n}", name=f"n{n}", capacity=10,
        items=tuple(Item(id=f"i{i}", size=(i % 9) + 1, display_name="Caja", category=ItemCategory.BOX, asset_id="clothes_box") for i in range(n)),
    )


def solve(n: int, policy: TracePolicy):
    instance = make_instance(n)
    result = BinPackingEngine().solve(
        instance, ExplainableRuleBasedHH(), [FirstFit(), BestFit(), WorstFit(), NextFit()], OriginalOrder(), trace_policy=policy
    )
    return instance, result


def test_scale_thresholds_and_speed_options():
    assert PresentationScale.for_item_count(10) is PresentationScale.SMALL
    assert PresentationScale.for_item_count(20) is PresentationScale.SMALL
    assert PresentationScale.for_item_count(50) is PresentationScale.MEDIUM
    assert PresentationScale.for_item_count(100) is PresentationScale.MEDIUM
    assert PresentationScale.for_item_count(200) is PresentationScale.LARGE
    assert PresentationScale.for_item_count(500) is PresentationScale.LARGE
    assert 200.0 in speed_options(PresentationScale.LARGE)


def test_trace_policies_compact_diagnostics_but_preserve_evaluation_total():
    _, full = solve(20, TracePolicy.FULL)
    _, standard = solve(20, TracePolicy.STANDARD)
    _, compact = solve(20, TracePolicy.COMPACT)
    assert any(isinstance(event, PlacementEvaluated) for event in full.trace.events)
    assert not any(isinstance(event, PlacementEvaluated) for event in standard.trace.events)
    assert any(isinstance(event, StateObserved) for event in standard.trace.events)
    assert not any(isinstance(event, StateObserved) for event in compact.trace.events)
    assert len(compact.trace.events) < len(standard.trace.events) < len(full.trace.events)
    assert full.trace.events[-1].placement_evaluations == standard.trace.events[-1].placement_evaluations == compact.trace.events[-1].placement_evaluations


def test_large_presenter_does_not_materialize_all_object_or_full_bin_cards():
    instance, result = solve(200, TracePolicy.COMPACT)
    catalog = ReplayCatalog.from_instance(instance)
    controller = ReplayController(result.trace, catalog=catalog)
    controller.seek_sequence(0)
    view = snapshot_to_view_model(controller.snapshot, catalog)
    assert view["presentationScale"] == "large"
    assert view["pendingItems"] == []
    assert view["bins"] == []
    assert view["categoryGroups"]
    assert view["activity"]["totalItems"] == 200
    assert view["tracePolicy"] == "compact"


def test_grouped_pending_models_preserve_pending_count():
    instance, result = solve(50, TracePolicy.STANDARD)
    catalog = ReplayCatalog.from_instance(instance)
    controller = ReplayController(result.trace, catalog=catalog)
    controller.seek_sequence(0)
    snapshot = controller.snapshot
    assert sum(row["count"] for row in pending_groups(snapshot, catalog)) == len(snapshot.remaining_item_ids)
    assert sum(row["count"] for row in category_groups(snapshot, catalog)) == len(snapshot.remaining_item_ids)


def test_interesting_replay_advances_without_changing_solution():
    instance, result = solve(50, TracePolicy.STANDARD)
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))
    controller.seek_sequence(0)
    frame = controller.advance_interesting()
    assert frame is not None
    controller.jump_to_end()
    assert controller.snapshot.summary is not None
    assert controller.snapshot.summary.bins_used == result.solution.bins_used
