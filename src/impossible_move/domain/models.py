from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Iterable, Sequence

from .exceptions import (
    CapacityExceeded,
    DuplicateItemError,
    ItemAlreadyAssignedError,
    UnknownBinError,
)


class ItemCategory(str, Enum):
    FURNITURE = "furniture"
    APPLIANCE = "appliance"
    ELECTRONICS = "electronics"
    BOX = "box"
    DECORATION = "decoration"
    PERSONAL = "personal"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    size: int
    display_name: str
    category: ItemCategory = ItemCategory.OTHER
    asset_id: str = "generic"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("item id must be non-empty")
        if self.size <= 0:
            raise ValueError("item size must be positive")
        if not self.display_name.strip():
            raise ValueError("display_name must be non-empty")
        if not self.asset_id.strip():
            raise ValueError("asset_id must be non-empty")


@dataclass(frozen=True, slots=True)
class InstanceMetadata:
    difficulty: str | None = None
    description: str | None = None
    optimal_value: int | None = None

    def __post_init__(self) -> None:
        if self.optimal_value is not None and self.optimal_value < 0:
            raise ValueError("optimal_value must be non-negative when provided")


class Bin:
    """Mutable contents with immutable identity and capacity."""

    __slots__ = ("_id", "_capacity", "_items")

    def __init__(self, id: int, capacity: int, items: Iterable[Item] = ()) -> None:
        if id < 0:
            raise ValueError("bin id must be non-negative")
        if capacity <= 0:
            raise ValueError("bin capacity must be positive")
        self._id = id
        self._capacity = capacity
        self._items: list[Item] = []
        for item in items:
            self.add(item)

    @property
    def id(self) -> int:
        return self._id

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def items(self) -> tuple[Item, ...]:
        return tuple(self._items)

    @property
    def used_capacity(self) -> int:
        return sum(item.size for item in self._items)

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - self.used_capacity

    def can_fit(self, item: Item) -> bool:
        return item.size <= self.remaining_capacity

    def add(self, item: Item) -> None:
        if any(existing.id == item.id for existing in self._items):
            raise ItemAlreadyAssignedError(f"item {item.id!r} is already in bin {self.id}")
        if not self.can_fit(item):
            raise CapacityExceeded(
                f"item {item.id!r} (size={item.size}) does not fit in bin {self.id}; "
                f"remaining capacity={self.remaining_capacity}"
            )
        self._items.append(item)

    def __repr__(self) -> str:
        return f"Bin(id={self.id}, capacity={self.capacity}, items={self.items!r})"


@dataclass(frozen=True, slots=True)
class BinPackingInstance:
    id: str
    name: str
    capacity: int
    items: tuple[Item, ...]
    metadata: InstanceMetadata = field(default_factory=InstanceMetadata)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("instance id must be non-empty")
        if not self.name.strip():
            raise ValueError("instance name must be non-empty")
        if self.capacity <= 0:
            raise ValueError("instance capacity must be positive")

        ids = [item.id for item in self.items]
        if len(ids) != len(set(ids)):
            raise DuplicateItemError("item identifiers must be unique within an instance")

        too_large = [item.id for item in self.items if item.size > self.capacity]
        if too_large:
            raise CapacityExceeded("items exceed bin capacity: " + ", ".join(sorted(too_large)))

        optimum = self.metadata.optimal_value
        if optimum is not None:
            if not self.items and optimum != 0:
                raise ValueError("an empty instance has optimal_value 0")
            if self.items and not (self.volume_lower_bound <= optimum <= len(self.items)):
                raise ValueError(
                    "optimal_value must lie between the volume lower bound and the item count"
                )

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self.items)

    @property
    def volume_lower_bound(self) -> int:
        return ceil(self.total_size / self.capacity) if self.items else 0


