from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ReplayCatalog, ReplayItemInfo

CATALOG_SCHEMA_VERSION = "1.1"


def catalog_to_dict(catalog: ReplayCatalog) -> dict[str, Any]:
    return {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "instance_id": catalog.instance_id,
        "bin_capacity": catalog.bin_capacity,
        "items": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "size": item.size,
                "category": item.category,
                "asset_id": item.asset_id,
            }
            for item in catalog.items.values()
        ],
    }


def catalog_to_json(catalog: ReplayCatalog, *, indent: int = 2) -> str:
    return json.dumps(catalog_to_dict(catalog), ensure_ascii=False, indent=indent)


def write_catalog(catalog: ReplayCatalog, path: str | Path) -> None:
    Path(path).write_text(catalog_to_json(catalog) + "\n", encoding="utf-8")


def catalog_from_dict(data: dict[str, Any]) -> ReplayCatalog:
    version = data.get("schema_version")
    if version not in {"1.0", "1.1"}:
        raise ValueError(f"unsupported replay catalog schema version {version!r}")
    try:
        instance_id = data["instance_id"]
        raw_items = data["items"]
    except KeyError as exc:
        raise ValueError(f"catalog is missing required field {exc.args[0]!r}") from exc
    if not isinstance(raw_items, list):
        raise ValueError("catalog items must be a list")
    items: dict[str, ReplayItemInfo] = {}
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("catalog item entries must be objects")
        item = ReplayItemInfo(**raw)
        if item.id in items:
            raise ValueError(f"catalog contains duplicate item id {item.id!r}")
        items[item.id] = item
    return ReplayCatalog(
        instance_id=instance_id,
        items=items,
        bin_capacity=data.get("bin_capacity"),
    )


def catalog_from_json(raw: str) -> ReplayCatalog:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("catalog JSON root must be an object")
    return catalog_from_dict(data)


def read_catalog(path: str | Path) -> ReplayCatalog:
    return catalog_from_json(Path(path).read_text(encoding="utf-8"))
