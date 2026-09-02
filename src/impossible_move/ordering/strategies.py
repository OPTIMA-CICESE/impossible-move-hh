from __future__ import annotations

from collections.abc import Sequence

from impossible_move.domain.models import Item
from impossible_move.optimization.contracts import ItemOrderingStrategy


class OriginalOrder(ItemOrderingStrategy):
    id = "original"

    def order(self, items: Sequence[Item]) -> list[Item]:
        return list(items)


class DecreasingSize(ItemOrderingStrategy):
    id = "decreasing_size"

    def order(self, items: Sequence[Item]) -> list[Item]:
        return sorted(items, key=lambda item: item.size, reverse=True)
