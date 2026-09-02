from __future__ import annotations

from dataclasses import dataclass

from impossible_move.domain.models import BinPackingInstance

SUPPORTED_ITEM_COUNTS = (10, 15, 20, 50, 100, 200, 500)
INSTANCE_LABELS = ("A", "B", "C", "D", "E")
SUPPORTED_PROFILES = ("natural", "contrastive", "challenge", "regime")
DEFAULT_PROFILE = "natural"
DEFAULT_BATCH_SEED = 20260831


@dataclass(frozen=True, slots=True)
class ExperimentConfiguration:
    """Reproducible configuration for one generated outreach experiment."""

    item_count: int = 10
    truck_capacity: int = 10
    instance_index: int = 0
    batch_seed: int = DEFAULT_BATCH_SEED
    profile: str = DEFAULT_PROFILE

    def __post_init__(self) -> None:
        if self.item_count not in SUPPORTED_ITEM_COUNTS:
            raise ValueError(
                f"item_count must be one of {SUPPORTED_ITEM_COUNTS!r}; got {self.item_count}"
            )
        if self.truck_capacity <= 0:
            raise ValueError("truck_capacity must be positive")
        if not 0 <= self.instance_index < len(INSTANCE_LABELS):
            raise ValueError("instance_index must identify one of the five candidates A-E")
        if self.batch_seed < 0:
            raise ValueError("batch_seed must be non-negative")
        if self.profile not in SUPPORTED_PROFILES:
            raise ValueError(f"profile must be one of {SUPPORTED_PROFILES!r}; got {self.profile!r}")

    @property
    def instance_label(self) -> str:
        return INSTANCE_LABELS[self.instance_index]

    def _replace(self, **changes) -> "ExperimentConfiguration":
        data = {
            "item_count": self.item_count,
            "truck_capacity": self.truck_capacity,
            "instance_index": self.instance_index,
            "batch_seed": self.batch_seed,
            "profile": self.profile,
        }
        data.update(changes)
        return ExperimentConfiguration(**data)

    def with_item_count(self, item_count: int) -> "ExperimentConfiguration":
        return self._replace(item_count=item_count)

    def with_capacity(self, truck_capacity: int) -> "ExperimentConfiguration":
        return self._replace(truck_capacity=truck_capacity)

    def with_instance_index(self, instance_index: int) -> "ExperimentConfiguration":
        return self._replace(instance_index=instance_index)

    def with_batch_seed(self, batch_seed: int) -> "ExperimentConfiguration":
        return self._replace(batch_seed=batch_seed, instance_index=0)

    def with_profile(self, profile: str) -> "ExperimentConfiguration":
        return self._replace(profile=profile, instance_index=0)


@dataclass(frozen=True, slots=True)
class GeneratedCandidate:
    index: int
    label: str
    seed: int
    instance: BinPackingInstance

    def __post_init__(self) -> None:
        if self.index < 0 or self.index >= len(INSTANCE_LABELS):
            raise ValueError("candidate index is outside A-E")
        if self.label != INSTANCE_LABELS[self.index]:
            raise ValueError("candidate label does not match its index")
        if self.seed < 0:
            raise ValueError("candidate seed must be non-negative")


@dataclass(frozen=True, slots=True)
class GeneratedInstanceSet:
    item_count: int
    truck_capacity: int
    batch_seed: int
    profile: str
    candidates: tuple[GeneratedCandidate, ...]

    def __post_init__(self) -> None:
        if self.profile not in SUPPORTED_PROFILES:
            raise ValueError("unsupported corpus profile")
        if len(self.candidates) != len(INSTANCE_LABELS):
            raise ValueError("an instance set must contain exactly five candidates")
        if tuple(candidate.label for candidate in self.candidates) != INSTANCE_LABELS:
            raise ValueError("instance set candidates must be ordered A-E")
        if any(len(candidate.instance.items) != self.item_count for candidate in self.candidates):
            raise ValueError("candidate item counts must match the set")
        if any(candidate.instance.capacity != self.truck_capacity for candidate in self.candidates):
            raise ValueError("candidate capacities must match the set")

    def selected(self, index: int) -> GeneratedCandidate:
        return self.candidates[index]
