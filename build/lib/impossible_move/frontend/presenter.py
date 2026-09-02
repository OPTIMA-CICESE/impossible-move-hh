from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from impossible_move.replay import ReplayAction, ReplayCatalog, ReplaySnapshot
from impossible_move.replay.history import decision_history as raw_decision_history
from .adaptive import (
    PresentationScale,
    activity_summary,
    category_groups,
    compact_bins,
    focused_bin_id,
    pending_groups,
    recommended_speed,
    scale_for_catalog,
    speed_options,
)
from .i18n import DEFAULT_LANGUAGE, localized_item_name, normalize_language, tr

_HEURISTIC_LABELS = {
    "first_fit": "First Fit",
    "best_fit": "Best Fit",
    "worst_fit": "Worst Fit",
    "next_fit": "Next Fit",
}

_RULE_IDS = (
    "base",
    "no_existing_fit",
    "exact_fit",
    "single_feasible_bin",
    "large_item",
    "small_item_many_options",
    "medium_item",
    "high_residual_spread",
    "tight_last_bin",
)

_FEATURE_ORDER = (
    "open_bins",
    "remaining_items",
    "current_item_size",
    "item_ratio",
    "utilization",
    "mean_remaining_capacity",
    "max_remaining_capacity",
    "feasible_bins",
    "feasible_ratio",
    "exact_fit_bins",
    "min_remaining_after",
    "max_remaining_after",
    "residual_spread",
    "last_bin_feasible",
    "last_bin_remaining_after",
)

_LEGEND_RULES = (
    "exact_fit",
    "large_item",
    "small_item_many_options",
    "single_feasible_bin",
    "high_residual_spread",
    "tight_last_bin",
    "no_existing_fit",
)


def heuristic_label(heuristic_id: str) -> str:
    return _HEURISTIC_LABELS.get(heuristic_id, heuristic_id.replace("_", " ").title())


def rule_label(rule_id: str, language: str = DEFAULT_LANGUAGE) -> str:
    fallback = rule_id.replace("_", " ").capitalize()
    value = tr(f"rule_{rule_id}", language)
    return fallback if value == f"rule_{rule_id}" else value


def rule_question(rule_id: str, language: str = DEFAULT_LANGUAGE) -> str:
    value = tr(f"question_{rule_id}", language)
    return rule_label(rule_id, language) if value == f"question_{rule_id}" else value


