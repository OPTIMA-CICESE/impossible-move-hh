from __future__ import annotations

from collections import Counter
from enum import Enum
from typing import Any

from impossible_move.replay import ReplayCatalog, ReplaySnapshot
from .i18n import DEFAULT_LANGUAGE, localized_item_name, tr


class PresentationScale(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

    @classmethod
    def for_item_count(cls, item_count: int) -> "PresentationScale":
        if item_count <= 20:
            return cls.SMALL
        if item_count <= 100:
            return cls.MEDIUM
        return cls.LARGE


def scale_for_catalog(catalog: ReplayCatalog | None) -> PresentationScale:
    return PresentationScale.for_item_count(len(catalog.items) if catalog is not None else 0)


def speed_options(scale: PresentationScale) -> tuple[float, ...]:
    if scale is PresentationScale.SMALL:
        return (0.5, 1.0, 2.0, 5.0, 20.0)
    if scale is PresentationScale.MEDIUM:
        return (1.0, 5.0, 20.0, 50.0)
    return (20.0, 50.0, 100.0, 200.0)


def recommended_speed(scale: PresentationScale) -> float:
    return {PresentationScale.SMALL: 1.0, PresentationScale.MEDIUM: 5.0, PresentationScale.LARGE: 20.0}[scale]


def _item(catalog: ReplayCatalog, item_id: str):
    return catalog.items[item_id]


def pending_groups(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None, *, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    if catalog is None:
        return []
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    labels: dict[str, str] = {}
    assets: dict[str, str] = {}
    categories: dict[str, str] = {}
    for item_id in snapshot.remaining_item_ids:
        info = _item(catalog, item_id)
        key = info.asset_id or info.category
        counts[key] += 1
        sizes[key] += info.size
        labels[key] = localized_item_name(info.asset_id, info.display_name, language).rsplit(" ", 1)[0] if info.display_name[-1:].isdigit() else localized_item_name(info.asset_id, info.display_name, language)
        assets[key] = info.asset_id
        categories[key] = info.category
    total = sum(counts.values())
    rows = [
        {
            "id": key,
            "label": labels[key],
            "assetId": assets[key],
            "category": categories[key],
            "count": count,
            "totalSize": sizes[key],
            "fraction": count / total if total else 0.0,
        }
        for key, count in counts.items()
    ]
    return sorted(rows, key=lambda row: (-row["count"], row["label"]))


def category_groups(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None, *, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    if catalog is None:
        return []
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for item_id in snapshot.remaining_item_ids:
        info = _item(catalog, item_id)
        counts[info.category] += 1
        sizes[info.category] += info.size
    total = sum(counts.values())
    return [
        {
            "id": key,
            "label": tr(f"category_{key}", language),
            "count": counts[key],
            "totalSize": sizes[key],
            "fraction": counts[key] / total if total else 0.0,
        }
        for key in sorted(counts, key=lambda key: (-counts[key], tr(f"category_{key}", language)))
    ]


def compact_bins(snapshot: ReplaySnapshot, *, language: str = DEFAULT_LANGUAGE) -> list[dict[str, Any]]:
    return [
        {
            "id": bin_.id,
            "label": f"{tr('truck', language)} {bin_.id + 1}",
            "capacity": bin_.capacity,
            "usedCapacity": bin_.used_capacity,
            "remainingCapacity": bin_.remaining_capacity,
            "utilization": bin_.used_capacity / bin_.capacity,
            "itemCount": len(bin_.item_ids),
            "selected": snapshot.selected_bin_id == bin_.id,
        }
        for bin_ in snapshot.bins
    ]


def focused_bin_id(snapshot: ReplaySnapshot) -> int | None:
    if snapshot.selected_bin_id is not None:
        return snapshot.selected_bin_id
    if snapshot.bins:
        return snapshot.bins[-1].id
    return None


def activity_summary(snapshot: ReplaySnapshot, catalog: ReplayCatalog | None) -> dict[str, Any]:
    total = len(catalog.items) if catalog is not None else len(snapshot.item_order)
    pending = len(snapshot.remaining_item_ids) + (1 if snapshot.current_item is not None else 0)
    processed = max(0, total - pending)
    focus = focused_bin_id(snapshot)
    return {
        "totalItems": total,
        "processedItems": processed,
        "pendingItems": pending,
        "processedFraction": processed / total if total else 0.0,
        "openBins": len(snapshot.bins),
        "focusedBinId": focus if focus is not None else -1,
    }
