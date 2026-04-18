from __future__ import annotations

import json

from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import Account, AdminUserName, UserName


def test_second_level_subclass_has_plain_string_runtime_behavior() -> None:
    typed_value: AdminUserName = AdminUserName("root")

    uppercased_value: str = typed_value.upper()
    concatenated_value: str = typed_value + "!"
    replaced_value: str = typed_value.replace("r", "R")

    assert uppercased_value == "ROOT"
    assert concatenated_value == "root!"
    assert replaced_value == "Root"

    assert type(uppercased_value) is str
    assert type(concatenated_value) is str
    assert type(replaced_value) is str


def test_json_dumps_serializes_typed_string_as_plain_json_string() -> None:
    typed_value: UserName = UserName("alice")

    serialized_value: str = json.dumps(typed_value)
    restored_value: object = json.loads(serialized_value)

    assert serialized_value == '"alice"'
    assert restored_value == "alice"
    assert type(restored_value) is str


def test_json_dumps_serializes_empty_typed_string_as_plain_json_string() -> None:
    typed_value: UserName = UserName("")

    serialized_value: str = json.dumps(typed_value)
    restored_value: object = json.loads(serialized_value)

    assert serialized_value == '""'
    assert restored_value == ""
    assert type(restored_value) is str


def test_json_dumps_serializes_nested_payload_values_as_plain_strings() -> None:
    payload: dict[str, object] = {
        "user_name": UserName("alice"),
        "admin_user_name": AdminUserName("root"),
        "empty_user_name": UserName(""),
    }

    serialized_payload: str = json.dumps(payload)
    restored_payload: object = json.loads(serialized_payload)

    assert restored_payload == {
        "user_name": "alice",
        "admin_user_name": "root",
        "empty_user_name": "",
    }


def test_normal_string_operations_return_plain_str() -> None:
    typed_value: UserName = UserName("alice")

    uppercased_value: str = typed_value.upper()
    concatenated_value: str = typed_value + "!"
    replaced_value: str = typed_value.replace("a", "A")

    assert uppercased_value == "ALICE"
    assert concatenated_value == "alice!"
    assert replaced_value == "Alice"

    assert type(uppercased_value) is str
    assert type(concatenated_value) is str
    assert type(replaced_value) is str


def test_dict_value_preserves_exact_runtime_subtype_on_store_and_retrieve() -> None:
    typed_value: UserName = UserName("alice")

    values_by_field_name: dict[str, UserName] = {"user_name": typed_value}

    retrieved_value: UserName = values_by_field_name["user_name"]

    assert retrieved_value is typed_value
    assert_exact_typed_string_instance(
        retrieved_value,
        expected_plain_value="alice",
        expected_type=UserName,
    )


def test_typed_string_key_is_retrievable_by_plain_string_key() -> None:
    typed_key: UserName = UserName("alice")
    values_by_user_name: dict[str, str] = {typed_key: "present"}

    retrieved_by_typed_key: str = values_by_user_name[typed_key]
    retrieved_by_plain_string_key: str = values_by_user_name["alice"]

    stored_keys: list[str] = list(values_by_user_name.keys())
    stored_key: str = stored_keys[0]

    assert retrieved_by_typed_key == "present"
    assert retrieved_by_plain_string_key == "present"
    assert stored_key is typed_key
    assert_exact_typed_string_instance(
        stored_key,
        expected_plain_value="alice",
        expected_type=UserName,
    )


def test_typed_string_has_same_hash_and_equality_as_plain_string() -> None:
    typed_value: UserName = UserName("alice")
    plain_value: str = "alice"

    assert typed_value == plain_value
    assert hash(typed_value) == hash(plain_value)


def test_repr_uses_exact_runtime_subtype_name_and_plain_string_value() -> None:
    typed_value: AdminUserName = AdminUserName("root")

    rendered_value: str = repr(typed_value)

    assert rendered_value == "AdminUserName('root')"


def test_plain_class_attribute_preserves_exact_runtime_subtype() -> None:
    typed_value: UserName = UserName("alice")

    account: Account = Account(user_name=typed_value)

    retrieved_value: UserName = account.user_name

    assert retrieved_value is typed_value
    assert_exact_typed_string_instance(
        retrieved_value,
        expected_plain_value="alice",
        expected_type=UserName,
    )
