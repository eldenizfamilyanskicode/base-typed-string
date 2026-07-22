from __future__ import annotations

from abc import ABC, ABCMeta
from typing import Any

import pytest

from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedStringConstraintConfigurationError,
    BaseTypedStringError,
)


def _create_constrained_type(
    class_name: str,
    class_attributes: dict[str, Any],
    *,
    parent_type: type[BaseConstrainedTypedString] = BaseConstrainedTypedString,
) -> type[BaseConstrainedTypedString]:
    return type(class_name, (parent_type,), class_attributes)


class ABCCompatibleConstrainedString(BaseConstrainedTypedString, ABC):
    min_length = 1


class DomainMeta(type):
    pass


class DomainMixin(metaclass=DomainMeta):
    pass


class CustomMetaclassConstrainedString(BaseConstrainedTypedString, DomainMixin):
    min_length = 1


def test_constrained_type_is_compatible_with_abc_meta() -> None:
    constrained_value = ABCCompatibleConstrainedString("value")

    assert type(ABCCompatibleConstrainedString) is ABCMeta
    assert type(constrained_value) is ABCCompatibleConstrainedString


def test_constrained_type_is_compatible_with_independent_metaclass() -> None:
    constrained_value = CustomMetaclassConstrainedString("value")

    assert type(CustomMetaclassConstrainedString) is DomainMeta
    assert type(constrained_value) is CustomMetaclassConstrainedString


@pytest.mark.parametrize(
    ("constraint_name", "invalid_value", "invalid_type_name"),
    [
        ("min_length", True, "bool"),
        ("min_length", 1.5, "float"),
        ("min_length", "1", "str"),
        ("max_length", False, "bool"),
        ("max_length", 1.5, "float"),
        ("max_length", "1", "str"),
    ],
)
def test_non_integer_length_configuration_is_rejected(
    constraint_name: str,
    invalid_value: object,
    invalid_type_name: str,
) -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type(
            "InvalidLengthType",
            {constraint_name: invalid_value},
        )

    assert str(caught_error.value) == (
        f"InvalidLengthType.{constraint_name} must be a non-negative int or None. "
        f"Got: {invalid_type_name}."
    )


@pytest.mark.parametrize("constraint_name", ["min_length", "max_length"])
def test_negative_length_configuration_is_rejected(constraint_name: str) -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type(
            "NegativeLength",
            {constraint_name: -1},
        )

    assert str(caught_error.value) == (
        f"NegativeLength.{constraint_name} must be non-negative. Got: -1."
    )


def test_zero_length_configuration_is_valid() -> None:
    zero_length_type = _create_constrained_type(
        "ZeroLength",
        {"min_length": 0, "max_length": 0},
    )

    assert zero_length_type("") == ""


def test_min_length_greater_than_max_length_is_rejected() -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type(
            "ReversedLengthRange",
            {"min_length": 3, "max_length": 2},
        )

    assert str(caught_error.value) == (
        "ReversedLengthRange.min_length must be less than or equal to max_length. "
        "Got: min_length=3, max_length=2."
    )


def test_non_string_pattern_is_rejected() -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type("NonStringPattern", {"pattern": 123})

    assert str(caught_error.value) == (
        "NonStringPattern.pattern must be str or None. Got: int."
    )


def test_invalid_regular_expression_is_rejected_at_class_definition() -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type("InvalidPattern", {"pattern": "["})

    assert str(caught_error.value) == (
        "InvalidPattern.pattern must be a valid Python regular expression. Got: '['."
    )
    assert caught_error.value.__cause__ is not None


def test_empty_regular_expression_is_valid_configuration() -> None:
    empty_pattern_type = _create_constrained_type(
        "EmptyPattern",
        {"pattern": ""},
    )

    assert empty_pattern_type("any-value") == "any-value"


