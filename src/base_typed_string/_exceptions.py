class BaseTypedStringError(Exception):
    """Root exception for all base_typed_string errors."""


class BaseTypedStringConstraintConfigurationError(BaseTypedStringError, ValueError):
    """Raised when typed string constraints are configured incorrectly."""


class BaseTypedStringConstraintViolationError(BaseTypedStringError, ValueError):
    """Raised when a string value violates its declared constraints."""


class BaseTypedStringInvalidInputValueError(BaseTypedStringError, TypeError):
    """Raised when a non-string input value is provided."""


class BaseTypedStringInvariantViolationError(BaseTypedStringError):
    """Raised when an internal invariant or contract is violated."""
