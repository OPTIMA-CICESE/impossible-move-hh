import pytest

from impossible_move.explainability import DecisionReason
from impossible_move.trace.events import (
    HeuristicSelected,
    ItemSelected,
    RunFinished,
    RunStarted,
    StateObserved,
)
from impossible_move.trace.serialization import trace_from_json, trace_to_json
from impossible_move.trace.trace import RunTrace


def complete_trace() -> RunTrace:
    return RunTrace(
        run_id="run-1",
        events=(
            RunStarted(
                sequence=0,
                step=0,
                timestamp_ns=1,
                run_id="run-1",
                instance_id="demo",
                hyper_heuristic_id="random",
                heuristic_ids=("ff", "bf"),
                item_order=("sofa",),
            ),
            ItemSelected(
                sequence=1,
                step=0,
                timestamp_ns=2,
                item_id="sofa",
                size=8,
                remaining_items=0,
            ),
            StateObserved(
                sequence=2,
                step=0,
                timestamp_ns=3,
                features={"current_item_size": 8.0},
            ),
            HeuristicSelected(
                sequence=3,
                step=0,
                timestamp_ns=4,
                heuristic_id="bf",
                scores={"ff": 0.2, "bf": 0.8},
                reasons=(DecisionReason("exact_fit", "bf", 0.8),),
            ),
            RunFinished(
                sequence=4,
                step=1,
                timestamp_ns=5,
                bins_used=1,
                total_capacity=10,
                used_capacity=8,
                unused_capacity=2,
                utilization=0.8,
                lower_bound=1,
            ),
        ),
    )


def test_trace_round_trip_json() -> None:
    trace = complete_trace()
    restored = trace_from_json(trace_to_json(trace))
    assert restored == trace


def test_trace_mappings_are_immutable() -> None:
    event = complete_trace().events[2]
    assert isinstance(event, StateObserved)
    with pytest.raises(TypeError):
        event.features["x"] = 1.0  # type: ignore[index]


def test_trace_events_for_step() -> None:
    trace = complete_trace()
    assert len(trace.events_for_step(1)) == 1
    assert isinstance(trace.events_for_step(1)[0], RunFinished)


def test_trace_rejects_non_contiguous_sequences() -> None:
    with pytest.raises(ValueError, match="contiguous"):
        RunTrace(
            run_id="run-1",
            events=(ItemSelected(sequence=1, step=0, item_id="a", size=1, remaining_items=0),),
        )


def test_trace_reader_accepts_legacy_schema_1_0_without_reasons() -> None:
    raw = trace_to_json(complete_trace())
    raw = raw.replace('"schema_version": "1.2"', '"schema_version": "1.0"')
    raw = raw.replace(',\n      "reasons": [\n        {\n          "rule_id": "exact_fit",\n          "heuristic_id": "bf",\n          "contribution": 0.8\n        }\n      ]', '')
    restored = trace_from_json(raw)
    assert restored.schema_version == "1.0"
    event = next(event for event in restored.events if isinstance(event, HeuristicSelected))
    assert event.reasons == ()