class BinPackingState:
    """Mutable execution state with controlled transitions.

    An item is always in exactly one of three places: unassigned, current, or assigned.
    """

    __slots__ = ("instance", "_unassigned_items", "_bins", "current_item", "step")

    def __init__(
        self,
        instance: BinPackingInstance,
        unassigned_items: Sequence[Item],
        bins: Sequence[Bin] = (),
        current_item: Item | None = None,
        step: int = 0,
    ) -> None:
        self.instance = instance
        self._unassigned_items = list(unassigned_items)
        self._bins = list(bins)
        self.current_item = current_item
        self.step = step
        self.validate()

    @classmethod
    def from_instance(
        cls,
        instance: BinPackingInstance,
        ordered_items: Sequence[Item] | None = None,
    ) -> "BinPackingState":
        order = tuple(instance.items if ordered_items is None else ordered_items)
        expected_ids = [item.id for item in instance.items]
        actual_ids = [item.id for item in order]
        if len(actual_ids) != len(expected_ids) or set(actual_ids) != set(expected_ids):
            raise ValueError("ordered_items must be a permutation of the instance items")
        by_id = {item.id: item for item in instance.items}
        if any(by_id[item.id] != item for item in order):
            raise ValueError("ordered_items must contain the actual instance items")
        return cls(instance=instance, unassigned_items=order)

    @property
    def unassigned_items(self) -> tuple[Item, ...]:
        return tuple(self._unassigned_items)

    @property
    def bins(self) -> tuple[Bin, ...]:
        return tuple(self._bins)

    @property
    def has_pending_items(self) -> bool:
        return bool(self._unassigned_items) or self.current_item is not None

    @property
    def is_complete(self) -> bool:
        return not self._unassigned_items and self.current_item is None

    @property
    def assigned_item_count(self) -> int:
        return sum(len(bin_.items) for bin_ in self._bins)

    def validate(self) -> None:
        if self.step < 0:
            raise ValueError("step must be non-negative")

        instance_by_id = {item.id: item for item in self.instance.items}
        seen: set[str] = set()

        bin_ids = [bin_.id for bin_ in self._bins]
        if len(bin_ids) != len(set(bin_ids)):
            raise ValueError("bin identifiers must be unique")

        def register(item: Item, where: str) -> None:
            if item.id not in instance_by_id or instance_by_id[item.id] != item:
                raise ValueError(f"unknown or mismatched item {item.id!r} in {where}")
            if item.id in seen:
                raise ItemAlreadyAssignedError(f"item {item.id!r} appears more than once")
            seen.add(item.id)

        for item in self._unassigned_items:
            register(item, "unassigned_items")

        if self.current_item is not None:
            register(self.current_item, "current_item")

        for bin_ in self._bins:
            if bin_.capacity != self.instance.capacity:
                raise ValueError("all bins must use the instance capacity")
            if bin_.used_capacity > bin_.capacity:
                raise CapacityExceeded(f"bin {bin_.id} exceeds its capacity")
            for item in bin_.items:
                register(item, f"bin {bin_.id}")

        if seen != set(instance_by_id):
            missing = sorted(set(instance_by_id) - seen)
            raise ValueError(f"state does not account for every instance item; missing={missing!r}")

    def begin_next_item(self) -> Item:
        if self.current_item is not None:
            raise RuntimeError("cannot select another item while current_item is active")
        if not self._unassigned_items:
            raise RuntimeError("no unassigned items remain")
        self.current_item = self._unassigned_items.pop(0)
        self.validate()
        return self.current_item

    def view(self) -> "BinPackingStateView":
        self.validate()
        return BinPackingStateView(
            instance=self.instance,
            unassigned_items=self.unassigned_items,
            bins=tuple(BinSnapshot.from_bin(bin_) for bin_ in self._bins),
            current_item=self.current_item,
            step=self.step,
        )

    def get_bin(self, bin_id: int) -> Bin:
        for bin_ in self._bins:
            if bin_.id == bin_id:
                return bin_
        raise UnknownBinError(f"bin {bin_id} does not exist")

    def create_bin(self) -> Bin:
        next_id = max((bin_.id for bin_ in self._bins), default=-1) + 1
        bin_ = Bin(id=next_id, capacity=self.instance.capacity)
        self._bins.append(bin_)
        self.validate()
        return bin_

    def place_current_item(self, bin_id: int) -> Item:
        if self.current_item is None:
            raise RuntimeError("there is no current item to place")
        item = self.current_item
        self.get_bin(bin_id).add(item)
        self.current_item = None
        self.step += 1
        self.validate()
        return item


