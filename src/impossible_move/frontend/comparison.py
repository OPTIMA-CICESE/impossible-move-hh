from __future__ import annotations

from typing import Any

from impossible_move.experiments.comparison import ResolvedComparison
from impossible_move.replay import ReplayController, ReplayMode
from impossible_move.trace.events import BinCreated, ItemPlaced
from impossible_move.replay.history import decision_history

from .i18n import DEFAULT_LANGUAGE, tr
from .presenter import snapshot_to_view_model, heuristic_label


class ComparisonReplayController:
    """Decision-synchronous player for multiple policies on the same instance."""

    def __init__(self, resolved: ResolvedComparison) -> None:
        self.resolved = resolved
        self.controllers = {
            policy_id: ReplayController(run.trace, catalog=run.catalog, mode=ReplayMode.PRESENTATION)
            for policy_id, run in self.resolved.runs.items()
        }
        self.decision = 0
        self.total_decisions = len(self.resolved.instance.items)
        self.curves = {policy_id: _bins_curve(run.trace) for policy_id, run in self.resolved.runs.items()}

    def reset(self) -> None:
        for controller in self.controllers.values():
            controller.reset()
        self.decision = 0

    @property
    def finished(self) -> bool:
        return self.decision >= self.total_decisions

    def advance_decision(self) -> None:
        if self.finished:
            return
        for controller in self.controllers.values():
            controller.advance_decision()
        self.decision += 1

    def jump_to_end(self) -> None:
        while not self.finished:
            self.advance_decision()

    def set_mode(self, mode: ReplayMode) -> None:
        for controller in self.controllers.values():
            controller.set_mode(mode)


def _method_label(policy_id: str, fixed_id: str, language: str) -> str:
    if policy_id == "adaptive":
        return tr("comparison_adaptive", language)
    if policy_id == "random":
        return tr("comparison_random", language)
    return tr("comparison_fixed_named", language, heuristic=heuristic_label(fixed_id))


def _bins_curve(trace) -> list[int]:
    bins = 0
    curve: list[int] = []
    for event in trace.events:
        if isinstance(event, BinCreated):
            bins += 1
        elif isinstance(event, ItemPlaced):
            curve.append(bins)
    return curve




def _placement_map(trace) -> dict[str, int]:
    return {event.item_id: event.bin_id for event in trace.events if isinstance(event, ItemPlaced)}


def move_explorer_view(controller: ComparisonReplayController, language: str) -> dict[str, Any]:
    from .i18n import localized_item_name

    placement_maps = {
        policy_id: _placement_map(run.trace)
        for policy_id, run in controller.resolved.runs.items()
    }
    policy_labels = {
        policy_id: _method_label(policy_id, controller.resolved.fixed_heuristic_id, language)
        for policy_id in controller.resolved.selected_policies
    }
    rows: list[dict[str, Any]] = []
    grouped: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(controller.resolved.instance.items):
        processed = index < controller.decision
        current = index == controller.decision and controller.decision < controller.total_decisions
        placements = []
        for policy_id in controller.resolved.selected_policies:
            bin_id = placement_maps.get(policy_id, {}).get(item.id) if processed else None
            placements.append({
                "policyId": policy_id,
                "policyLabel": policy_labels[policy_id],
                "binId": (bin_id + 1) if bin_id is not None else None,
            })
        row = {
            "index": index,
            "id": item.id,
            "displayName": localized_item_name(item.asset_id, item.display_name, language),
            "size": item.size,
            "assetId": item.asset_id,
            "category": item.category.value,
            "processed": processed,
            "current": current,
            "pending": not processed and not current,
            "placements": placements,
        }
        rows.append(row)
        key = item.asset_id or item.category.value
        group = grouped.setdefault(key, {
            "key": key,
            "displayName": localized_item_name(item.asset_id, item.display_name, language),
            "assetId": item.asset_id,
            "total": 0,
            "processed": 0,
            "pending": 0,
            "totalSize": 0,
        })
        group["total"] += 1
        group["totalSize"] += item.size
        if processed:
            group["processed"] += 1
        else:
            group["pending"] += 1
    groups = sorted(grouped.values(), key=lambda g: (-g["total"], g["displayName"]))
    return {
        "items": rows,
        "groups": groups,
        "itemCount": len(rows),
        "totalSize": controller.resolved.instance.total_size,
        "decision": controller.decision,
        "totalDecisions": controller.total_decisions,
        "capacity": controller.resolved.instance.capacity,
    }

