from __future__ import annotations

import pytest

from impossible_move.domain.models import BinPackingInstance, Item, ItemCategory
from impossible_move.engine import BinPackingEngine
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.replay import (
    ReplayActionType,
    ReplayCatalog,
    ReplayConsistencyError,
    ReplayController,
    ReplayMode,
    ReplayStatus,
)
from impossible_move.trace.events import ItemPlaced, RunFinished
from impossible_move.trace.serialization import trace_from_json, trace_to_json


def moving_item(id_: str, size: int, name: str | None = None) -> Item:
    return Item(
        id=id_,
        size=size,
        display_name=name or id_,
        category=ItemCategory.FURNITURE,
        asset_id=f"asset_{id_}",
    )


def solved_demo():
    instance = BinPackingInstance(
        "replay-demo",
        "Replay Demo",
        10,
        (
            moving_item("sofa", 8, "Sofá"),
            moving_item("box", 2, "Caja"),
            moving_item("bed", 6, "Cama"),
            moving_item("tv", 4, "TV"),
        ),
    )
    result = BinPackingEngine().solve(
        instance,
        ExplainableRuleBasedHH(),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        OriginalOrder(),
        run_id="replay-run",
    )
    return instance, result


def test_detailed_replay_emits_every_trace_event() -> None:
    instance, result = solved_demo()
    controller = ReplayController(
        result.trace,
        catalog=ReplayCatalog.from_instance(instance),
        mode=ReplayMode.DETAILED,
    )

    frames = []
    while (frame := controller.advance()) is not None:
        frames.append(frame)

    assert len(frames) == len(result.trace.events)
    assert frames[0].action.type is ReplayActionType.RUN_STARTED
    assert frames[-1].action.type is ReplayActionType.RUN_FINISHED
    assert controller.status is ReplayStatus.FINISHED


def test_presentation_mode_filters_details_but_reconstructs_same_final_state() -> None:
    instance, result = solved_demo()
    controller = ReplayController(
        result.trace,
        catalog=ReplayCatalog.from_instance(instance),
        mode=ReplayMode.PRESENTATION,
    )

    action_types = []
    while (frame := controller.advance()) is not None:
        action_types.append(frame.action.type)

    assert ReplayActionType.STATE_OBSERVED not in action_types
    assert ReplayActionType.EVALUATE_BIN not in action_types
    assert ReplayActionType.SELECT_PLACEMENT not in action_types
    assert action_types.count(ReplayActionType.FOCUS_ITEM) == len(instance.items)
    assert action_types.count(ReplayActionType.PLACE_ITEM) == len(instance.items)

    snapshot = controller.snapshot
    assert snapshot.summary is not None
    assert snapshot.summary.bins_used == result.solution.bins_used
    assert tuple(bin_.item_ids for bin_ in snapshot.bins) == tuple(
        bin_.item_ids for bin_ in result.solution.bins
    )


def test_catalog_enriches_current_item_without_entering_trace() -> None:
    instance, result = solved_demo()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))

    controller.advance()  # RunStarted
    frame = controller.advance()  # ItemSelected

    assert frame is not None
    assert frame.snapshot.current_item is not None
    assert frame.snapshot.current_item.id == "sofa"
    assert frame.snapshot.current_item.display_name == "Sofá"
    assert frame.snapshot.current_item.asset_id == "asset_sofa"
    assert frame.snapshot.item_order == ("sofa", "box", "bed", "tv")
    assert frame.snapshot.remaining_item_ids == ("box", "bed", "tv")


def test_rule_scores_reasons_and_selection_counts_are_available_for_frontend() -> None:
    instance, result = solved_demo()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))

    heuristic_frame = None
    while heuristic_frame is None:
        frame = controller.advance()
        assert frame is not None
        if frame.action.type is ReplayActionType.SELECT_HEURISTIC:
            heuristic_frame = frame

    snapshot = heuristic_frame.snapshot
    assert snapshot.selected_heuristic_id is not None
    assert snapshot.heuristic_scores
    assert snapshot.decision_reasons
    assert snapshot.heuristic_counts[snapshot.selected_heuristic_id] == 1


def test_play_pause_tick_and_speed_are_timer_agnostic() -> None:
    _, result = solved_demo()
    controller = ReplayController(result.trace, speed=2.0, base_interval_ms=800)

    assert controller.interval_ms == 400
    assert controller.tick() is None

    controller.play()
    assert controller.status is ReplayStatus.PLAYING
    assert controller.tick() is not None

    controller.pause()
    assert controller.status is ReplayStatus.PAUSED
    cursor = controller.snapshot.cursor
    assert controller.tick() is None
    assert controller.snapshot.cursor == cursor

    controller.set_speed(5.0)
    assert controller.interval_ms == 160


