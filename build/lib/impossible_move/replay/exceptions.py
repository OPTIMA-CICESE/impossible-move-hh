class ReplayError(Exception):
    """Base exception for replay-layer failures."""


class ReplayConsistencyError(ReplayError):
    """Raised when a trace cannot be reconstructed consistently."""
