import pytest

from impossible_move.domain.exceptions import (
    CapacityExceeded,
    DuplicateItemError,
    ItemAlreadyAssignedError,
)
from impossible_move.domain.models import (
    Bin,
    BinPackingInstance,
    BinPackingSolution,
    BinPackingState,
    Item,
    ItemCategory,
)


def item(id_: str, size: int) -> Item:
    return Item(
        id=id_,
        size=size,
        display_name=id_,
        category=ItemCategory.BOX,
        asset_id="box",
    )


def test_instance_lower_bound() -> None:
    instance = BinPackingInstance(
        id="demo",
        name="Demo",
        capacity=10,
        items=(item("a", 8), item("b", 7), item("c", 5)),
    )
    assert instance.total_size == 20
    assert instance.volume_lower_bound == 2


def test_instance_rejects_duplicate_ids() -> None:
    with pytest.raises(DuplicateItemError):
        BinPackingInstance(
            id="demo",
            name="Demo",
            capacity=10,
            items=(item("a", 5), item("a", 4)),
        )


def test_instance_rejects_oversized_item() -> None:
    with pytest.raises(CapacityExceeded):
        BinPackingInstance(
            id="demo",
            name="Demo",
            capacity=10,
            items=(item("a", 11),),
        )


def test_bin_enforces_capacity_and_does_not_expose_mutable_items() -> None:
    bin_ = Bin(id=0, capacity=10)
    bin_.add(item("a", 7))
    assert bin_.remaining_capacity == 3
    assert isinstance(bin_.items, tuple)
    with pytest.raises(CapacityExceeded):
        bin_.add(item("b", 4))


def test_bin_rejects_duplicate_item() -> None:
    bin_ = Bin(id=0, capacity=10)
    a = item("a", 2)
    bin_.add(a)
    with pytest.raises(ItemAlreadyAssignedError):
        bin_.add(a)


def test_state_lifecycle_accounts_for_every_item_exactly_once() -> None:
    items = (item("a", 3), item("b", 4))
    instance = BinPackingInstance(id="demo", name="Demo", capacity=10, items=items)
    state = BinPackingState.from_instance(instance)
    assert state.unassigned_items == items
    assert state.bins == ()
    assert state.step == 0

    current = state.begin_next_item()
    assert current.id == "a"
    assert state.current_item == current
    assert [obj.id for obj in state.unassigned_items] == ["b"]

    truck = state.create_bin()
    state.place_current_item(truck.id)
    assert state.current_item is None
    assert state.step == 1
    assert state.assigned_item_count == 1


def test_state_rejects_duplicate_bin_ids() -> None:
    a = item("a", 3)
    instance = BinPackingInstance(id="demo", name="Demo", capacity=10, items=(a,))
    with pytest.raises(ValueError, match="bin identifiers"):
        BinPackingState(instance, (), bins=(Bin(0, 10, (a,)), Bin(0, 10)))


def test_solution_requires_complete_state() -> None:
    a = item("a", 3)
    instance = BinPackingInstance(id="demo", name="Demo", capacity=10, items=(a,))
    state = BinPackingState.from_instance(instance)
    state.begin_next_item()
    with pytest.raises(ValueError, match="complete"):
        BinPackingSolution.from_state(state)


def test_state_view_is_immutable_and_bins_are_snapshots() -> None:
    a = item("a", 3)
    instance = BinPackingInstance(id="demo", name="Demo", capacity=10, items=(a,))
    state = BinPackingState.from_instance(instance)
    state.begin_next_item()
    truck = state.create_bin()
    view = state.view()

    assert view.current_item == a
    assert view.bins[0].id == truck.id
    assert not hasattr(view.bins[0], "add")
    with pytest.raises(AttributeError):
        view.step = 99  # type: ignore[misc]


def test_bin_identity_and_capacity_cannot_be_reassigned() -> None:
    bin_ = Bin(0, 10)
    with pytest.raises(AttributeError):
        bin_.capacity = 99  # type: ignore[misc]
    with pytest.raises(AttributeError):
        bin_.id = 4  # type: ignore[misc]