class DeceptivelyEqualPattern(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


def test_pattern_string_subclass_is_normalized_to_plain_string() -> None:
    pattern_subclass_value = DeceptivelyEqualPattern(r"^[a-z]+$")

    constrained_type = _create_constrained_type(
        "NormalizedPattern",
        {"pattern": pattern_subclass_value},
    )

    assert constrained_type.pattern == r"^[a-z]+$"
    assert type(constrained_type.pattern) is str


def test_constraint_configuration_error_is_package_error_and_value_error() -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type("InvalidPattern", {"pattern": object()})

    assert isinstance(caught_error.value, BaseTypedStringError)
    assert isinstance(caught_error.value, ValueError)


class ParentConstrainedString(BaseConstrainedTypedString):
    min_length = 2
    max_length = 10


class NarrowerChildConstrainedString(ParentConstrainedString):
    min_length = 3
    max_length = 8
    pattern = r"^[a-z]+$"


class SameConstraintGrandchild(NarrowerChildConstrainedString):
    pass


class MinimumConstrainedString(BaseConstrainedTypedString):
    min_length = 2


class MaximumConstrainedString(BaseConstrainedTypedString):
    max_length = 5


class MultiplyInheritedConstrainedString(
    MinimumConstrainedString,
    MaximumConstrainedString,
):
    pass


def test_child_can_only_tighten_inherited_constraints() -> None:
    constrained_value = NarrowerChildConstrainedString("abcd")

    assert constrained_value == "abcd"
    assert type(constrained_value) is NarrowerChildConstrainedString

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        _create_constrained_type(
            "WeakerMinimum",
            {"min_length": 1},
            parent_type=ParentConstrainedString,
        )

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        _create_constrained_type(
            "RemovedMinimum",
            {"min_length": None},
            parent_type=ParentConstrainedString,
        )

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        _create_constrained_type(
            "WeakerMaximum",
            {"max_length": 11},
            parent_type=ParentConstrainedString,
        )

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        _create_constrained_type(
            "RemovedMaximum",
            {"max_length": None},
            parent_type=ParentConstrainedString,
        )


def test_grandchild_inherits_constraints_and_preserves_exact_type() -> None:
    constrained_value = SameConstraintGrandchild("abcd")

    assert constrained_value == "abcd"
    assert type(constrained_value) is SameConstraintGrandchild
    assert isinstance(constrained_value, NarrowerChildConstrainedString)


def test_multiple_inheritance_applies_every_parent_constraint() -> None:
    constrained_value = MultiplyInheritedConstrainedString("abc")

    assert constrained_value == "abc"

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        type(
            "WeakenedSecondParent",
            (MinimumConstrainedString, MaximumConstrainedString),
            {"max_length": 6},
        )


@pytest.mark.parametrize("replacement_pattern", [r"^[A-Z]+$", None])
def test_child_cannot_replace_or_remove_inherited_pattern(
    replacement_pattern: str | None,
) -> None:
    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        _create_constrained_type(
            "ReplacedPattern",
            {"pattern": replacement_pattern},
            parent_type=NarrowerChildConstrainedString,
        )

    assert "cannot replace or remove inherited pattern" in str(caught_error.value)


def test_string_subclass_cannot_spoof_inherited_pattern_comparison() -> None:
    deceptive_replacement = DeceptivelyEqualPattern(r"^[A-Z]+$")

    with pytest.raises(BaseTypedStringConstraintConfigurationError):
        _create_constrained_type(
            "DeceptivePatternReplacement",
            {"pattern": deceptive_replacement},
            parent_type=NarrowerChildConstrainedString,
        )


@pytest.mark.parametrize(
    ("constraint_name", "changed_value"),
    [
        ("min_length", 1),
        ("max_length", 6),
        ("pattern", r"^[A-Z]+$"),
    ],
)
def test_changed_constraint_is_rejected_on_next_use(
    constraint_name: str,
    changed_value: object,
) -> None:
    constrained_type = _create_constrained_type(
        "ChangedConstraint",
        {
            "max_length": 5,
            "min_length": 2,
            "pattern": r"^[a-z]+$",
        },
    )

    setattr(constrained_type, constraint_name, changed_value)

    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        constrained_type("abc")

    assert str(caught_error.value) == (
        f"ChangedConstraint.{constraint_name} cannot be changed after class creation. "
        "Declare constraints in the class body."
    )


def test_deleted_constraint_is_rejected_on_next_use() -> None:
    constrained_type = _create_constrained_type(
        "DeletedConstraint",
        {"pattern": r"^[a-z]+$"},
    )

    delattr(constrained_type, "pattern")

    with pytest.raises(BaseTypedStringConstraintConfigurationError) as caught_error:
        constrained_type("abc")

    assert str(caught_error.value) == (
        "DeletedConstraint.pattern cannot be changed after class creation. "
        "Declare constraints in the class body."
    )


def test_non_constraint_class_attributes_remain_mutable() -> None:
    description_attribute_name = "description"
    mutable_type = _create_constrained_type(
        "MutableNonConstraintAttribute",
        {description_attribute_name: "before"},
    )

    setattr(mutable_type, description_attribute_name, "after")
    assert getattr(mutable_type, description_attribute_name) == "after"

    delattr(mutable_type, description_attribute_name)
    assert not hasattr(mutable_type, description_attribute_name)
