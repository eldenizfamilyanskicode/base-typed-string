from __future__ import annotations

import json
from typing import Any

import pytest

from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedString,
    BaseTypedStringConstraintViolationError,
    BaseTypedStringError,
    BaseTypedStringInvalidInputValueError,
)
from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import MisleadingUserName, RequestExecutionDigest


class ShortUppercaseCode(BaseConstrainedTypedString):
    min_length = 2
    max_length = 4
    pattern = r"^[A-Z]+$"


class ContainsDecimalDigit(BaseConstrainedTypedString):
    pattern = r"\d+"


class OneCharacterString(BaseConstrainedTypedString):
    min_length = 1
    max_length = 1


class EmptyStringOnly(BaseConstrainedTypedString):
    max_length = 0


class UnconstrainedIntermediateString(BaseConstrainedTypedString):
    pass


class MisleadingConstraintString(BaseConstrainedTypedString):
    pattern = r"^allowed$"

    def __str__(self) -> str:
        return "allowed"


class PrivateHelperNameCollisionString(BaseConstrainedTypedString):
    min_length = 2

    @classmethod
    def _validate_value_constraints(cls, **kwargs: Any) -> None:
        del cls
        del kwargs


def test_valid_value_preserves_exact_constrained_subtype() -> None:
    constrained_value: ShortUppercaseCode = ShortUppercaseCode("AB")

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="AB",
        expected_type=ShortUppercaseCode,
    )
    assert isinstance(constrained_value, BaseConstrainedTypedString)


def test_base_constrained_typed_string_can_be_instantiated_directly() -> None:
    constrained_value: BaseConstrainedTypedString = BaseConstrainedTypedString(
        "plain-value"
    )

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="plain-value",
        expected_type=BaseConstrainedTypedString,
    )


def test_subclass_without_constraints_has_explicit_no_op_behavior() -> None:
    constrained_value = UnconstrainedIntermediateString("plain-value")

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="plain-value",
        expected_type=UnconstrainedIntermediateString,
    )


@pytest.mark.parametrize("valid_value", ["AB", "ABC", "ABCD"])
def test_length_boundaries_are_inclusive(valid_value: str) -> None:
    assert ShortUppercaseCode(valid_value) == valid_value


def test_zero_max_length_accepts_only_empty_string() -> None:
    constrained_value = EmptyStringOnly("")

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="",
        expected_type=EmptyStringOnly,
    )

    with pytest.raises(BaseTypedStringConstraintViolationError):
        EmptyStringOnly("x")


def test_unicode_length_counts_characters_instead_of_encoded_bytes() -> None:
    constrained_value = OneCharacterString("😀")

    assert constrained_value == "😀"


def test_unanchored_pattern_uses_search_semantics() -> None:
    constrained_value = ContainsDecimalDigit("prefix-42-suffix")

    assert constrained_value == "prefix-42-suffix"


def test_value_below_min_length_raises_constraint_violation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError) as caught_error:
        ShortUppercaseCode("A")

    assert str(caught_error.value) == (
        "ShortUppercaseCode value violates min_length=2. Got length: 1."
    )


def test_value_above_max_length_raises_constraint_violation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError) as caught_error:
        ShortUppercaseCode("ABCDE")

    assert str(caught_error.value) == (
        "ShortUppercaseCode value violates max_length=4. Got length: 5."
    )


def test_pattern_mismatch_raises_constraint_violation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError) as caught_error:
        ShortUppercaseCode("ab")

    assert str(caught_error.value) == (
        "ShortUppercaseCode value violates pattern='^[A-Z]+$'."
    )


def test_constraint_violation_is_package_error_and_value_error() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError) as caught_error:
        ShortUppercaseCode("A")

    assert isinstance(caught_error.value, BaseTypedStringError)
    assert isinstance(caught_error.value, ValueError)


def test_constraint_error_does_not_expose_input_value() -> None:
    secret_invalid_value = "secret-lowercase-value"

    with pytest.raises(BaseTypedStringConstraintViolationError) as caught_error:
        ShortUppercaseCode(secret_invalid_value)

    assert secret_invalid_value not in str(caught_error.value)


def test_constructor_accepts_existing_base_typed_string() -> None:
    source_value = BaseTypedString("AB")

    constrained_value = ShortUppercaseCode(source_value)

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="AB",
        expected_type=ShortUppercaseCode,
    )


def test_constructor_ignores_source_string_subclass_display_override() -> None:
    source_value = MisleadingUserName("AB")

    constrained_value = ShortUppercaseCode(source_value)

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value="AB",
        expected_type=ShortUppercaseCode,
    )


def test_constructor_accepts_existing_constrained_typed_string() -> None:
    source_value = ShortUppercaseCode("AB")

    copied_value = ShortUppercaseCode(source_value)

    assert copied_value == source_value
    assert copied_value is not source_value
    assert type(copied_value) is ShortUppercaseCode


def test_non_string_input_uses_existing_invalid_input_error() -> None:
    invalid_value: Any = 123

    with pytest.raises(BaseTypedStringInvalidInputValueError):
        ShortUppercaseCode(invalid_value)


def test_constructor_does_not_normalize_before_validation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError):
        ShortUppercaseCode(" AB ")


def test_overridden_str_cannot_spoof_constraint_validation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError):
        MisleadingConstraintString("forbidden")


def test_private_helper_name_collision_cannot_bypass_validation() -> None:
    with pytest.raises(BaseTypedStringConstraintViolationError):
        PrivateHelperNameCollisionString("x")


def test_normal_string_operations_return_plain_str_without_revalidation() -> None:
    constrained_value = ShortUppercaseCode("AB")

    lowercased_value = constrained_value.lower()

    assert lowercased_value == "ab"
    assert type(lowercased_value) is str


def test_repr_uses_exact_constrained_subtype_name() -> None:
    constrained_value = ShortUppercaseCode("AB")

    assert repr(constrained_value) == "ShortUppercaseCode('AB')"


def test_hash_and_equality_match_plain_string() -> None:
    constrained_value = ShortUppercaseCode("AB")

    assert constrained_value == "AB"
    assert hash(constrained_value) == hash("AB")


def test_json_roundtrip_uses_plain_string_boundary() -> None:
    constrained_value = RequestExecutionDigest("a" * 64)

    serialized_value = json.dumps(constrained_value)
    restored_value = json.loads(serialized_value)

    assert serialized_value == f'"{"a" * 64}"'
    assert restored_value == "a" * 64
    assert type(restored_value) is str
