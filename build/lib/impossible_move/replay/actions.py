from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from impossible_move.trace.events import (
    BinCreated,
    HeuristicSelected,
    ItemPlaced,
    ItemSelected,
    PlacementEvaluated,
    PlacementSelected,
    RunFinished,
    RunStarted,
    StateObserved,
    TraceEventType,
)
from impossible_move.trace.serialization import event_to_dict


class ReplayMode(str, Enum):
    DETAILED = "detailed"
    PRESENTATION = "presentation"


class ReplayActionType(str, Enum):
    RUN_STARTED = "run_started"
    FOCUS_ITEM = "focus_item"
    STATE_OBSERVED = "state_observed"
    SELECT_HEURISTIC = "select_heuristic"
    EVALUATE_BIN = "evaluate_bin"
    SELECT_PLACEMENT = "select_placement"
    CREATE_BIN = "create_bin"
    PLACE_ITEM = "place_item"
    RUN_FINISHED = "run_finished"


_EVENT_ACTIONS: dict[type, ReplayActionType] = {
    RunStarted: ReplayActionType.RUN_STARTED,
    ItemSelected: ReplayActionType.FOCUS_ITEM,
    StateObserved: ReplayActionType.STATE_OBSERVED,
    HeuristicSelected: ReplayActionType.SELECT_HEURISTIC,
    PlacementEvaluated: ReplayActionType.EVALUATE_BIN,
    PlacementSelected: ReplayActionType.SELECT_PLACEMENT,
    BinCreated: ReplayActionType.CREATE_BIN,
    ItemPlaced: ReplayActionType.PLACE_ITEM,
    RunFinished: ReplayActionType.RUN_FINISHED,
}

_PRESENTATION_ACTIONS = frozenset(
    {
        ReplayActionType.RUN_STARTED,
        ReplayActionType.FOCUS_ITEM,
        ReplayActionType.SELECT_HEURISTIC,
        ReplayActionType.CREATE_BIN,
        ReplayActionType.PLACE_ITEM,
        ReplayActionType.RUN_FINISHED,
    }
)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ReplayAction:
    type: ReplayActionType
    sequence: int
    step: int
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.sequence < 0 or self.step < 0:
            raise ValueError("action sequence and step must be non-negative")
        object.__setattr__(self, "payload", _freeze(dict(self.payload)))


def action_from_event(event: TraceEventType) -> ReplayAction:
    try:
        action_type = _EVENT_ACTIONS[type(event)]
    except KeyError as exc:
        raise TypeError(f"unsupported replay event type {type(event).__name__}") from exc
    payload = event_to_dict(event)
    for key in ("type", "sequence", "step", "timestamp_ns"):
        payload.pop(key, None)
    return ReplayAction(
        type=action_type,
        sequence=event.sequence,
        step=event.step,
        payload=payload,
    )


def is_visible(action_type: ReplayActionType, mode: ReplayMode) -> bool:
    if mode is ReplayMode.DETAILED:
        return True
    return action_type in _PRESENTATION_ACTIONS
