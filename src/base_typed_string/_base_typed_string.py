from __future__ import annotations

from typing import Any, TypeVar

from ._exceptions import (
    BaseTypedStringInvalidInputValueError,
    BaseTypedStringInvariantViolationError,
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
        value: Any,
    ) -> BaseTypedStringType:
        if not isinstance(value, str):
            raise BaseTypedStringInvalidInputValueError(
                "BaseTypedString must be initialized only with str. "
                f"Got: {type(value).__name__}."
            )

        return str.__new__(cls, value)


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
        try:
            from pydantic_core import core_schema
        except ImportError as import_error:
            raise BaseTypedStringInvariantViolationError(
                "pydantic-core is required to build BaseTypedString schema."
            ) from import_error

        def serialize_to_plain_string(value: BaseTypedString) -> str:
            return str(value)

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(strict=True),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_to_plain_string,
                return_schema=core_schema.str_schema(),
            ),
        )

    def __getnewargs__(self) -> tuple[str]:
        return (str(self),)

    def __reduce__(
        self,
    ) -> tuple[type[BaseTypedString], tuple[str]]:
        return (self.__class__, (str(self),))
