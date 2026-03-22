from __future__ import annotations

from typing import Any

import pytest

from base_typed_string import BaseTypedString, BaseTypedStringInvalidInputValueError
from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import AdminUserName, UserName


def test_empty_string_is_valid() -> None:
    typed_value: UserName = UserName("")

    assert_exact_typed_string_instance(
        typed_value,
        expected_plain_value="",
        expected_type=UserName,
    )


def test_second_level_subclass_instantiation_preserves_exact_runtime_type() -> None:
    typed_value: AdminUserName = AdminUserName("root")

    assert_exact_typed_string_instance(
        typed_value,
        expected_plain_value="root",
        expected_type=AdminUserName,
    )

    assert isinstance(typed_value, UserName)


def test_base_typed_string_can_be_instantiated_directly() -> None:
    typed_value: BaseTypedString = BaseTypedString("plain-value")

    assert_exact_typed_string_instance(
        typed_value,
        expected_plain_value="plain-value",
        expected_type=BaseTypedString,
    )


def test_subclass_instantiation_preserves_exact_runtime_type() -> None:
    typed_value: UserName = UserName("alice")

    assert_exact_typed_string_instance(
        typed_value,
        expected_plain_value="alice",
        expected_type=UserName,
    )


def test_constructor_accepts_existing_typed_string_instance() -> None:
    source_value: UserName = UserName("alice")

    copied_value: UserName = UserName(source_value)

    assert_exact_typed_string_instance(
        copied_value,
        expected_plain_value="alice",
        expected_type=UserName,
    )


@pytest.mark.parametrize(
    ("invalid_value", "expected_type_name"),
    [
        (123, "int"),
        (None, "NoneType"),
        (True, "bool"),
        (3.14, "float"),
        (object(), "object"),
    ],
)
def test_non_string_input_raises_domain_error(
    invalid_value: Any,
    expected_type_name: str,
) -> None:
    with pytest.raises(BaseTypedStringInvalidInputValueError) as caught_error:
        UserName(invalid_value)

    error_message: str = str(caught_error.value)

    assert "BaseTypedString must be initialized only with str" in error_message
    assert expected_type_name in error_message
