from impossible_move.domain.models import Bin, BinPackingInstance, BinPackingState, Item
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit


def item(id_: str, size: int) -> Item:
    return Item(id=id_, size=size, display_name=id_)


def state_for_current(current: Item, remaining_by_bin: tuple[int, ...]) -> BinPackingState:
    fillers = tuple(
        item(f"filler-{index}", 10 - remaining)
        for index, remaining in enumerate(remaining_by_bin)
        if remaining < 10
    )
    all_items = (current,) + fillers
    instance = BinPackingInstance("demo", "Demo", 10, all_items)
    bins = []
    filler_by_id = {obj.id: obj for obj in fillers}
    for index, remaining in enumerate(remaining_by_bin):
        bin_ = Bin(index, 10)
        filler = filler_by_id.get(f"filler-{index}")
        if filler is not None:
            bin_.add(filler)
        bins.append(bin_)
    return BinPackingState(instance, (), bins=bins, current_item=current)


def test_first_fit_selects_first_feasible_bin_and_stops_evaluating() -> None:
    current = item("x", 4)
    state = state_for_current(current, (2, 5, 8))
    result = FirstFit().choose_placement(current, state.view())
    assert result.decision.bin_id == 1
    assert [evaluation.bin_id for evaluation in result.evaluations] == [0, 1]


def test_best_fit_minimizes_remaining_space() -> None:
    current = item("x", 4)
    state = state_for_current(current, (2, 5, 8))
    result = BestFit().choose_placement(current, state.view())
    assert result.decision.bin_id == 1
    assert len(result.evaluations) == 3


def test_worst_fit_maximizes_remaining_space() -> None:
    current = item("x", 4)
    state = state_for_current(current, (2, 5, 8))
    result = WorstFit().choose_placement(current, state.view())
    assert result.decision.bin_id == 2


def test_next_fit_only_considers_last_bin() -> None:
    current = item("x", 4)
    state = state_for_current(current, (8, 3))
    result = NextFit().choose_placement(current, state.view())
    assert result.decision.create_new_bin
    assert [evaluation.bin_id for evaluation in result.evaluations] == [1]
