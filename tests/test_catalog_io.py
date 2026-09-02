import json

import pytest

from impossible_move.replay import (
    ReplayCatalog,
    ReplayItemInfo,
    catalog_from_dict,
    catalog_from_json,
    catalog_to_dict,
    catalog_to_json,
)


def sample_catalog() -> ReplayCatalog:
    return ReplayCatalog(
        instance_id="move-1",
        bin_capacity=10,
        items={
            "sofa": ReplayItemInfo(
                id="sofa",
                display_name="Sofá",
                size=8,
                category="furniture",
                asset_id="sofa",
            ),
            "box": ReplayItemInfo(
                id="box",
                display_name="Caja",
                size=2,
                category="box",
                asset_id="clothes_box",
            ),
        },
    )


def test_catalog_json_round_trip():
    catalog = sample_catalog()
    restored = catalog_from_json(catalog_to_json(catalog))
    assert restored == catalog
    assert restored.items["sofa"].display_name == "Sofá"


def test_catalog_dict_has_schema_and_stable_items():
    data = catalog_to_dict(sample_catalog())
    assert data["schema_version"] == "1.1"
    assert data["instance_id"] == "move-1"
    assert [item["id"] for item in data["items"]] == ["sofa", "box"]


def test_catalog_rejects_duplicate_ids():
    data = catalog_to_dict(sample_catalog())
    data["items"].append(dict(data["items"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        catalog_from_dict(data)


def test_catalog_rejects_unknown_schema():
    data = catalog_to_dict(sample_catalog())
    data["schema_version"] = "9.9"
    with pytest.raises(ValueError, match="unsupported"):
        catalog_from_dict(data)

def test_catalog_reads_schema_1_0_without_capacity():
    data = catalog_to_dict(sample_catalog())
    data["schema_version"] = "1.0"
    data.pop("bin_capacity", None)
    restored = catalog_from_dict(data)
    assert restored.bin_capacity is None
    assert restored.items["sofa"].size == 8