def test_advance_decision_stops_after_each_item_is_placed() -> None:
    instance, result = solved_demo()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))

    frame = controller.advance_decision()
    assert frame is not None
    assert frame.action.type is ReplayActionType.PLACE_ITEM
    assert frame.snapshot.current_item is None
    assert sum(len(bin_.item_ids) for bin_ in frame.snapshot.bins) == 1

    second = controller.advance_decision()
    assert second is not None
    assert second.action.type is ReplayActionType.PLACE_ITEM
    assert sum(len(bin_.item_ids) for bin_ in second.snapshot.bins) == 2


def test_seek_and_reset_are_deterministic() -> None:
    instance, result = solved_demo()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))

    placed_sequences = [
        event.sequence for event in result.trace.events if isinstance(event, ItemPlaced)
    ]
    target = placed_sequences[1]

    first = controller.seek_sequence(target)
    assert first is not None
    first_snapshot = first.snapshot

    controller.jump_to_end()
    controller.reset()
    second = controller.seek_sequence(target)
    assert second is not None

    assert second.snapshot.bins == first_snapshot.bins
    assert second.snapshot.heuristic_counts == first_snapshot.heuristic_counts
    assert second.snapshot.cursor == target


def test_seek_step_zero_reaches_first_completed_decision() -> None:
    _, result = solved_demo()
    controller = ReplayController(result.trace)
    frame = controller.seek_step(0)

    assert frame is not None
    assert frame.action.type is ReplayActionType.PLACE_ITEM
    assert sum(len(bin_.item_ids) for bin_ in frame.snapshot.bins) == 1


def test_subscriber_receives_frames_and_can_unsubscribe() -> None:
    _, result = solved_demo()
    controller = ReplayController(result.trace)
    frames = []
    unsubscribe = controller.subscribe(frames.append)

    controller.advance()
    assert len(frames) == 1
    unsubscribe()
    controller.advance()
    assert len(frames) == 1


def test_replay_reads_legacy_schema_1_0() -> None:
    _, result = solved_demo()
    raw = trace_to_json(result.trace).replace('"schema_version": "1.1"', '"schema_version": "1.0"')
    # The legacy reader accepts reasons if present; remove them by round-tripping
    # through normal JSON syntax is unnecessary for replay behavior.
    legacy = trace_from_json(raw)

    controller = ReplayController(legacy)
    controller.jump_to_end()
    assert controller.snapshot.summary is not None
    assert controller.status is ReplayStatus.FINISHED


def test_catalog_mismatch_is_rejected() -> None:
    instance, result = solved_demo()
    wrong = BinPackingInstance("other", "Other", 10, instance.items)
    with pytest.raises(ValueError, match="does not match"):
        ReplayController(result.trace, catalog=ReplayCatalog.from_instance(wrong))


def test_replay_detects_semantically_inconsistent_trace() -> None:
    _, result = solved_demo()
    raw_events = list(result.trace.events)
    index = next(i for i, event in enumerate(raw_events) if isinstance(event, ItemPlaced))
    original = raw_events[index]
    assert isinstance(original, ItemPlaced)
    # Dataclass constructor itself allows non-negative but semantically wrong capacity.
    raw_events[index] = ItemPlaced(
        sequence=original.sequence,
        step=original.step,
        timestamp_ns=original.timestamp_ns,
        item_id=original.item_id,
        bin_id=original.bin_id,
        used_capacity=original.used_capacity + 1,
        remaining_capacity=original.remaining_capacity - 1,
    )
    from impossible_move.trace.trace import RunTrace

    malformed = RunTrace(run_id=result.trace.run_id, events=tuple(raw_events))
    controller = ReplayController(malformed)
    with pytest.raises(ReplayConsistencyError, match="do not match"):
        controller.jump_to_end()


def test_invalid_speed_is_rejected() -> None:
    controller = ReplayController()
    with pytest.raises(ValueError):
        controller.set_speed(0)
    with pytest.raises(ValueError):
        controller.set_speed(float("inf"))


def test_next_interesting_skips_unavoidable_initial_opening_and_lands_on_complete_decision() -> None:
    instance, result = solved_demo()
    controller = ReplayController(result.trace, catalog=ReplayCatalog.from_instance(instance))

    frame = controller.advance_interesting()

    assert frame is not None
    assert frame.action.type is ReplayActionType.PLACE_ITEM
    # Step 0 necessarily opens the first truck and should not by itself count
    # as an interesting jump.  The demo's next object creates an exact fit.
    assert frame.snapshot.current_step == 1
    assert sum(len(bin_.item_ids) for bin_ in frame.snapshot.bins) == 2
