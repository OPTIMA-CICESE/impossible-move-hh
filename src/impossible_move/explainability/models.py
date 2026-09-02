from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class DecisionReason:
    """Machine-readable explanation for a hyper-heuristic score contribution.

    ``rule_id`` is intentionally language-neutral so a frontend can map it to
    localized human-readable text without coupling presentation concerns to the
    optimization layer.
    """

    rule_id: str
    heuristic_id: str
    contribution: float

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must be non-empty")
        if not self.heuristic_id.strip():
            raise ValueError("heuristic_id must be non-empty")
        if not isfinite(self.contribution):
            raise ValueError("decision reason contribution must be finite")
