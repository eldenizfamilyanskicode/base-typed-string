from __future__ import annotations

import inspect
from importlib.metadata import version

import base_typed_string
from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedString,
    BaseTypedStringConstraintConfigurationError,
    BaseTypedStringConstraintViolationError,
    BaseTypedStringError,
    BaseTypedStringInvalidInputValueError,
    BaseTypedStringInvariantViolationError,
)


def test_public_api_exports_both_base_classes_and_all_package_errors() -> None:
    expected_export_names = [
        "BaseConstrainedTypedString",
        "BaseTypedString",
        "BaseTypedStringConstraintConfigurationError",
        "BaseTypedStringConstraintViolationError",
        "BaseTypedStringError",
        "BaseTypedStringInvalidInputValueError",
        "BaseTypedStringInvariantViolationError",
    ]
    expected_export_values = [
        BaseConstrainedTypedString,
        BaseTypedString,
        BaseTypedStringConstraintConfigurationError,
        BaseTypedStringConstraintViolationError,
        BaseTypedStringError,
        BaseTypedStringInvalidInputValueError,
        BaseTypedStringInvariantViolationError,
    ]

    assert base_typed_string.__all__ == expected_export_names
    assert [
        getattr(base_typed_string, export_name) for export_name in expected_export_names
    ] == expected_export_values


def test_constrained_base_is_a_real_callable_string_class() -> None:
    assert inspect.isclass(BaseConstrainedTypedString)
    assert callable(BaseConstrainedTypedString)
    assert issubclass(BaseConstrainedTypedString, BaseTypedString)
    assert issubclass(BaseConstrainedTypedString, str)
    assert (
        BaseConstrainedTypedString.__module__
        == "base_typed_string._base_constrained_typed_string._base"
    )


def test_runtime_version_matches_installed_project_metadata() -> None:
    assert base_typed_string.__version__ == version("base-typed-string")
