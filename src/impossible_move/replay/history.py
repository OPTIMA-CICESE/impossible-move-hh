from __future__ import annotations

from collections import defaultdict
from typing import Any

from impossible_move.trace.events import HeuristicSelected, ItemPlaced, ItemSelected, PlacementSelected
from impossible_move.trace.trace import RunTrace
from .catalog import ReplayCatalog


def decision_history(trace: RunTrace, catalog: ReplayCatalog | None = None) -> list[dict[str, Any]]:
    """Extract one stable history record per HH decision from a RunTrace."""
    by_step: dict[int, dict[str, Any]] = defaultdict(dict)
    for event in trace.events:
        row = by_step[event.step]
        if isinstance(event, ItemSelected):
            row.update(item_id=event.item_id, item_size=event.size)
        elif isinstance(event, HeuristicSelected):
            row.update(
                heuristic_id=event.heuristic_id,
                scores=dict(event.scores or {}),
                reasons=[
                    {
                        "rule_id": reason.rule_id,
                        "heuristic_id": reason.heuristic_id,
                        "contribution": reason.contribution,
                    }
                    for reason in event.reasons
                ],
            )
        elif isinstance(event, PlacementSelected):
            row.update(selected_bin_id=event.bin_id, create_new_bin=event.create_new_bin)
        elif isinstance(event, ItemPlaced):
            row.update(
                placed_bin_id=event.bin_id,
                used_after=event.used_capacity,
                remaining_after=event.remaining_capacity,
            )

    result: list[dict[str, Any]] = []
    decision_no = 0
    for step in sorted(by_step):
        row = by_step[step]
        if "heuristic_id" not in row:
            continue
        decision_no += 1
        item_id = str(row.get("item_id", ""))
        info = catalog.items.get(item_id) if catalog is not None else None
        item_size = int(row.get("item_size", info.size if info else 0))
        remaining_after = row.get("remaining_after")
        used_after = row.get("used_after")
        result.append(
            {
                "decision": decision_no,
                "step": step,
                "item_id": item_id,
                "item_size": item_size,
                "asset_id": info.asset_id if info else "generic",
                "display_name": info.display_name if info else item_id,
                "heuristic_id": str(row["heuristic_id"]),
                "scores": dict(row.get("scores", {})),
                "reasons": list(row.get("reasons", [])),
                "bin_id": int(row.get("placed_bin_id", row.get("selected_bin_id", -1))),
                "create_new_bin": bool(row.get("create_new_bin", False)),
                "used_before": (int(used_after) - item_size) if used_after is not None else None,
                "used_after": int(used_after) if used_after is not None else None,
                "remaining_before": (int(remaining_after) + item_size) if remaining_after is not None else None,
                "remaining_after": int(remaining_after) if remaining_after is not None else None,
            }
        )
    return result