def comparison_view(controller: ComparisonReplayController, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    methods: list[dict[str, Any]] = []
    for policy_id in controller.resolved.selected_policies:
        run = controller.resolved.runs[policy_id]
        rc = controller.controllers[policy_id]
        vm = snapshot_to_view_model(rc.snapshot, run.catalog, language=language)
        counts = vm.get("heuristicCounts", [])
        methods.append(
            {
                "id": policy_id,
                "label": _method_label(policy_id, controller.resolved.fixed_heuristic_id, language),
                "selectedHeuristicId": vm.get("selectedHeuristicId", ""),
                "selectedHeuristicLabel": vm.get("selectedHeuristicLabel", ""),
                "binsUsed": vm["summary"]["binsUsed"],
                "utilization": vm["summary"]["utilization"],
                "lowerBound": run.lower_bound,
                "gap": vm["summary"]["binsUsed"] - run.lower_bound,
                "finalBins": run.bins_used,
                "finalGap": run.gap,
                "finished": vm["summary"]["finished"],
                "compactBins": vm.get("compactBins", []),
                "focusedBin": vm.get("focusedBin", {}),
                "heuristicCounts": counts if policy_id != "fixed" else [],
                "fixedHeuristicLabel": heuristic_label(controller.resolved.fixed_heuristic_id) if policy_id == "fixed" else "",
                "curve": controller.curves.get(policy_id, []),
            }
        )
    item = {}
    if methods:
        first_id = controller.resolved.selected_policies[0]
        first_run = controller.resolved.runs[first_id]
        history = decision_history(first_run.trace, first_run.catalog)
        if history:
            idx = min(max(controller.decision - 1, 0), len(history) - 1)
            row = history[idx]
            info = first_run.catalog.items.get(row["item_id"])
            if info is not None:
                from .i18n import localized_item_name
                item = {
                    "id": info.id,
                    "displayName": localized_item_name(info.asset_id, info.display_name, language),
                    "size": info.size,
                    "assetId": info.asset_id,
                    "category": info.category,
                }
    best_fixed = {}
    if controller.resolved.best_fixed_heuristic_id is not None:
        adaptive_run = controller.resolved.runs.get("adaptive")
        delta = controller.resolved.adaptive_delta_to_best_fixed
        best_fixed = {
            "heuristicId": controller.resolved.best_fixed_heuristic_id,
            "heuristicLabel": heuristic_label(controller.resolved.best_fixed_heuristic_id),
            "bins": controller.resolved.best_fixed_bins,
            "adaptiveBins": adaptive_run.bins_used if adaptive_run is not None else None,
            "delta": delta,
            "classification": controller.resolved.adaptive_classification,
            "benchmarks": [
                {"heuristicId": hid, "heuristicLabel": heuristic_label(hid), "bins": bins}
                for hid, bins in controller.resolved.fixed_benchmarks.items()
            ],
        }

    return {
        "active": True,
        "methodCount": len(methods),
        "decision": controller.decision,
        "totalDecisions": controller.total_decisions,
        "progress": controller.decision / controller.total_decisions if controller.total_decisions else 0.0,
        "finished": controller.finished,
        "currentItem": item,
        "methods": methods,
        "moveItemCount": controller.total_decisions,
        "moveTotalSize": controller.resolved.instance.total_size,
        "moveCapacity": controller.resolved.instance.capacity,
        "lowerBound": next(iter(controller.resolved.runs.values())).lower_bound if controller.resolved.runs else 0,
        "bestFixed": best_fixed,
    }
