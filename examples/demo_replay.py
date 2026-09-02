from pathlib import Path

from impossible_move.replay import ReplayActionType, ReplayController, ReplayMode
from impossible_move.trace.serialization import read_trace

trace_path = Path(__file__).with_name("demo_rule_trace.json")
trace = read_trace(trace_path)
controller = ReplayController(trace, mode=ReplayMode.PRESENTATION, speed=5.0)

print(f"run={trace.run_id}")
print(f"mode={controller.mode.value}")
print(f"speed={controller.speed:g}x interval={controller.interval_ms}ms")
print()

while (frame := controller.advance()) is not None:
    action = frame.action
    snapshot = frame.snapshot
    if action.type is ReplayActionType.FOCUS_ITEM:
        print(
            f"step {action.step:02d} | item={action.payload['item_id']} "
            f"size={action.payload['size']}"
        )
    elif action.type is ReplayActionType.SELECT_HEURISTIC:
        print(
            f"           | HH -> {snapshot.selected_heuristic_id} "
            f"scores={dict(snapshot.heuristic_scores)}"
        )
    elif action.type is ReplayActionType.CREATE_BIN:
        print(f"           | new truck/bin={action.payload['bin_id']}")
    elif action.type is ReplayActionType.PLACE_ITEM:
        print(
            f"           | place {action.payload['item_id']} -> "
            f"truck/bin {action.payload['bin_id']}"
        )
    elif action.type is ReplayActionType.RUN_FINISHED:
        assert snapshot.summary is not None
        print()
        print(
            f"finished | bins={snapshot.summary.bins_used} "
            f"utilization={snapshot.summary.utilization:.1%} "
            f"lower_bound={snapshot.summary.lower_bound}"
        )
        print(f"HH selections={dict(snapshot.heuristic_counts)}")
