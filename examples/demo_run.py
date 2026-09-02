from pathlib import Path

from impossible_move.domain.models import BinPackingInstance, InstanceMetadata, Item, ItemCategory
from impossible_move.engine import BinPackingEngine
from impossible_move.heuristics import BestFit, FirstFit, NextFit, WorstFit
from impossible_move.hyperheuristics import RandomHyperHeuristic
from impossible_move.ordering import DecreasingSize
from impossible_move.trace.serialization import write_trace


def moving_item(id_: str, name: str, size: int, category: ItemCategory, asset: str) -> Item:
    return Item(id=id_, display_name=name, size=size, category=category, asset_id=asset)


instance = BinPackingInstance(
    id="mudanza_demo_01",
    name="La mudanza imposible — demo 01",
    capacity=10,
    items=(
        moving_item("sofa", "Sofá", 8, ItemCategory.FURNITURE, "sofa"),
        moving_item("fridge", "Refrigerador", 7, ItemCategory.APPLIANCE, "fridge"),
        moving_item("bed", "Cama", 6, ItemCategory.FURNITURE, "bed"),
        moving_item("desk", "Escritorio", 5, ItemCategory.FURNITURE, "desk"),
        moving_item("tv", "Televisión", 4, ItemCategory.ELECTRONICS, "tv"),
        moving_item("chair", "Silla", 3, ItemCategory.FURNITURE, "chair"),
        moving_item("books", "Caja de libros", 3, ItemCategory.BOX, "books_box"),
        moving_item("clothes", "Caja de ropa", 2, ItemCategory.BOX, "clothes_box"),
        moving_item("lamp", "Lámpara", 2, ItemCategory.DECORATION, "lamp"),
        moving_item("plant", "Planta", 1, ItemCategory.DECORATION, "plant"),
    ),
    metadata=InstanceMetadata(
        difficulty="tutorial",
        description="Small outreach instance using concrete moving objects.",
    ),
)

engine = BinPackingEngine()
result = engine.solve(
    instance,
    RandomHyperHeuristic(seed=7),
    [FirstFit(), BestFit(), WorstFit(), NextFit()],
    DecreasingSize(),
    run_id="demo-run-001",
)

output = Path(__file__).with_name("demo_trace.json")
write_trace(result.trace, output)

print(f"bins_used={result.solution.bins_used}")
print(f"lower_bound={result.solution.lower_bound}")
print(f"utilization={result.solution.utilization:.3f}")
print(f"events={len(result.trace.events)}")
print(f"trace={output}")
