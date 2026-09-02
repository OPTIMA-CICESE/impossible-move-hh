from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from random import Random

from impossible_move.domain.models import (
    BinPackingInstance,
    InstanceMetadata,
    Item,
    ItemCategory,
)

from .models import (
    DEFAULT_PROFILE,
    GeneratedCandidate,
    GeneratedInstanceSet,
    INSTANCE_LABELS,
    SUPPORTED_PROFILES,
)


@dataclass(frozen=True, slots=True)
class MovingObjectTemplate:
    key: str
    display_name: str
    category: ItemCategory
    asset_id: str
    min_ratio: float
    max_ratio: float
    weight: int

    def __post_init__(self) -> None:
        if not 0 < self.min_ratio <= self.max_ratio <= 1:
            raise ValueError("object size ratios must lie in (0, 1]")
        if self.weight <= 0:
            raise ValueError("template weight must be positive")


DEFAULT_TEMPLATES: tuple[MovingObjectTemplate, ...] = (
    MovingObjectTemplate("sofa", "Sofá", ItemCategory.FURNITURE, "sofa", 0.60, 0.85, 7),
    MovingObjectTemplate("fridge", "Refrigerador", ItemCategory.APPLIANCE, "fridge", 0.50, 0.75, 6),
    MovingObjectTemplate("bed", "Cama", ItemCategory.FURNITURE, "bed", 0.45, 0.70, 7),
    MovingObjectTemplate("desk", "Escritorio", ItemCategory.FURNITURE, "desk", 0.30, 0.55, 7),
    MovingObjectTemplate("tv", "Televisión", ItemCategory.ELECTRONICS, "tv", 0.20, 0.40, 8),
    MovingObjectTemplate("chair", "Silla", ItemCategory.FURNITURE, "chair", 0.15, 0.30, 11),
    MovingObjectTemplate("books_box", "Caja de libros", ItemCategory.BOX, "books_box", 0.15, 0.35, 15),
    MovingObjectTemplate("clothes_box", "Caja de ropa", ItemCategory.BOX, "clothes_box", 0.10, 0.25, 16),
    MovingObjectTemplate("lamp", "Lámpara", ItemCategory.DECORATION, "lamp", 0.10, 0.20, 9),
    MovingObjectTemplate("plant", "Planta", ItemCategory.DECORATION, "plant", 0.05, 0.20, 14),
)

# Reproducible online motifs (expressed for capacity 10 and scaled to any capacity).
# They were selected because different valid low-level placement policies can diverge
# on them.  Importantly, the library contains motifs that favour different methods;
# it is not an encoded "adaptive wins" benchmark.
_CONTRASTIVE_MOTIFS: tuple[tuple[int, ...], ...] = (
    (3, 8, 2, 4, 6, 4, 5, 8, 6, 7, 6, 2, 4, 3, 6, 3, 3, 2, 4, 3),
    (3, 8, 3, 8, 6, 5, 2, 2, 4, 6, 5, 2, 4, 6, 4, 7, 2, 6, 4, 8),
    (4, 2, 4, 6, 2, 5, 6, 7, 4, 8, 3, 3, 2, 7, 4, 2, 7, 3, 4, 8),
    (5, 2, 2, 5, 6, 6, 4, 5, 5, 8, 6, 7, 7, 3, 5, 2, 4, 3, 4, 6),
    (8, 5, 2, 8, 2, 6, 8, 2, 2, 3, 3, 2, 4, 2, 8, 8, 5, 4, 8, 3),
    (4, 5, 7, 4, 2, 8, 2, 5, 7, 3, 2, 7, 2, 3, 4, 3, 2, 7, 6, 3),
    (4, 2, 7, 3, 6, 8, 7, 3, 5, 3, 6, 7, 4, 3, 5, 6, 6, 2, 6, 2),
    (7, 4, 2, 2, 8, 2, 7, 8, 4, 2, 8, 7, 4, 4, 6, 7, 4, 2, 8, 7),
)

# Regime-switching recipes concatenate different contrastive motifs as explicit
# temporal phases. The library intentionally includes recipes where the adaptive
# HH wins, ties, or loses against the best fixed heuristic; the profile exposes
# adaptation opportunities without encoding a guaranteed winner.
_REGIME_RECIPES: tuple[tuple[int, ...], ...] = (
    (0, 0, 0, 0, 0),
    (6, 2, 6, 2, 0),
    (2, 4, 7, 1, 3),
    (1, 3, 0, 5, 2),
    (4, 7, 4, 7, 2),
    (5, 0, 5, 0, 6),
    (0, 1, 6, 2, 3),
    (7, 4, 2, 5, 1),
)


