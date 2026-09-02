class EngineError(RuntimeError):
    """Base error for invalid optimizer behavior."""


class InvalidOrderingError(EngineError):
    """Raised when an ordering strategy does not return a valid permutation."""


class InvalidHeuristicSelectionError(EngineError):
    """Raised when a hyper-heuristic selects an unavailable heuristic."""


class InvalidPlacementError(EngineError):
    """Raised when a low-level heuristic proposes an invalid placement."""
