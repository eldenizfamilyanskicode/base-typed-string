from __future__ import annotations

from typing import Any, ClassVar, TypeVar, cast

import base_typed_string._base_constrained_typed_string._constraints as _constraints
from base_typed_string._base_typed_string import BaseTypedString
from base_typed_string._pydantic_support import (
    build_typed_string_pydantic_core_schema,
)

BaseConstrainedTypedStringType = TypeVar(
    "BaseConstrainedTypedStringType",
    bound="BaseConstrainedTypedString",
)
_CONSTRAINT_CONFIGURATION_ATTRIBUTE_NAME = "_constraint_configuration"


def _effective_constraint_configuration(
    typed_string_type: type[BaseConstrainedTypedString],
) -> _constraints.ConstraintConfiguration:
    configuration = cast(
        _constraints.ConstraintConfiguration,
        getattr(typed_string_type, _CONSTRAINT_CONFIGURATION_ATTRIBUTE_NAME),
    )
    _constraints.validate_constraint_declaration_unchanged(
        class_name=typed_string_type.__name__,
        configuration=configuration,
        current_min_length=typed_string_type.min_length,
        current_max_length=typed_string_type.max_length,
        current_pattern=typed_string_type.pattern,
    )
    return configuration


class BaseConstrainedTypedString(BaseTypedString):
    """
    Callable domain-typed string with declarative value constraints.

    Subclasses may declare ``min_length``, ``max_length``, and ``pattern`` as
    class attributes. Construction accepts only ``str``, validates every declared
    constraint, and returns the exact subclass. Constraint declarations cannot be
    changed after class creation and may only become stricter in subclasses.

    ``pattern`` uses Python ``re.search`` semantics. The class performs no
    normalization or coercion and does not require Pydantic for direct use.
    """

    __slots__ = ()

    min_length: ClassVar[int | None] = None
    max_length: ClassVar[int | None] = None
    pattern: ClassVar[str | None] = None

    _constraint_configuration: ClassVar[_constraints.ConstraintConfiguration] = (
        _constraints.EMPTY_CONSTRAINT_CONFIGURATION
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        parent_configurations = tuple(
            _effective_constraint_configuration(parent_type)
            for parent_type in cls.__mro__[1:]
            if issubclass(parent_type, BaseConstrainedTypedString)
        )
        configuration = _constraints.build_effective_constraint_configuration(
            class_name=cls.__name__,
            class_namespace=vars(cls),
            parent_configurations=parent_configurations,
        )

        type.__setattr__(cls, "min_length", configuration.min_length)
        type.__setattr__(cls, "max_length", configuration.max_length)
        type.__setattr__(cls, "pattern", configuration.pattern)
        type.__setattr__(
            cls,
            _CONSTRAINT_CONFIGURATION_ATTRIBUTE_NAME,
            configuration,
        )

    def __new__(
        cls: type[BaseConstrainedTypedStringType],
        value: str,
    ) -> BaseConstrainedTypedStringType:
        typed_value: BaseConstrainedTypedStringType = super().__new__(cls, value)
        _constraints.validate_value_constraints(
            class_name=cls.__name__,
            value=str.__str__(typed_value),
            configuration=_effective_constraint_configuration(cls),
        )
        return typed_value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: Any,
    ) -> Any:
        """Build a strict constrained string schema that returns the exact subtype."""
        del source_type
        del handler

        configuration = _effective_constraint_configuration(cls)

        def validate_configuration() -> None:
            _effective_constraint_configuration(cls)

        return build_typed_string_pydantic_core_schema(
            cls,
            min_length=configuration.min_length,
            max_length=configuration.max_length,
            pattern=configuration.pattern,
            compiled_pattern=configuration.compiled_pattern,
            configuration_validator=validate_configuration,
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: Any,
        handler: Any,
    ) -> Any:
        """Expose the Python-regex constraint in generated JSON Schema."""
        configuration = _effective_constraint_configuration(cls)
        json_schema: dict[str, Any] = handler(core_schema)

        if configuration.pattern is not None:
            json_schema["pattern"] = configuration.pattern

        return json_schema
