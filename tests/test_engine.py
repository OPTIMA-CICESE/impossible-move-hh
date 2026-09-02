from impossible_move.domain.models import BinPackingInstance, Item
from impossible_move.engine import BinPackingEngine
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH, RandomHyperHeuristic
from impossible_move.ordering import DecreasingSize, OriginalOrder
from impossible_move.trace.events import (
    BinCreated,
    HeuristicSelected,
    ItemPlaced,
    RunFinished,
    RunStarted,
)
from impossible_move.trace.serialization import trace_from_json, trace_to_json


def item(id_: str, size: int) -> Item:
    return Item(id=id_, size=size, display_name=id_)


def test_engine_produces_complete_solution_and_replayable_trace() -> None:
    instance = BinPackingInstance(
        "demo",
        "Demo",
        10,
        (item("a", 8), item("b", 2), item("c", 7), item("d", 3)),
    )
    engine = BinPackingEngine()
    result = engine.solve(
        instance,
        RandomHyperHeuristic(seed=3),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        DecreasingSize(),
        run_id="test-run",
    )

    assert result.solution.total_size == 20
    assert result.solution.bins_used >= result.solution.lower_bound == 2
    assert isinstance(result.trace.events[0], RunStarted)
    assert isinstance(result.trace.events[-1], RunFinished)
    assert len([event for event in result.trace.events if isinstance(event, ItemPlaced)]) == 4
    assert any(isinstance(event, BinCreated) for event in result.trace.events)
    assert len([event for event in result.trace.events if isinstance(event, HeuristicSelected)]) == 4
    assert trace_from_json(trace_to_json(result.trace)) == result.trace


def test_seeded_random_hh_is_reproducible_across_runs() -> None:
    instance = BinPackingInstance(
        "demo",
        "Demo",
        10,
        tuple(item(str(index), size) for index, size in enumerate((6, 4, 5, 5, 3, 7, 2, 8))),
    )
    engine = BinPackingEngine()
    hh = RandomHyperHeuristic(seed=11)
    heuristics = [FirstFit(), BestFit(), WorstFit(), NextFit()]

    first = engine.solve(instance, hh, heuristics, OriginalOrder(), run_id="run-1")
    second = engine.solve(instance, hh, heuristics, OriginalOrder(), run_id="run-2")

    first_choices = [
        event.heuristic_id for event in first.trace.events if isinstance(event, HeuristicSelected)
    ]
    second_choices = [
        event.heuristic_id for event in second.trace.events if isinstance(event, HeuristicSelected)
    ]
    assert first_choices == second_choices


def test_explainable_hh_emits_auditable_reasons_in_trace() -> None:
    instance = BinPackingInstance(
        "demo-rules",
        "Demo Rules",
        10,
        tuple(item(str(index), size) for index, size in enumerate((8, 2, 6, 4, 3, 3, 7, 1))),
    )
    result = BinPackingEngine().solve(
        instance,
        ExplainableRuleBasedHH(),
        [FirstFit(), BestFit(), WorstFit(), NextFit()],
        OriginalOrder(),
        run_id="rule-run",
    )
    selections = [
        event for event in result.trace.events if isinstance(event, HeuristicSelected)
    ]
    assert selections
    assert result.trace.schema_version == "1.2"
    assert all(selection.scores is not None for selection in selections)
    assert all(selection.reasons for selection in selections)
    assert trace_from_json(trace_to_json(result.trace)) == result.trace
