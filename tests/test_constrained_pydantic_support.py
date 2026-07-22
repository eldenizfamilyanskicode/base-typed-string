from __future__ import annotations

import json

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("pydantic_core")

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError
from pydantic_core import PydanticSerializationError

from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedString,
    BaseTypedStringConstraintConfigurationError,
)
from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import (
    RequestExecutionDigest,
    SpecializedRequestExecutionDigest,
)


class DigestModel(BaseModel):
    value: RequestExecutionDigest


class NestedDigestModel(BaseModel):
    primary_digest: RequestExecutionDigest
    digest_list: list[RequestExecutionDigest]
    digest_mapping: dict[str, RequestExecutionDigest]


class SpecializedDigestModel(BaseModel):
    value: SpecializedRequestExecutionDigest


class PythonRegexString(BaseConstrainedTypedString):
    pattern = r"^(?=.*[A-Z])[A-Za-z]+$"


class PythonRegexModel(BaseModel):
    value: PythonRegexString


class LengthOnlyString(BaseConstrainedTypedString):
    min_length = 1
    max_length = 3


class LengthOnlyModel(BaseModel):
    value: LengthOnlyString


class SearchPatternString(BaseConstrainedTypedString):
    pattern = "abc"


class SearchPatternModel(BaseModel):
    value: SearchPatternString


class UppercaseString(BaseConstrainedTypedString):
    pattern = r"^[A-Z]+$"


class MutationDetectedString(BaseConstrainedTypedString):
    min_length = 1


class NormalizationConfiguredModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_lower=True,
        coerce_numbers_to_str=True,
    )

    value: UppercaseString


VALID_DIGEST = "a" * 64


def test_pydantic_accepts_valid_string_and_returns_exact_constrained_subtype() -> None:
    model = DigestModel.model_validate({"value": VALID_DIGEST})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value=VALID_DIGEST,
        expected_type=RequestExecutionDigest,
    )


def test_pydantic_preserves_exact_second_level_constrained_subtype() -> None:
    model = SpecializedDigestModel.model_validate({"value": VALID_DIGEST})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value=VALID_DIGEST,
        expected_type=SpecializedRequestExecutionDigest,
    )


def test_pydantic_accepts_existing_constrained_instance() -> None:
    source_value = RequestExecutionDigest(VALID_DIGEST)

    model = DigestModel.model_validate({"value": source_value})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value=VALID_DIGEST,
        expected_type=RequestExecutionDigest,
    )


def test_pydantic_reconstructs_child_as_exact_declared_parent_type() -> None:
    source_value = SpecializedRequestExecutionDigest(VALID_DIGEST)

    model = DigestModel.model_validate({"value": source_value})

    assert type(model.value) is RequestExecutionDigest
    assert model.value == VALID_DIGEST


def test_pydantic_converts_other_typed_string_to_exact_target_type() -> None:
    source_value = BaseTypedString(VALID_DIGEST)

    model = DigestModel.model_validate({"value": source_value})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value=VALID_DIGEST,
        expected_type=RequestExecutionDigest,
    )


@pytest.mark.parametrize(
    ("invalid_value", "expected_error_type"),
    [
        ("a" * 63, "string_too_short"),
        ("a" * 65, "string_too_long"),
        ("A" * 64, "string_pattern_mismatch"),
    ],
)
def test_pydantic_rejects_each_constraint_violation(
    invalid_value: str,
    expected_error_type: str,
) -> None:
    with pytest.raises(ValidationError) as caught_error:
        DigestModel.model_validate({"value": invalid_value})

    assert caught_error.value.errors()[0]["type"] == expected_error_type


def test_pydantic_strictly_rejects_non_string_input() -> None:
    with pytest.raises(ValidationError) as caught_error:
        DigestModel.model_validate({"value": 123})

    assert caught_error.value.errors()[0]["type"] == "string_type"


def test_non_strict_pydantic_call_cannot_override_string_only_contract() -> None:
    constrained_adapter = TypeAdapter(RequestExecutionDigest)
    base_adapter = TypeAdapter(BaseTypedString)

    with pytest.raises(ValidationError):
        constrained_adapter.validate_python(b"a" * 64, strict=False)

    with pytest.raises(ValidationError):
        base_adapter.validate_python(b"plain-value", strict=False)


def test_pydantic_revalidates_forged_constrained_instance() -> None:
    adapter = TypeAdapter(RequestExecutionDigest)
    forged_invalid_value = str.__new__(RequestExecutionDigest, "invalid")

    with pytest.raises(ValidationError) as caught_error:
        adapter.validate_python(forged_invalid_value)

    assert caught_error.value.errors()[0]["type"] == "string_too_short"


