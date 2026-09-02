from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from impossible_move.trace.events import PlacementEvaluated, PlacementSelected, StateObserved, TraceEventType
from impossible_move.trace.policy import TracePolicy
from impossible_move.trace.trace import RunTrace

TEvent = TypeVar("TEvent", bound=TraceEventType)


class TraceRecorder:
    """Append-only recorder with policy-based diagnostic compaction."""

    def __init__(self, run_id: str, policy: TracePolicy = TracePolicy.FULL) -> None:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        self.run_id = run_id
        self.policy = TracePolicy(policy)
        self._events: list[TraceEventType] = []

    def _keep(self, event: TraceEventType) -> bool:
        if self.policy is TracePolicy.FULL:
            return True
        if isinstance(event, PlacementEvaluated):
            return False
        if self.policy is TracePolicy.COMPACT and isinstance(event, (StateObserved, PlacementSelected)):
            return False
        return True

    def append(self, event: TEvent) -> TEvent:
        if not self._keep(event):
            return event
        event = replace(event, sequence=len(self._events))
        self._events.append(event)
        return event

    def build(self) -> RunTrace:
        return RunTrace(run_id=self.run_id, events=tuple(self._events))