def _item_dict(item_id: str, catalog: ReplayCatalog | None, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    if catalog is None:
        return {
            "id": item_id,
            "displayName": item_id,
            "size": 0,
            "category": "other",
            "assetId": "generic",
        }
    info = catalog.items.get(item_id)
    if info is None:
        return {
            "id": item_id,
            "displayName": item_id,
            "size": 0,
            "category": "other",
            "assetId": "generic",
        }
    return {
        "id": info.id,
        "displayName": localized_item_name(info.asset_id, info.display_name, language),
        "size": info.size,
        "category": info.category,
        "assetId": info.asset_id,
    }


def pending_items(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    return [_item_dict(item_id, catalog, language) for item_id in snapshot.remaining_item_ids]


def current_item(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    item = snapshot.current_item
    if item is None:
        return {}
    return {
        "id": item.id,
        "displayName": localized_item_name(item.asset_id, item.display_name, language),
        "size": item.size,
        "category": item.category,
        "assetId": item.asset_id,
    }


def bins(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for bin_ in snapshot.bins:
        result.append(
            {
                "id": bin_.id,
                "capacity": bin_.capacity,
                "usedCapacity": bin_.used_capacity,
                "remainingCapacity": bin_.remaining_capacity,
                "utilization": bin_.used_capacity / bin_.capacity,
                "isSelected": snapshot.selected_bin_id == bin_.id,
                "items": [_item_dict(item_id, catalog, language) for item_id in bin_.item_ids],
            }
        )
    return result


def bin_detail(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None, bin_id: int | None, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    if bin_id is None:
        return {}
    for row in bins(snapshot, catalog, language):
        if row["id"] == bin_id:
            return row
    return {}


def heuristic_scores(snapshot: ReplaySnapshot) -> list[dict[str, Any]]:
    ids = snapshot.heuristic_ids or tuple(snapshot.heuristic_scores)
    raw = {heuristic_id: float(snapshot.heuristic_scores.get(heuristic_id, 0.0)) for heuristic_id in ids}
    max_score = max(raw.values(), default=0.0)
    return [
        {
            "id": heuristic_id,
            "label": heuristic_label(heuristic_id),
            "score": score,
            "normalized": (score / max_score) if max_score > 0 else 0.0,
            "selected": heuristic_id == snapshot.selected_heuristic_id,
        }
        for heuristic_id, score in raw.items()
    ]


def heuristic_counts(snapshot: ReplaySnapshot) -> list[dict[str, Any]]:
    ids = snapshot.heuristic_ids or tuple(snapshot.heuristic_counts)
    total = sum(int(snapshot.heuristic_counts.get(heuristic_id, 0)) for heuristic_id in ids)
    return [
        {
            "id": heuristic_id,
            "label": heuristic_label(heuristic_id),
            "count": int(snapshot.heuristic_counts.get(heuristic_id, 0)),
            "fraction": (int(snapshot.heuristic_counts.get(heuristic_id, 0)) / total) if total else 0.0,
        }
        for heuristic_id in ids
    ]


def decision_reasons(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    return [
        {
            "ruleId": reason.rule_id,
            "ruleLabel": rule_label(reason.rule_id, language),
            "question": rule_question(reason.rule_id, language),
            "answer": tr("yes", language) if reason.rule_id != "base" else "",
            "heuristicId": reason.heuristic_id,
            "heuristicLabel": heuristic_label(reason.heuristic_id),
            "contribution": reason.contribution,
        }
        for reason in snapshot.decision_reasons
    ]


def rule_legend(language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    return [
        {
            "ruleId": rule_id,
            "question": rule_question(rule_id, language),
            "meaning": tr(f"legend_{rule_id}", language),
        }
        for rule_id in _LEGEND_RULES
    ]


def feature_rows(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in _FEATURE_ORDER:
        if key not in snapshot.features:
            continue
        seen.add(key)
        label = tr(f"feature_{key}", language)
        rows.append({"id": key, "label": label, "value": float(snapshot.features[key])})
    for key, value in snapshot.features.items():
        if key in seen:
            continue
        rows.append({"id": key, "label": key.replace("_", " ").capitalize(), "value": float(value)})
    return rows


def placement_evaluations(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    return [
        {
            "binId": evaluation.bin_id,
            "binLabel": f"{tr('truck', language)} {evaluation.bin_id + 1}",
            "feasible": evaluation.feasible,
            "remainingBefore": evaluation.remaining_before,
            "remainingAfter": evaluation.remaining_after if evaluation.remaining_after is not None else -1,
            "score": evaluation.score if evaluation.score is not None else 0.0,
            "hasScore": evaluation.score is not None,
            "selected": snapshot.selected_bin_id == evaluation.bin_id,
        }
        for evaluation in snapshot.placement_evaluations
    ]


def summary(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None = None) -> dict[str, Any]:
    value = snapshot.summary
    if value is None:
        used = sum(bin_.used_capacity for bin_ in snapshot.bins)
        total_capacity = sum(bin_.capacity for bin_ in snapshot.bins)
        bin_capacity = catalog.bin_capacity if catalog is not None else None
        total_item_size = sum(item.size for item in catalog.items.values()) if catalog is not None else 0
        lower_bound = (
            (total_item_size + bin_capacity - 1) // bin_capacity
            if bin_capacity is not None and bin_capacity > 0
            else 0
        )
        return {
            "binsUsed": len(snapshot.bins),
            "usedCapacity": used,
            "totalCapacity": total_capacity,
            "totalItemSize": total_item_size,
            "unusedCapacity": total_capacity - used,
            "utilization": (used / total_capacity) if total_capacity else 0.0,
            "lowerBound": lower_bound,
            "placementEvaluations": 0,
            "finished": False,
        }
    total_item_size = sum(item.size for item in catalog.items.values()) if catalog is not None else value.used_capacity
    return {
        "binsUsed": value.bins_used,
        "usedCapacity": value.used_capacity,
        "totalCapacity": value.total_capacity,
        "totalItemSize": total_item_size,
        "unusedCapacity": value.unused_capacity,
        "utilization": value.utilization,
        "lowerBound": value.lower_bound,
        "placementEvaluations": value.placement_evaluations,
        "finished": True,
    }


def _top_public_reasons(snapshot: ReplaySnapshot, language: str, limit: int = 2) -> list[str]:
    relevant = [reason for reason in snapshot.decision_reasons if reason.rule_id != "base"]
    relevant.sort(key=lambda reason: abs(reason.contribution), reverse=True)
    phrases: list[str] = []
    for reason in relevant:
        phrase = tr(f"reason_{reason.rule_id}", language)
        if phrase.startswith("reason_"):
            continue
        if phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) >= limit:
            break
    return phrases


def decision_narrative(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> str:
    language = normalize_language(language)
    if not snapshot.selected_heuristic_id:
        if snapshot.summary is not None or snapshot.status.value == "finished":
            return tr("narrative_finished", language)
        if snapshot.current_item is not None:
            return tr("narrative_observing", language)
        if snapshot.status.value == "paused":
            return tr("narrative_paused", language)
        return tr("narrative_ready", language)

    label = heuristic_label(snapshot.selected_heuristic_id)
    phrases = _top_public_reasons(snapshot, language)
    if not phrases:
        return tr("narrative_base", language, heuristic=label)
    connector = tr("and_word", language)
    reason_text = phrases[0] if len(phrases) == 1 else connector.join(phrases[:2])
    return tr("narrative_reason", language, heuristic=label, reason=reason_text)


def status_message(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> str:
    if snapshot.summary is not None or snapshot.status.value == "finished":
        return tr("status_finished", language)
    if snapshot.status.value == "playing":
        return tr("status_playing", language)
    if snapshot.status.value == "paused":
        return tr("status_paused", language)
    if snapshot.current_item is not None:
        return tr("status_preparing", language)
    return tr("status_ready", language)


def mode_info(snapshot: ReplaySnapshot, language: str = DEFAULT_LANGUAGE) -> dict[str, str]:
    if snapshot.mode.value == "presentation":
        return {
            "label": tr("mode_presentation_label", language),
            "description": tr("mode_presentation_description", language),
        }
    return {
        "label": tr("mode_detailed_label", language),
        "description": tr("mode_detailed_description", language),
    }


def snapshot_to_view_model(
    snapshot: ReplaySnapshot,
    catalog: ReplayCatalog | None,
    *,
    last_action: str = "",
    language: str = DEFAULT_LANGUAGE,
    interesting_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    language = normalize_language(language)
    reasons = decision_reasons(snapshot, language)
    scale = scale_for_catalog(catalog)
    activity = activity_summary(snapshot, catalog)
    focus_id = focused_bin_id(snapshot)
    all_bins = bins(snapshot, catalog, language) if scale is PresentationScale.SMALL else []
    options = speed_options(scale)
    scale_key = {"small": "scale_small", "medium": "scale_medium", "large": "scale_large"}[scale.value]
    trace_key = {"full": "trace_full", "standard": "trace_standard", "compact": "trace_compact"}.get(snapshot.trace_policy)
    return {
        "language": language,
        "status": snapshot.status.value,
        "statusMessage": status_message(snapshot, language),
        "mode": snapshot.mode.value,
        "modeInfo": mode_info(snapshot, language),
        "speed": snapshot.speed,
        "progress": snapshot.progress,
        "cursor": snapshot.cursor,
        "totalEvents": snapshot.total_events,
        "currentStep": snapshot.current_step if snapshot.current_step is not None else -1,
        "decisionCount": sum(int(value) for value in snapshot.heuristic_counts.values()),
        "decisionTotal": len(snapshot.item_order),
        "decisionProgress": (sum(int(value) for value in snapshot.heuristic_counts.values()) / len(snapshot.item_order)) if snapshot.item_order else 0.0,
        "lastAction": last_action,
        "pendingItems": pending_items(snapshot, catalog, language) if scale is PresentationScale.SMALL else [],
        "pendingGroups": pending_groups(snapshot, catalog, language=language),
        "categoryGroups": category_groups(snapshot, catalog, language=language),
        "activity": activity,
        "currentItem": current_item(snapshot, language),
        "bins": all_bins,
        "compactBins": compact_bins(snapshot, language=language),
        "focusedBin": bin_detail(snapshot, catalog, focus_id, language),
        "selectedHeuristicId": snapshot.selected_heuristic_id or "",
        "selectedHeuristicLabel": heuristic_label(snapshot.selected_heuristic_id) if snapshot.selected_heuristic_id else "",
        "heuristicScores": heuristic_scores(snapshot),
        "heuristicCounts": heuristic_counts(snapshot),
        "decisionReasons": reasons,
        "decisionGraphReasons": [reason for reason in reasons if reason["ruleId"] != "base"],
        "decisionNarrative": decision_narrative(snapshot, language),
        "ruleLegend": rule_legend(language),
        "features": dict(snapshot.features),
        "featureRows": feature_rows(snapshot, language),
        "placementEvaluations": placement_evaluations(snapshot, language),
        "binCapacity": catalog.bin_capacity if catalog is not None and catalog.bin_capacity is not None else 0,
        "presentationScale": scale.value,
        "presentationScaleLabel": tr(scale_key, language),
        "speedOptions": [{"value": value, "label": (str(int(value)) if float(value).is_integer() else str(value)) + "×"} for value in options],
        "recommendedSpeed": recommended_speed(scale),
        "tracePolicy": snapshot.trace_policy,
        "tracePolicyLabel": tr(trace_key, language) if trace_key else snapshot.trace_policy,
        "placementDetailsAvailable": snapshot.trace_policy == "full",
        "featureDetailsAvailable": snapshot.trace_policy != "compact",
        "summary": summary(snapshot, catalog),
        "interestingInfo": dict(interesting_info or {}),
    }



def trace_decision_history(trace, catalog: ReplayCatalog | None, language: str = DEFAULT_LANGUAGE, limit: int | None = None) -> list[dict[str, Any]]:
    rows = raw_decision_history(trace, catalog)
    localized: list[dict[str, Any]] = []
    for row in rows:
        item_id = row["item_id"]
        info = catalog.items.get(item_id) if catalog is not None else None
        reasons = []
        for reason in row.get("reasons", []):
            reasons.append({
                **reason,
                "question": rule_question(reason["rule_id"], language),
                "heuristicLabel": heuristic_label(reason["heuristic_id"]),
            })
        localized.append({
            **row,
            "displayName": localized_item_name(info.asset_id, info.display_name, language) if info else row.get("display_name", item_id),
            "heuristicLabel": heuristic_label(row["heuristic_id"]),
            "reasons": reasons,
            "scoreRows": [
                {"id": heuristic_id, "label": heuristic_label(heuristic_id), "score": float(score)}
                for heuristic_id, score in row.get("scores", {}).items()
            ],
            "truckLabel": f"{tr('truck', language)} {row['bin_id'] + 1}" if row.get("bin_id", -1) >= 0 else "—",
        })
    return localized if limit is None else localized[:max(0, limit)]


def grouped_decision_histories(trace, catalog: ReplayCatalog | None, language: str = DEFAULT_LANGUAGE, limit: int | None = None) -> list[dict[str, Any]]:
    rows = trace_decision_history(trace, catalog, language, limit)
    ids = ("first_fit", "best_fit", "worst_fit", "next_fit")
    total = len(rows)
    return [
        {
            "id": heuristic_id,
            "label": heuristic_label(heuristic_id),
            "count": sum(1 for row in rows if row["heuristic_id"] == heuristic_id),
            "fraction": (sum(1 for row in rows if row["heuristic_id"] == heuristic_id) / total) if total else 0.0,
            "decisions": [row for row in rows if row["heuristic_id"] == heuristic_id],
        }
        for heuristic_id in ids
    ]

def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_plain(item) for item in value]
    return value


def action_to_transition(
    action: ReplayAction,
    snapshot: ReplaySnapshot,
    catalog: ReplayCatalog | None,
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    payload = _plain(action.payload)
    transition: dict[str, Any] = {
        "type": action.type.value,
        "sequence": action.sequence,
        "step": action.step,
        "payload": payload,
    }

    item_id = payload.get("item_id")
    if item_id:
        transition["item"] = _item_dict(str(item_id), catalog, language)

    bin_id = payload.get("bin_id")
    if bin_id is not None:
        transition["binId"] = int(bin_id)
        ordered_ids = [bin_.id for bin_ in snapshot.bins]
        transition["binIndex"] = ordered_ids.index(int(bin_id)) if int(bin_id) in ordered_ids else -1

    heuristic_id = payload.get("heuristic_id")
    if heuristic_id:
        transition["heuristicId"] = str(heuristic_id)
        transition["heuristicLabel"] = heuristic_label(str(heuristic_id))

    return transition
