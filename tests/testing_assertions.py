from __future__ import annotations

from typing import TypeVar

from base_typed_string import BaseTypedString

BaseTypedStringSubtype = TypeVar(
    "BaseTypedStringSubtype",
    bound=BaseTypedString,
)


def assert_exact_typed_string_instance(
    value: object,
    *,
    expected_plain_value: str,
    expected_type: type[BaseTypedStringSubtype],
) -> None:
    assert value == expected_plain_value
    assert isinstance(value, expected_type)
    assert isinstance(value, BaseTypedString)
    assert isinstance(value, str)
    assert type(value) is expected_type
