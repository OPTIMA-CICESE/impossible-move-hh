from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from impossible_move.domain.models import (
    BinPackingInstance,
    InstanceMetadata,
    Item,
    ItemCategory,
)

INSTANCE_SCHEMA_VERSION = "1.0"


def instance_to_dict(instance: BinPackingInstance) -> dict[str, Any]:
    return {
        "schema_version": INSTANCE_SCHEMA_VERSION,
        "id": instance.id,
        "name": instance.name,
        "capacity": instance.capacity,
        "metadata": {
            "difficulty": instance.metadata.difficulty,
            "description": instance.metadata.description,
            "optimal_value": instance.metadata.optimal_value,
        },
        "items": [
            {
                "id": item.id,
                "size": item.size,
                "display_name": item.display_name,
                "category": item.category.value,
                "asset_id": item.asset_id,
            }
            for item in instance.items
        ],
    }


def instance_from_dict(data: dict[str, Any]) -> BinPackingInstance:
    if data.get("schema_version") != INSTANCE_SCHEMA_VERSION:
        raise ValueError(f"unsupported instance schema version {data.get('schema_version')!r}")
    metadata = InstanceMetadata(**data.get("metadata", {}))
    items = tuple(
        Item(
            id=raw["id"],
            size=int(raw["size"]),
            display_name=raw["display_name"],
            category=ItemCategory(raw.get("category", ItemCategory.OTHER.value)),
            asset_id=raw.get("asset_id", "generic"),
        )
        for raw in data["items"]
    )
    return BinPackingInstance(
        id=data["id"],
        name=data["name"],
        capacity=int(data["capacity"]),
        items=items,
        metadata=metadata,
    )


def write_instance(instance: BinPackingInstance, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(instance_to_dict(instance), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_instance(path: str | Path) -> BinPackingInstance:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("instance JSON root must be an object")
    return instance_from_dict(raw)
