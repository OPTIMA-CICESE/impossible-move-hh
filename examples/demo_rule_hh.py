from collections import Counter
from pathlib import Path

from impossible_move.domain.models import BinPackingInstance, InstanceMetadata, Item, ItemCategory
from impossible_move.engine import BinPackingEngine
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import ExplainableRuleBasedHH
from impossible_move.ordering import OriginalOrder
from impossible_move.trace.events import HeuristicSelected
from impossible_move.trace.serialization import write_trace
from impossible_move.replay import ReplayCatalog, write_catalog


def moving_item(id_: str, name: str, size: int, category: ItemCategory, asset: str) -> Item:
    return Item(id=id_, display_name=name, size=size, category=category, asset_id=asset)


instance = BinPackingInstance(
    id="mudanza_rule_demo_01",
    name="La mudanza imposible — HH explicable",
    capacity=10,
    items=(
        moving_item("sofa", "Sofá", 8, ItemCategory.FURNITURE, "sofa"),
        moving_item("clothes", "Caja de ropa", 2, ItemCategory.BOX, "clothes_box"),
        moving_item("bed", "Cama", 6, ItemCategory.FURNITURE, "bed"),
        moving_item("tv", "Televisión", 4, ItemCategory.ELECTRONICS, "tv"),
        moving_item("chair", "Silla", 3, ItemCategory.FURNITURE, "chair"),
        moving_item("books", "Caja de libros", 3, ItemCategory.BOX, "books_box"),
        moving_item("fridge", "Refrigerador", 7, ItemCategory.APPLIANCE, "fridge"),
        moving_item("plant", "Planta", 1, ItemCategory.DECORATION, "plant"),
        moving_item("desk", "Escritorio", 5, ItemCategory.FURNITURE, "desk"),
        moving_item("lamp", "Lámpara", 2, ItemCategory.DECORATION, "lamp"),
    ),
    metadata=InstanceMetadata(
        difficulty="tutorial",
        description="Small instance designed to expose rule-based HH decisions.",
    ),
)

result = BinPackingEngine().solve(
    instance,
    ExplainableRuleBasedHH(),
    [FirstFit(), BestFit(), WorstFit(), NextFit()],
    OriginalOrder(),
    run_id="rule-demo-run-001",
)

output = Path(__file__).with_name("demo_rule_trace.json")
write_trace(result.trace, output)
catalog_output = Path(__file__).with_name("demo_rule_catalog.json")
write_catalog(ReplayCatalog.from_instance(instance), catalog_output)

selections = [
    event for event in result.trace.events if isinstance(event, HeuristicSelected)
]
counts = Counter(event.heuristic_id for event in selections)

print(f"schema={result.trace.schema_version}")
print(f"bins_used={result.solution.bins_used}")
print(f"lower_bound={result.solution.lower_bound}")
print(f"utilization={result.solution.utilization:.3f}")
print(f"events={len(result.trace.events)}")
print(f"selections={dict(counts)}")
print(f"trace={output}")
print(f"catalog={catalog_output}")

print("\nDecision audit:")
for event in selections:
    reasons = ", ".join(
        f"{reason.rule_id}:{reason.heuristic_id}+{reason.contribution:g}"
        for reason in event.reasons
    )
    print(
        f"step={event.step:02d} selected={event.heuristic_id:<10} "
        f"scores={dict(event.scores or {})} reasons=[{reasons}]"
    )
