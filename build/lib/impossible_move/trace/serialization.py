from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from impossible_move.explainability import DecisionReason

from .events import (
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
from .trace import RunTrace

_EVENT_TYPES = {
    cls.__name__: cls
    for cls in (
        RunStarted,
        ItemSelected,
        StateObserved,
        HeuristicSelected,
        PlacementEvaluated,
        PlacementSelected,
        BinCreated,
        ItemPlaced,
        RunFinished,
    )
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    return value


def event_to_dict(event: TraceEventType) -> dict[str, Any]:
    data = _jsonable(event)
    data["type"] = event.event_type
    return data


def trace_to_dict(trace: RunTrace) -> dict[str, Any]:
    return {
        "schema_version": trace.schema_version,
        "run_id": trace.run_id,
        "events": [event_to_dict(event) for event in trace.events],
    }


def trace_to_json(trace: RunTrace, *, indent: int = 2) -> str:
    return json.dumps(trace_to_dict(trace), ensure_ascii=False, indent=indent)


def write_trace(trace: RunTrace, path: str | Path) -> None:
    Path(path).write_text(trace_to_json(trace) + "\n", encoding="utf-8")


def event_from_dict(data: dict[str, Any]) -> TraceEventType:
    payload = dict(data)
    try:
        event_type = payload.pop("type")
    except KeyError as exc:
        raise ValueError("trace event is missing its type") from exc
    try:
        cls = _EVENT_TYPES[event_type]
    except KeyError as exc:
        raise ValueError(f"unknown event type {event_type!r}") from exc

    if cls is RunStarted:
        payload["heuristic_ids"] = tuple(payload["heuristic_ids"])
        payload["item_order"] = tuple(payload["item_order"])
    elif cls is HeuristicSelected:
        raw_reasons = payload.get("reasons", ())
        payload["reasons"] = tuple(
            reason if isinstance(reason, DecisionReason) else DecisionReason(**reason)
            for reason in raw_reasons
        )
    return cls(**payload)


def trace_from_dict(data: dict[str, Any]) -> RunTrace:
    version = data.get("schema_version")
    if version not in {"1.0", "1.1", "1.2"}:
        raise ValueError(f"unsupported trace schema version {version!r}")
    try:
        run_id = data["run_id"]
        raw_events = data["events"]
    except KeyError as exc:
        raise ValueError(f"trace is missing required field {exc.args[0]!r}") from exc
    if not isinstance(raw_events, list):
        raise ValueError("trace events must be a list")
    return RunTrace(
        schema_version=version,
        run_id=run_id,
        events=tuple(event_from_dict(event) for event in raw_events),
    )


def trace_from_json(raw: str) -> RunTrace:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("trace JSON root must be an object")
    return trace_from_dict(data)


def read_trace(path: str | Path) -> RunTrace:
    return trace_from_json(Path(path).read_text(encoding="utf-8"))
