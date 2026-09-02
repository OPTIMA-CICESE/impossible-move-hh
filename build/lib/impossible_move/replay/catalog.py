from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from impossible_move.domain.models import BinPackingInstance, ItemCategory


@dataclass(frozen=True, slots=True)
class ReplayItemInfo:
    id: str
    display_name: str
    size: int
    category: str = ItemCategory.OTHER.value
    asset_id: str = "generic"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("replay item id must be non-empty")
        if not self.display_name.strip():
            raise ValueError("replay item display_name must be non-empty")
        if self.size <= 0:
            raise ValueError("replay item size must be positive")
        if not self.category.strip():
            raise ValueError("replay item category must be non-empty")
        if not self.asset_id.strip():
            raise ValueError("replay item asset_id must be non-empty")


@dataclass(frozen=True, slots=True)
class ReplayCatalog:
    """Presentation metadata kept separate from the optimization trace.

    The trace only needs stable item identifiers and mathematical values.  The
    catalog enriches those identifiers with labels and asset ids for a frontend.
    """

    instance_id: str
    items: Mapping[str, ReplayItemInfo]
    bin_capacity: int | None = None

    def __post_init__(self) -> None:
        if not self.instance_id.strip():
            raise ValueError("catalog instance_id must be non-empty")
        if self.bin_capacity is not None and self.bin_capacity <= 0:
            raise ValueError("catalog bin_capacity must be positive when provided")
        copied = dict(self.items)
        if any(key != item.id for key, item in copied.items()):
            raise ValueError("catalog mapping keys must match ReplayItemInfo.id")
        object.__setattr__(self, "items", MappingProxyType(copied))

    @classmethod
    def from_instance(cls, instance: BinPackingInstance) -> "ReplayCatalog":
        return cls(
            instance_id=instance.id,
            bin_capacity=instance.capacity,
            items={
                item.id: ReplayItemInfo(
                    id=item.id,
                    display_name=item.display_name,
                    size=item.size,
                    category=item.category.value,
                    asset_id=item.asset_id,
                )
                for item in instance.items
            },
        )

    def get(self, item_id: str, *, fallback_size: int | None = None) -> ReplayItemInfo:
        try:
            return self.items[item_id]
        except KeyError:
            if fallback_size is None:
                raise
            return ReplayItemInfo(
                id=item_id,
                display_name=item_id,
                size=fallback_size,
            )
