from __future__ import annotations

from typing import Any, TypeVar

from base_typed_string._exceptions import (
    BaseTypedStringInvalidInputValueError,
)
from base_typed_string._pydantic_support import (
    build_typed_string_pydantic_core_schema,
)

BaseTypedStringType = TypeVar(
    "BaseTypedStringType",
    bound="BaseTypedString",
)


class BaseTypedString(str):
    """
    Transparent domain-typed string.

    Design rules:
    - stores an exact runtime subtype
    - behaves like plain str in normal string operations
    - normal string operations usually return plain str
    - preserves subtype in containers, pickle, and Pydantic model fields
    - does not introduce extra public domain-specific API
    """

    __slots__ = ()

    def __new__(
        cls: type[BaseTypedStringType],
        value: str,
    ) -> BaseTypedStringType:
        if not isinstance(value, str):  # pyright: ignore[reportUnnecessaryIsInstance] runtime boundary guard
            raise BaseTypedStringInvalidInputValueError(
                "BaseTypedString must be initialized only with str. "
                f"Got: {type(value).__name__}."
            )

        return str.__new__(cls, str.__str__(value))

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: Any,
    ) -> Any:
        """
        Provide Pydantic v2 validation and serialization.

        Validation:
        - accepts only strict str input
        - returns the exact subclass instance

        Serialization:
        - serializes as plain str
        """
        del source_type
        del handler

        return build_typed_string_pydantic_core_schema(cls)

    def __getnewargs__(self) -> tuple[str]:
        return (str.__str__(self),)

    def __reduce__(
        self,
    ) -> tuple[type[BaseTypedString], tuple[str]]:
        return (self.__class__, (str.__str__(self),))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str.__str__(self)!r})"
