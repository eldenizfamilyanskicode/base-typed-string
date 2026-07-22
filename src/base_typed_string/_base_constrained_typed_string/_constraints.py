from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from base_typed_string._exceptions import (
    BaseTypedStringConstraintConfigurationError,
    BaseTypedStringConstraintViolationError,
)


@dataclass(frozen=True, slots=True)
class ConstraintConfiguration:
    min_length: int | None
    max_length: int | None
    pattern: str | None
    compiled_pattern: re.Pattern[str] | None


EMPTY_CONSTRAINT_CONFIGURATION = ConstraintConfiguration(
    min_length=None,
    max_length=None,
    pattern=None,
    compiled_pattern=None,
)


def build_effective_constraint_configuration(
    *,
    class_name: str,
    class_namespace: Mapping[str, object],
    parent_configurations: Iterable[ConstraintConfiguration],
) -> ConstraintConfiguration:
    parent_configuration_values = tuple(parent_configurations)
    min_length_value = class_namespace.get(
        "min_length",
        _inherited_min_length(parent_configuration_values),
    )
    max_length_value = class_namespace.get(
        "max_length",
        _inherited_max_length(parent_configuration_values),
    )
    pattern_value = class_namespace.get(
        "pattern",
        _inherited_pattern(parent_configuration_values),
    )

    configuration = _build_constraint_configuration(
        class_name=class_name,
        min_length_value=min_length_value,
        max_length_value=max_length_value,
        pattern_value=pattern_value,
    )
    validate_inherited_constraints(
        class_name=class_name,
        configuration=configuration,
        parent_configurations=parent_configuration_values,
    )
    return configuration


def _build_constraint_configuration(
    *,
    class_name: str,
    min_length_value: object,
    max_length_value: object,
    pattern_value: object,
) -> ConstraintConfiguration:
    min_length = _validated_length_constraint(
        class_name=class_name,
        constraint_name="min_length",
        constraint_value=min_length_value,
    )
    max_length = _validated_length_constraint(
        class_name=class_name,
        constraint_name="max_length",
        constraint_value=max_length_value,
    )

    if min_length is not None and max_length is not None and min_length > max_length:
        raise BaseTypedStringConstraintConfigurationError(
            f"{class_name}.min_length must be less than or equal to max_length. "
            f"Got: min_length={min_length}, max_length={max_length}."
        )

    pattern, compiled_pattern = _validated_pattern_constraint(
        class_name=class_name,
        constraint_value=pattern_value,
    )

    return ConstraintConfiguration(
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        compiled_pattern=compiled_pattern,
    )


def _inherited_min_length(
    parent_configurations: Iterable[ConstraintConfiguration],
) -> int | None:
    inherited_values = tuple(
        configuration.min_length
        for configuration in parent_configurations
        if configuration.min_length is not None
    )
    return max(inherited_values, default=None)


def _inherited_max_length(
    parent_configurations: Iterable[ConstraintConfiguration],
) -> int | None:
    inherited_values = tuple(
        configuration.max_length
        for configuration in parent_configurations
        if configuration.max_length is not None
    )
    return min(inherited_values, default=None)


def _inherited_pattern(
    parent_configurations: Iterable[ConstraintConfiguration],
) -> str | None:
    return next(
        (
            configuration.pattern
            for configuration in parent_configurations
            if configuration.pattern is not None
        ),
        None,
    )


def validate_constraint_declaration_unchanged(
    *,
    class_name: str,
    configuration: ConstraintConfiguration,
    current_min_length: object,
    current_max_length: object,
    current_pattern: object,
) -> None:
    if not _length_declaration_matches(
        current_value=current_min_length,
        configured_value=configuration.min_length,
    ):
        _raise_changed_constraint(class_name, "min_length")

    if not _length_declaration_matches(
        current_value=current_max_length,
        configured_value=configuration.max_length,
    ):
        _raise_changed_constraint(class_name, "max_length")

    if not _pattern_declaration_matches(
        current_value=current_pattern,
        configured_value=configuration.pattern,
    ):
        _raise_changed_constraint(class_name, "pattern")


