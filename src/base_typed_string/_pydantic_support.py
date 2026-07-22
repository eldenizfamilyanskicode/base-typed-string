from __future__ import annotations

from collections.abc import Callable
from re import Pattern
from typing import Any

from base_typed_string._exceptions import BaseTypedStringInvariantViolationError


def build_typed_string_pydantic_core_schema(
    typed_string_type: type[str],
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    pattern: str | None = None,
    compiled_pattern: Pattern[str] | None = None,
    configuration_validator: Callable[[], None] | None = None,
) -> Any:
    """Build a strict Pydantic v2 schema for one concrete typed string class."""
    try:
        from pydantic_core import (  # pyright: ignore[reportMissingImports]
            PydanticKnownError,
            PydanticSerializationError,
            core_schema,
        )
    except ImportError as import_error:
        raise BaseTypedStringInvariantViolationError(
            f"pydantic-core is required to build {typed_string_type.__name__} schema."
        ) from import_error

    def require_string_instance(value: object) -> str:
        if configuration_validator is not None:
            configuration_validator()

        if not isinstance(value, str):
            raise PydanticKnownError("string_type")

        return value

    def serialize_to_plain_string(value: object) -> str:
        if configuration_validator is not None:
            configuration_validator()

        if not isinstance(value, typed_string_type):
            raise PydanticSerializationError(
                f"Expected {typed_string_type.__name__} during serialization. "
                f"Got: {type(value).__name__}."
            )

        return str.__str__(value)

    input_schema: Any = core_schema.no_info_before_validator_function(
        require_string_instance,
        core_schema.str_schema(
            strict=True,
            min_length=min_length,
            max_length=max_length,
            strip_whitespace=False,
            to_lower=False,
            to_upper=False,
        ),
    )

    if pattern is not None and compiled_pattern is not None:

        def require_pattern_match(value: str) -> str:
            if compiled_pattern.search(value) is None:
                raise PydanticKnownError(
                    "string_pattern_mismatch",
                    {"pattern": pattern},
                )

            return value

        input_schema = core_schema.no_info_after_validator_function(
            require_pattern_match,
            input_schema,
        )

    return core_schema.no_info_after_validator_function(
        typed_string_type,
        input_schema,
        serialization=core_schema.plain_serializer_function_ser_schema(
            serialize_to_plain_string,
            return_schema=core_schema.str_schema(
                strict=True,
                min_length=min_length,
                max_length=max_length,
                strip_whitespace=False,
                to_lower=False,
                to_upper=False,
            ),
        ),
    )
