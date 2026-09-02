from __future__ import annotations

from dataclasses import dataclass

from .events import TraceEventType


SUPPORTED_SCHEMA_VERSIONS = ("1.0", "1.1", "1.2")
CURRENT_SCHEMA_VERSION = "1.2"


@dataclass(frozen=True, slots=True)
class RunTrace:
    run_id: str
    events: tuple[TraceEventType, ...]
    schema_version: str = CURRENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must be non-empty")
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(f"unsupported trace schema version {self.schema_version!r}")
        expected = list(range(len(self.events)))
        actual = [event.sequence for event in self.events]
        if actual != expected:
            raise ValueError(f"event sequences must be contiguous from zero; got {actual!r}")
        steps = [event.step for event in self.events]
        if steps != sorted(steps):
            raise ValueError("event steps must be non-decreasing")

    def events_for_step(self, step: int) -> tuple[TraceEventType, ...]:
        if step < 0:
            raise ValueError("step must be non-negative")
        return tuple(event for event in self.events if event.step == step)