def validate_inherited_constraints(
    *,
    class_name: str,
    configuration: ConstraintConfiguration,
    parent_configurations: Iterable[ConstraintConfiguration],
) -> None:
    for parent_configuration in parent_configurations:
        if parent_configuration.min_length is not None and (
            configuration.min_length is None
            or configuration.min_length < parent_configuration.min_length
        ):
            raise BaseTypedStringConstraintConfigurationError(
                f"{class_name}.min_length cannot weaken inherited "
                f"min_length={parent_configuration.min_length}."
            )

        if parent_configuration.max_length is not None and (
            configuration.max_length is None
            or configuration.max_length > parent_configuration.max_length
        ):
            raise BaseTypedStringConstraintConfigurationError(
                f"{class_name}.max_length cannot weaken inherited "
                f"max_length={parent_configuration.max_length}."
            )

        if (
            parent_configuration.pattern is not None
            and configuration.pattern != parent_configuration.pattern
        ):
            raise BaseTypedStringConstraintConfigurationError(
                f"{class_name}.pattern cannot replace or remove inherited "
                f"pattern {parent_configuration.pattern!r}."
            )


def validate_value_constraints(
    *,
    class_name: str,
    value: str,
    configuration: ConstraintConfiguration,
) -> None:
    value_length = len(value)

    if configuration.min_length is not None and value_length < configuration.min_length:
        raise BaseTypedStringConstraintViolationError(
            f"{class_name} value violates min_length={configuration.min_length}. "
            f"Got length: {value_length}."
        )

    if configuration.max_length is not None and value_length > configuration.max_length:
        raise BaseTypedStringConstraintViolationError(
            f"{class_name} value violates max_length={configuration.max_length}. "
            f"Got length: {value_length}."
        )

    if (
        configuration.compiled_pattern is not None
        and configuration.compiled_pattern.search(value) is None
    ):
        raise BaseTypedStringConstraintViolationError(
            f"{class_name} value violates pattern={configuration.pattern!r}."
        )


def _length_declaration_matches(
    *,
    current_value: object,
    configured_value: int | None,
) -> bool:
    if configured_value is None:
        return current_value is None

    return type(current_value) is int and current_value == configured_value


def _pattern_declaration_matches(
    *,
    current_value: object,
    configured_value: str | None,
) -> bool:
    if configured_value is None:
        return current_value is None

    return type(current_value) is str and current_value == configured_value


def _raise_changed_constraint(class_name: str, constraint_name: str) -> None:
    raise BaseTypedStringConstraintConfigurationError(
        f"{class_name}.{constraint_name} cannot be changed after class creation. "
        "Declare constraints in the class body."
    )


def _validated_length_constraint(
    *,
    class_name: str,
    constraint_name: str,
    constraint_value: object,
) -> int | None:
    if constraint_value is None:
        return None

    if type(constraint_value) is not int:
        raise BaseTypedStringConstraintConfigurationError(
            f"{class_name}.{constraint_name} must be a non-negative int or None. "
            f"Got: {type(constraint_value).__name__}."
        )

    if constraint_value < 0:
        raise BaseTypedStringConstraintConfigurationError(
            f"{class_name}.{constraint_name} must be non-negative. "
            f"Got: {constraint_value}."
        )

    return constraint_value


def _validated_pattern_constraint(
    *,
    class_name: str,
    constraint_value: object,
) -> tuple[str | None, re.Pattern[str] | None]:
    if constraint_value is None:
        return None, None

    if not isinstance(constraint_value, str):
        raise BaseTypedStringConstraintConfigurationError(
            f"{class_name}.pattern must be str or None. "
            f"Got: {type(constraint_value).__name__}."
        )

    plain_pattern = str.__str__(constraint_value)

    try:
        compiled_pattern: re.Pattern[str] = re.compile(plain_pattern)
    except re.error as pattern_error:
        raise BaseTypedStringConstraintConfigurationError(
            f"{class_name}.pattern must be a valid Python regular expression. "
            f"Got: {plain_pattern!r}."
        ) from pattern_error

    return plain_pattern, compiled_pattern
