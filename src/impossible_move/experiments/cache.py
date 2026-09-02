from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from impossible_move.domain.models import BinPackingInstance
from impossible_move.replay import ReplayCatalog, read_catalog, write_catalog
from impossible_move.trace.serialization import read_trace, write_trace
from impossible_move.trace.trace import RunTrace

from .instance_io import read_instance, write_instance
from .models import ExperimentConfiguration
from .statistics import SearchSpaceEstimate

CACHE_SCHEMA_VERSION = "1.2"
ALGORITHM_PROFILE_VERSION = "explainable-rule-based-v1-original-order-v2-adaptive-trace-corpus-v3"

logger = logging.getLogger(__name__)


def default_cache_root() -> Path:
    override = os.environ.get("IMPOSSIBLE_MOVE_CACHE")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "ImpossibleMove" / "cache"
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "impossible_move"


def _canonical_key_payload(config: ExperimentConfiguration, instance_seed: int) -> dict[str, Any]:
    return {
        "algorithm_profile": ALGORITHM_PROFILE_VERSION,
        "item_count": config.item_count,
        "truck_capacity": config.truck_capacity,
        "instance_index": config.instance_index,
        "batch_seed": config.batch_seed,
        "instance_seed": instance_seed,
        "profile": config.profile,
    }


def cache_key(config: ExperimentConfiguration, instance_seed: int) -> str:
    raw = json.dumps(_canonical_key_payload(config, instance_seed), sort_keys=True, separators=(",", ":"))
    digest = sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"{config.profile}_n{config.item_count}_c{config.truck_capacity}_{config.instance_label}_{digest}"


@dataclass(frozen=True, slots=True)
class CachedExperiment:
    trace: RunTrace
    catalog: ReplayCatalog
    instance: BinPackingInstance
    statistics: SearchSpaceEstimate
    cache_key: str


class ExperimentCache:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else default_cache_root()

    def directory_for(self, config: ExperimentConfiguration, instance_seed: int) -> Path:
        return self.root / cache_key(config, instance_seed)

    def load(self, config: ExperimentConfiguration, instance_seed: int) -> CachedExperiment | None:
        directory = self.directory_for(config, instance_seed)
        manifest_path = directory / "manifest.json"
        if not manifest_path.exists():
            logger.debug("Cache miss | directory=%s", directory)
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema_version") != CACHE_SCHEMA_VERSION:
                return None
            if manifest.get("algorithm_profile") != ALGORITHM_PROFILE_VERSION:
                return None
            if manifest.get("key_payload") != _canonical_key_payload(config, instance_seed):
                return None
            instance = read_instance(directory / "instance.json")
            trace = read_trace(directory / "trace.json")
            catalog = read_catalog(directory / "catalog.json")
            stats_raw = manifest["statistics"]
            statistics = SearchSpaceEstimate(
                item_count=int(stats_raw["item_count"]),
                heuristic_count=int(stats_raw["heuristic_count"]),
                decision_sequences=int(stats_raw["decision_sequences"]),
                theoretical_partitions=int(stats_raw["theoretical_partitions"]),
                decisions_observed=int(stats_raw.get("decisions_observed", 0)),
                heuristic_options_scored=int(stats_raw.get("heuristic_options_scored", 0)),
                heuristic_options_not_selected=int(stats_raw.get("heuristic_options_not_selected", 0)),
                placement_evaluations=int(stats_raw.get("placement_evaluations", 0)),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable cache entry | directory=%s | error=%s", directory, exc)
            return None
        logger.debug("Cache entry loaded | directory=%s", directory)
        return CachedExperiment(
            trace=trace,
            catalog=catalog,
            instance=instance,
            statistics=statistics,
            cache_key=directory.name,
        )

    def store(
        self,
        *,
        config: ExperimentConfiguration,
        instance_seed: int,
        instance,
        trace: RunTrace,
        catalog: ReplayCatalog,
        statistics: SearchSpaceEstimate,
    ) -> str:
        directory = self.directory_for(config, instance_seed)
        directory.mkdir(parents=True, exist_ok=True)
        write_instance(instance, directory / "instance.json")
        write_trace(trace, directory / "trace.json")
        write_catalog(catalog, directory / "catalog.json")
        manifest = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "algorithm_profile": ALGORITHM_PROFILE_VERSION,
            "key_payload": _canonical_key_payload(config, instance_seed),
            "statistics": {
                "item_count": statistics.item_count,
                "heuristic_count": statistics.heuristic_count,
                "decision_sequences": str(statistics.decision_sequences),
                "theoretical_partitions": str(statistics.theoretical_partitions),
                "decisions_observed": statistics.decisions_observed,
                "heuristic_options_scored": statistics.heuristic_options_scored,
                "heuristic_options_not_selected": statistics.heuristic_options_not_selected,
                "placement_evaluations": statistics.placement_evaluations,
            },
        }
        (directory / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.debug("Cache entry stored | directory=%s", directory)
        return directory.name
