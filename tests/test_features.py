from impossible_move.domain.models import Bin, BinPackingInstance, BinPackingState, Item
from impossible_move.optimization.features import extract_bin_packing_features


def item(id_: str, size: int) -> Item:
    return Item(id=id_, size=size, display_name=id_)


def test_shared_feature_extractor_describes_current_placement_state() -> None:
    current = item("current", 4)
    fillers = (item("a", 8), item("b", 4), item("c", 2))
    instance = BinPackingInstance("demo", "Demo", 10, (current,) + fillers)
    bins = (
        Bin(0, 10, (fillers[0],)),  # remaining 2: infeasible
        Bin(1, 10, (fillers[1],)),  # remaining 6: after 2
        Bin(2, 10, (fillers[2],)),  # remaining 8: after 4
    )
    state = BinPackingState(instance, (), bins=bins, current_item=current)

    features = extract_bin_packing_features(state.view())

    assert features["open_bins"] == 3.0
    assert features["item_ratio"] == 0.4
    assert features["feasible_bins"] == 2.0
    assert features["feasible_ratio"] == 2 / 3
    assert features["exact_fit_bins"] == 0.0
    assert features["min_remaining_after"] == 2.0
    assert features["max_remaining_after"] == 4.0
    assert features["residual_spread"] == 0.2
    assert features["last_bin_feasible"] == 1.0
    assert features["last_bin_remaining_after"] == 4.0


def test_feature_extractor_reports_exact_fit() -> None:
    current = item("current", 6)
    filler = item("filler", 4)
    instance = BinPackingInstance("demo", "Demo", 10, (current, filler))
    state = BinPackingState(instance, (), bins=(Bin(0, 10, (filler,)),), current_item=current)
    features = extract_bin_packing_features(state.view())
    assert features["exact_fit_bins"] == 1.0
    assert features["min_remaining_after"] == 0.0
