class DomainError(ValueError):
    """Base error for invalid domain operations."""


class CapacityExceeded(DomainError):
    """Raised when an item cannot be placed in a bin."""


class DuplicateItemError(DomainError):
    """Raised when an instance contains duplicate item identifiers."""


class UnknownBinError(DomainError):
    """Raised when a referenced bin does not exist."""


class ItemAlreadyAssignedError(DomainError):
    """Raised when an item is assigned more than once."""
