from __future__ import annotations

import pickle

from base_typed_string import BaseTypedString
from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import AdminUserName, UserName


def test_getnewargs_returns_plain_string_tuple() -> None:
    typed_value: UserName = UserName("alice")

    new_arguments: tuple[str] = typed_value.__getnewargs__()

    assert new_arguments == ("alice",)


def test_reduce_returns_constructor_and_plain_string_args() -> None:
    typed_value: UserName = UserName("alice")

    reduced_value: tuple[type[BaseTypedString], tuple[str]] = typed_value.__reduce__()
    constructor: type[BaseTypedString]
    constructor_arguments: tuple[str]
    constructor, constructor_arguments = reduced_value

    assert constructor is UserName
    assert constructor_arguments == ("alice",)


def test_pickle_roundtrip_preserves_exact_runtime_subtype() -> None:
    source_value: UserName = UserName("alice")

    serialized_value: bytes = pickle.dumps(source_value)
    restored_value: object = pickle.loads(serialized_value)

    assert_exact_typed_string_instance(
        restored_value,
        expected_plain_value="alice",
        expected_type=UserName,
    )


def test_pickle_roundtrip_preserves_exact_second_level_subtype() -> None:
    source_value: AdminUserName = AdminUserName("root")

    serialized_value: bytes = pickle.dumps(source_value)
    restored_value: object = pickle.loads(serialized_value)

    assert_exact_typed_string_instance(
        restored_value,
        expected_plain_value="root",
        expected_type=AdminUserName,
    )
