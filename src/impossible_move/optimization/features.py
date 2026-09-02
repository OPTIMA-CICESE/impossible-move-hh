from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from impossible_move.domain.models import BinPackingStateView


def extract_bin_packing_features(state: BinPackingStateView) -> Mapping[str, float]:
    """Extract the shared, interpretable state vector used by trace and HH logic.

    The function is deliberately pure: both the trace observer and explainable
    hyper-heuristics call this exact implementation, preventing feature drift
    between what the optimizer uses and what the frontend later displays.
    """

    item = state.current_item
    if item is None:
        raise RuntimeError("feature extraction requires an active current_item")

    capacity = state.instance.capacity
    remaining = [bin_.remaining_capacity for bin_ in state.bins]
    total_capacity = sum(bin_.capacity for bin_ in state.bins)
    used_capacity = sum(bin_.used_capacity for bin_ in state.bins)

    feasible = [bin_ for bin_ in state.bins if bin_.can_fit(item)]
    remaining_after = [bin_.remaining_capacity - item.size for bin_ in feasible]
    exact_fit_bins = sum(1 for residual in remaining_after if residual == 0)

    if remaining_after:
        min_after = min(remaining_after)
        max_after = max(remaining_after)
        residual_spread = (max_after - min_after) / capacity
    else:
        min_after = 0
        max_after = 0
        residual_spread = 0.0

    if state.bins:
        last_bin = state.bins[-1]
        last_feasible = last_bin.can_fit(item)
        last_after = last_bin.remaining_capacity - item.size if last_feasible else 0
    else:
        last_feasible = False
        last_after = 0

    features = {
        "open_bins": float(len(state.bins)),
        "current_item_size": float(item.size),
        "item_ratio": float(item.size / capacity),
        "remaining_items": float(len(state.unassigned_items)),
        "mean_remaining_capacity": (
            float(sum(remaining) / len(remaining)) if remaining else 0.0
        ),
        "max_remaining_capacity": float(max(remaining)) if remaining else 0.0,
        "utilization": float(used_capacity / total_capacity) if total_capacity else 0.0,
        "feasible_bins": float(len(feasible)),
        "feasible_ratio": float(len(feasible) / len(state.bins)) if state.bins else 0.0,
        "exact_fit_bins": float(exact_fit_bins),
        "min_remaining_after": float(min_after),
        "max_remaining_after": float(max_after),
        "residual_spread": float(residual_spread),
        "last_bin_feasible": 1.0 if last_feasible else 0.0,
        "last_bin_remaining_after": float(last_after),
    }
    return MappingProxyType(features)