def test_model_string_configuration_cannot_normalize_constrained_input() -> None:
    valid_model = NormalizationConfiguredModel.model_validate({"value": "ABC"})

    assert valid_model.value == "ABC"

    with pytest.raises(ValidationError):
        NormalizationConfiguredModel.model_validate({"value": " ABC "})

    with pytest.raises(ValidationError):
        NormalizationConfiguredModel.model_validate({"value": 123})


def test_cached_pydantic_schema_rejects_changed_constraint_declaration() -> None:
    adapter = TypeAdapter(MutationDetectedString)
    source_value = MutationDetectedString("a")
    changed_minimum_length = 2

    MutationDetectedString.min_length = changed_minimum_length
    try:
        with pytest.raises(ValidationError, match="cannot be changed"):
            adapter.validate_python("aa")

        with pytest.raises(PydanticSerializationError, match="cannot be changed"):
            adapter.dump_python(source_value)

        with pytest.raises(
            BaseTypedStringConstraintConfigurationError,
            match="cannot be changed",
        ):
            adapter.json_schema()
    finally:
        MutationDetectedString.min_length = 1


def test_pydantic_preserves_exact_subtype_in_nested_containers() -> None:
    model = NestedDigestModel.model_validate(
        {
            "primary_digest": VALID_DIGEST,
            "digest_list": [VALID_DIGEST],
            "digest_mapping": {"request": VALID_DIGEST},
        }
    )

    assert type(model.primary_digest) is RequestExecutionDigest
    assert type(model.digest_list[0]) is RequestExecutionDigest
    assert type(model.digest_mapping["request"]) is RequestExecutionDigest


def test_pydantic_model_validate_json_constructs_exact_subtype() -> None:
    json_payload = json.dumps({"value": VALID_DIGEST})

    model = DigestModel.model_validate_json(json_payload)

    assert type(model.value) is RequestExecutionDigest
    assert model.value == VALID_DIGEST


def test_pydantic_serializes_constrained_values_as_plain_strings() -> None:
    model = DigestModel.model_validate({"value": VALID_DIGEST})

    dumped_python = model.model_dump()
    dumped_json = model.model_dump_json()

    assert dumped_python == {"value": VALID_DIGEST}
    assert type(dumped_python["value"]) is str
    assert dumped_json == f'{{"value":"{VALID_DIGEST}"}}'


def test_type_adapter_returns_exact_constrained_subtype() -> None:
    adapter = TypeAdapter(RequestExecutionDigest)

    constrained_value = adapter.validate_python(VALID_DIGEST)

    assert_exact_typed_string_instance(
        constrained_value,
        expected_plain_value=VALID_DIGEST,
        expected_type=RequestExecutionDigest,
    )


def test_json_schema_exposes_all_string_constraints() -> None:
    value_schema = DigestModel.model_json_schema()["properties"]["value"]

    assert value_schema == {
        "maxLength": 64,
        "minLength": 64,
        "pattern": "^[0-9a-f]{64}$",
        "title": "Value",
        "type": "string",
    }


def test_json_schema_without_pattern_does_not_add_pattern_keyword() -> None:
    value_schema = LengthOnlyModel.model_json_schema()["properties"]["value"]

    assert value_schema == {
        "maxLength": 3,
        "minLength": 1,
        "title": "Value",
        "type": "string",
    }


def test_validation_and_serialization_json_schemas_expose_constraints() -> None:
    adapter = TypeAdapter(RequestExecutionDigest)

    validation_schema = adapter.json_schema(mode="validation")
    serialization_schema = adapter.json_schema(mode="serialization")

    expected_schema = {
        "maxLength": 64,
        "minLength": 64,
        "pattern": "^[0-9a-f]{64}$",
        "type": "string",
    }
    assert validation_schema == expected_schema
    assert serialization_schema == expected_schema


def test_python_specific_regex_has_same_constructor_and_pydantic_behavior() -> None:
    direct_value = PythonRegexString("Agent")
    model = PythonRegexModel.model_validate({"value": "Agent"})

    assert direct_value == "Agent"
    assert type(model.value) is PythonRegexString

    with pytest.raises(ValidationError):
        PythonRegexModel.model_validate({"value": "agent"})


def test_pattern_search_semantics_match_in_constructor_and_pydantic() -> None:
    direct_value = SearchPatternString("prefix-abc-suffix")
    model = SearchPatternModel.model_validate({"value": "prefix-abc-suffix"})

    assert direct_value == "prefix-abc-suffix"
    assert model.value == "prefix-abc-suffix"