@dataclass(frozen=True, slots=True)
class BinSnapshot:
    id: int
    capacity: int
    item_ids: tuple[str, ...]
    used_capacity: int
    remaining_capacity: int

    def __post_init__(self) -> None:
        if self.id < 0:
            raise ValueError("bin snapshot id must be non-negative")
        if self.capacity <= 0:
            raise ValueError("bin snapshot capacity must be positive")
        if self.used_capacity < 0 or self.remaining_capacity < 0:
            raise ValueError("snapshot capacities must be non-negative")
        if self.used_capacity + self.remaining_capacity != self.capacity:
            raise ValueError("snapshot used and remaining capacity must sum to capacity")
        if len(self.item_ids) != len(set(self.item_ids)):
            raise DuplicateItemError("a bin snapshot cannot contain duplicate item ids")

    def can_fit(self, item: Item) -> bool:
        return item.size <= self.remaining_capacity

    @classmethod
    def from_bin(cls, bin_: Bin) -> "BinSnapshot":
        return cls(
            id=bin_.id,
            capacity=bin_.capacity,
            item_ids=tuple(item.id for item in bin_.items),
            used_capacity=bin_.used_capacity,
            remaining_capacity=bin_.remaining_capacity,
        )


@dataclass(frozen=True, slots=True)
class BinPackingStateView:
    instance: BinPackingInstance
    unassigned_items: tuple[Item, ...]
    bins: tuple[BinSnapshot, ...]
    current_item: Item | None
    step: int

    @property
    def has_pending_items(self) -> bool:
        return bool(self.unassigned_items) or self.current_item is not None

    @property
    def assigned_item_count(self) -> int:
        return sum(len(bin_.item_ids) for bin_ in self.bins)


@dataclass(frozen=True, slots=True)
class BinPackingSolution:
    instance_id: str
    bins: tuple[BinSnapshot, ...]
    total_size: int
    lower_bound: int

    def __post_init__(self) -> None:
        if not self.instance_id.strip():
            raise ValueError("instance_id must be non-empty")
        if self.total_size < 0 or self.lower_bound < 0:
            raise ValueError("solution totals must be non-negative")
        bin_ids = [bin_.id for bin_ in self.bins]
        if len(bin_ids) != len(set(bin_ids)):
            raise ValueError("solution bin ids must be unique")
        item_ids = [item_id for bin_ in self.bins for item_id in bin_.item_ids]
        if len(item_ids) != len(set(item_ids)):
            raise DuplicateItemError("an item cannot appear in multiple solution bins")
        if sum(bin_.used_capacity for bin_ in self.bins) != self.total_size:
            raise ValueError("solution total_size must equal the sum of used bin capacities")
        if self.bins and self.lower_bound > len(self.bins):
            raise ValueError("lower_bound cannot exceed the number of bins used")

    @classmethod
    def from_state(cls, state: BinPackingState) -> "BinPackingSolution":
        if not state.is_complete:
            raise ValueError("cannot create final solution before the state is complete")
        state.validate()
        return cls(
            instance_id=state.instance.id,
            bins=tuple(BinSnapshot.from_bin(bin_) for bin_ in state.bins),
            total_size=state.instance.total_size,
            lower_bound=state.instance.volume_lower_bound,
        )

    @property
    def bins_used(self) -> int:
        return len(self.bins)

    @property
    def total_capacity(self) -> int:
        return sum(bin_.capacity for bin_ in self.bins)

    @property
    def unused_capacity(self) -> int:
        return self.total_capacity - self.total_size

    @property
    def utilization(self) -> float:
        return self.total_size / self.total_capacity if self.total_capacity else 1.0