class MovingInstanceGenerator:
    """Generate reproducible moving-themed 1D bin-packing instances.

    ``natural`` preserves the original outreach distribution. ``contrastive``
    repeats/rotates valid online size motifs so placement choices have persistent
    consequences. ``challenge`` removes most tiny filler items by drawing from
    roughly 20%-80% of truck capacity. ``regime`` concatenates distinct temporal
    phases so the most suitable low-level heuristic can change during one run.
    """

    def __init__(self, templates: tuple[MovingObjectTemplate, ...] = DEFAULT_TEMPLATES) -> None:
        if not templates:
            raise ValueError("at least one object template is required")
        self.templates = templates
        self._population = tuple(templates)
        self._weights = tuple(template.weight for template in templates)

    @staticmethod
    def derive_seed(
        item_count: int,
        capacity: int,
        batch_seed: int,
        index: int,
        profile: str = DEFAULT_PROFILE,
    ) -> int:
        if profile not in SUPPORTED_PROFILES:
            raise ValueError(f"unsupported corpus profile: {profile!r}")
        payload = f"impossible-move|{profile}|{item_count}|{capacity}|{batch_seed}|{index}".encode("utf-8")
        return int.from_bytes(sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)

    def _template_for_ratio(self, ratio: float, rng: Random) -> MovingObjectTemplate:
        # Prefer semantically plausible templates whose advertised size range contains
        # the target ratio.  If none does, choose the nearest midpoint.
        containing = [t for t in self.templates if t.min_ratio <= ratio <= t.max_ratio]
        if containing:
            return rng.choice(containing)
        return min(self.templates, key=lambda t: abs(((t.min_ratio + t.max_ratio) / 2) - ratio))

    @staticmethod
    def _scaled_size(tenths: int, capacity: int) -> int:
        return max(1, min(capacity, round((tenths / 10.0) * capacity)))

    def _sizes_for_profile(self, *, profile: str, item_count: int, capacity: int, rng: Random) -> list[int] | None:
        if profile == "natural":
            return None
        if profile == "contrastive":
            motif = list(_CONTRASTIVE_MOTIFS[rng.randrange(len(_CONTRASTIVE_MOTIFS))])
            # A deterministic rotation makes A-E and regenerated batches distinct while
            # preserving the online character of the motif.
            shift = rng.randrange(len(motif))
            motif = motif[shift:] + motif[:shift]
            return [self._scaled_size(motif[i % len(motif)], capacity) for i in range(item_count)]
        if profile == "challenge":
            lo = max(1, int(round(0.20 * capacity)))
            hi = max(lo, int(round(0.80 * capacity)))
            # Discrete sizes keep the instance readable and guarantee no sub-20%
            # filler items (modulo integer rounding for very small capacities).
            palette = list(range(lo, hi + 1))
            return [rng.choice(palette) for _ in range(item_count)]
        if profile == "regime":
            # Each motif is one temporal regime. We deliberately keep regime
            # boundaries intact instead of globally shuffling sizes: the order
            # change is the phenomenon this profile is designed to expose.
            recipe = _REGIME_RECIPES[rng.randrange(len(_REGIME_RECIPES))]
            result: list[int] = []
            phase = 0
            while len(result) < item_count:
                motif = _CONTRASTIVE_MOTIFS[recipe[phase % len(recipe)]]
                result.extend(self._scaled_size(value, capacity) for value in motif)
                phase += 1
            return result[:item_count]
        raise ValueError(f"unsupported corpus profile: {profile!r}")

    def generate_instance(
        self,
        *,
        item_count: int,
        capacity: int,
        seed: int,
        label: str,
        profile: str = DEFAULT_PROFILE,
    ) -> BinPackingInstance:
        if item_count <= 0:
            raise ValueError("item_count must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if profile not in SUPPORTED_PROFILES:
            raise ValueError(f"unsupported corpus profile: {profile!r}")

        rng = Random(seed)
        counters: dict[str, int] = {}
        items: list[Item] = []
        prescribed_sizes = self._sizes_for_profile(
            profile=profile, item_count=item_count, capacity=capacity, rng=rng
        )

        for ordinal in range(item_count):
            if prescribed_sizes is None:
                template = rng.choices(self._population, weights=self._weights, k=1)[0]
                ratio = rng.uniform(template.min_ratio, template.max_ratio)
                size = max(1, min(capacity, round(ratio * capacity)))
            else:
                size = prescribed_sizes[ordinal]
                ratio = size / capacity
                template = self._template_for_ratio(ratio, rng)

            counters[template.key] = counters.get(template.key, 0) + 1
            local_number = counters[template.key]
            items.append(
                Item(
                    id=f"{template.key}_{ordinal + 1:04d}",
                    size=size,
                    display_name=(
                        template.display_name
                        if local_number == 1
                        else f"{template.display_name} {local_number}"
                    ),
                    category=template.category,
                    asset_id=template.asset_id,
                )
            )

        instance_id = f"generated_{profile}_n{item_count}_c{capacity}_{label.lower()}_{seed:016x}"
        return BinPackingInstance(
            id=instance_id,
            name=f"La mudanza imposible · {item_count} objetos · ejemplar {label}",
            capacity=capacity,
            items=tuple(items),
            metadata=InstanceMetadata(
                difficulty=profile,
                description=(
                    f"Ejemplar reproducible de divulgación ({profile}) con {item_count} objetos, "
                    f"capacidad {capacity}, semilla {seed}."
                ),
            ),
        )

    def generate_set(
        self,
        *,
        item_count: int,
        capacity: int,
        batch_seed: int,
        profile: str = DEFAULT_PROFILE,
    ) -> GeneratedInstanceSet:
        candidates: list[GeneratedCandidate] = []
        for index, label in enumerate(INSTANCE_LABELS):
            seed = self.derive_seed(item_count, capacity, batch_seed, index, profile)
            candidates.append(
                GeneratedCandidate(
                    index=index,
                    label=label,
                    seed=seed,
                    instance=self.generate_instance(
                        item_count=item_count,
                        capacity=capacity,
                        seed=seed,
                        label=label,
                        profile=profile,
                    ),
                )
            )
        return GeneratedInstanceSet(
            item_count=item_count,
            truck_capacity=capacity,
            batch_seed=batch_seed,
            profile=profile,
            candidates=tuple(candidates),
        )
