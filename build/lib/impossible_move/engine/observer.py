from __future__ import annotations

from typing import Mapping, Protocol

from impossible_move.domain.models import BinPackingStateView
from impossible_move.optimization.features import extract_bin_packing_features


class StateObserver(Protocol):
    def observe(self, state: BinPackingStateView) -> Mapping[str, float]:
        """Extract the features exposed to the trace."""
        ...


class DefaultStateObserver:
    """Expose the same interpretable feature vector consumed by the rule HH."""

    def observe(self, state: BinPackingStateView) -> Mapping[str, float]:
        return extract_bin_packing_features(state)
