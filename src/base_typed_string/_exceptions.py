class BaseTypedStringError(Exception):
    """Root exception for all base_typed_string errors."""


class BaseTypedStringInvalidInputValueError(BaseTypedStringError, TypeError):
    """Raised when a non-string input value is provided."""


class BaseTypedStringInvariantViolationError(BaseTypedStringError):
    """Raised when an internal invariant or contract is violated."""
