from collections import defaultdict

import pytest

from impossible_move.domain.models import Bin, BinPackingInstance, BinPackingState, Item
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.optimization.contracts import LowLevelHeuristic


def item(id_: str, size: int) -> Item:
    return Item(id=id_, size=size, display_name=id_)


def state_for_current(current: Item, remaining_by_bin: tuple[int, ...]) -> BinPackingState:
    fillers = tuple(
        item(f"filler-{index}", 10 - remaining)
        for index, remaining in enumerate(remaining_by_bin)
        if remaining < 10
    )
    instance = BinPackingInstance("demo", "Demo", 10, (current,) + fillers)
    filler_by_id = {obj.id: obj for obj in fillers}
    bins = []
    for index, remaining in enumerate(remaining_by_bin):
        bin_ = Bin(index, 10)
        filler = filler_by_id.get(f"filler-{index}")
        if filler is not None:
            bin_.add(filler)
        bins.append(bin_)
    return BinPackingState(instance, (), bins=bins, current_item=current)


def heuristics() -> list[LowLevelHeuristic]:
    return [FirstFit(), BestFit(), WorstFit(), NextFit()]


def assert_reasons_reconstruct_scores(selection) -> None:
    totals = defaultdict(float)
    for reason in selection.reasons:
        totals[reason.heuristic_id] += reason.contribution
    assert selection.scores is not None
    assert dict(selection.scores) == pytest.approx(dict(totals))


def test_exact_fit_strongly_selects_best_fit() -> None:
    state = state_for_current(item("x", 6), (2, 6, 9))
    selection = ExplainableRuleBasedHH().select(state.view(), heuristics())
    assert selection.heuristic_id == "best_fit"
    assert any(reason.rule_id == "exact_fit" for reason in selection.reasons)
    assert_reasons_reconstruct_scores(selection)


def test_small_item_with_multiple_options_selects_worst_fit() -> None:
    state = state_for_current(item("x", 2), (6, 8))
    selection = ExplainableRuleBasedHH().select(state.view(), heuristics())
    assert selection.heuristic_id == "worst_fit"
    assert any(reason.rule_id == "small_item_many_options" for reason in selection.reasons)
    assert_reasons_reconstruct_scores(selection)


def test_tight_last_bin_selects_next_fit() -> None:
    state = state_for_current(item("x", 4), (6, 6))
    selection = ExplainableRuleBasedHH().select(state.view(), heuristics())
    assert selection.heuristic_id == "next_fit"
    assert any(reason.rule_id == "tight_last_bin" for reason in selection.reasons)
    assert_reasons_reconstruct_scores(selection)


def test_large_item_selects_best_fit() -> None:
    state = state_for_current(item("x", 6), (8, 9))
    selection = ExplainableRuleBasedHH().select(state.view(), heuristics())
    assert selection.heuristic_id == "best_fit"
    assert any(reason.rule_id == "large_item" for reason in selection.reasons)


def test_no_existing_fit_selects_first_fit() -> None:
    state = state_for_current(item("x", 7), (2, 3))
    selection = ExplainableRuleBasedHH().select(state.view(), heuristics())
    assert selection.heuristic_id == "first_fit"
    assert any(reason.rule_id == "no_existing_fit" for reason in selection.reasons)


def test_rule_based_hh_rejects_unsupported_heuristics() -> None:
    class Unsupported(LowLevelHeuristic):
        id = "unsupported"
        display_name = "Unsupported"

        def choose_placement(self, item, state):  # pragma: no cover - never called
            raise AssertionError

    state = state_for_current(item("x", 4), (8,))
    with pytest.raises(ValueError, match="unsupported"):
        ExplainableRuleBasedHH().select(state.view(), [FirstFit(), Unsupported()])
