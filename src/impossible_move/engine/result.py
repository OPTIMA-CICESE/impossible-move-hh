from dataclasses import dataclass

from impossible_move.domain.models import BinPackingSolution
from impossible_move.trace.trace import RunTrace


@dataclass(frozen=True, slots=True)
class RunResult:
    solution: BinPackingSolution
    trace: RunTrace
