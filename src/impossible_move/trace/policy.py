from __future__ import annotations

from enum import Enum


class TracePolicy(str, Enum):
    """Controls how much diagnostic information is persisted in a run trace.

    FULL is intended for small teaching instances. STANDARD preserves state
    observations but aggregates placement evaluations. COMPACT keeps only the
    events required to explain and replay the selected HH trajectory.
    """

    FULL = "full"
    STANDARD = "standard"
    COMPACT = "compact"

    @classmethod
    def for_item_count(cls, item_count: int) -> "TracePolicy":
        if item_count <= 20:
            return cls.FULL
        if item_count <= 100:
            return cls.STANDARD
        return cls.COMPACT
