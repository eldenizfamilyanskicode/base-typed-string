from __future__ import annotations

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("pydantic_core")

from pydantic import BaseModel, ValidationError

from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import AdminUserName, EmailAddress


class ExampleModel(BaseModel):
    value: EmailAddress


class ContactModel(BaseModel):
    primary_email: EmailAddress
    email_list: list[EmailAddress]
    email_tuple: tuple[EmailAddress, ...]
    email_mapping: dict[str, EmailAddress]


class AdminExampleModel(BaseModel):
    value: AdminUserName


def test_pydantic_preserves_exact_second_level_subtype() -> None:
    model: AdminExampleModel = AdminExampleModel.model_validate({"value": "root"})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value="root",
        expected_type=AdminUserName,
    )


def test_pydantic_accepts_empty_string() -> None:
    model: ExampleModel = ExampleModel.model_validate({"value": ""})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value="",
        expected_type=EmailAddress,
    )


def test_pydantic_accepts_plain_string_and_returns_exact_subtype() -> None:
    model: ExampleModel = ExampleModel.model_validate({"value": "hello@example.com"})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value="hello@example.com",
        expected_type=EmailAddress,
    )


def test_pydantic_accepts_existing_typed_string_instance() -> None:
    typed_value: EmailAddress = EmailAddress("hello@example.com")

    model: ExampleModel = ExampleModel.model_validate({"value": typed_value})

    assert_exact_typed_string_instance(
        model.value,
        expected_plain_value="hello@example.com",
        expected_type=EmailAddress,
    )


def test_pydantic_rejects_non_string_input() -> None:
    with pytest.raises(ValidationError):
        ExampleModel.model_validate({"value": 123})


def test_pydantic_preserves_exact_runtime_subtypes_in_nested_data_structures() -> None:
    input_payload: dict[str, object] = {
        "primary_email": "primary@example.com",
        "email_list": ["list@example.com"],
        "email_tuple": ("tuple@example.com",),
        "email_mapping": {"work": "dict@example.com"},
    }

    model: ContactModel = ContactModel.model_validate(input_payload)

    assert_exact_typed_string_instance(
        model.primary_email,
        expected_plain_value="primary@example.com",
        expected_type=EmailAddress,
    )
    assert_exact_typed_string_instance(
        model.email_list[0],
        expected_plain_value="list@example.com",
        expected_type=EmailAddress,
    )
    assert_exact_typed_string_instance(
        model.email_tuple[0],
        expected_plain_value="tuple@example.com",
        expected_type=EmailAddress,
    )
    assert_exact_typed_string_instance(
        model.email_mapping["work"],
        expected_plain_value="dict@example.com",
        expected_type=EmailAddress,
    )


def test_pydantic_serializes_to_plain_strings() -> None:
    model: ContactModel = ContactModel.model_validate(
        {
            "primary_email": "primary@example.com",
            "email_list": ["list@example.com"],
            "email_tuple": ("tuple@example.com",),
            "email_mapping": {"work": "dict@example.com"},
        }
    )

    dumped_python: dict[str, object] = model.model_dump()
    dumped_json: str = model.model_dump_json()

    assert dumped_python == {
        "primary_email": "primary@example.com",
        "email_list": ["list@example.com"],
        "email_tuple": ("tuple@example.com",),
        "email_mapping": {"work": "dict@example.com"},
    }
    assert dumped_json == (
        '{"primary_email":"primary@example.com",'
        '"email_list":["list@example.com"],'
        '"email_tuple":["tuple@example.com"],'
        '"email_mapping":{"work":"dict@example.com"}}'
    )
