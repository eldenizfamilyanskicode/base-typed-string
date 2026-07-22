from __future__ import annotations

import pickle

import pytest

from base_typed_string import BaseTypedString
from tests.testing_assertions import assert_exact_typed_string_instance
from tests.testing_types import (
    RequestExecutionDigest,
    SpecializedRequestExecutionDigest,
)


def test_constrained_getnewargs_returns_plain_string_tuple() -> None:
    constrained_value = RequestExecutionDigest("a" * 64)

    assert constrained_value.__getnewargs__() == ("a" * 64,)


def test_constrained_reduce_returns_exact_constructor_and_plain_string() -> None:
    constrained_value = RequestExecutionDigest("a" * 64)

    reduced_value: tuple[type[BaseTypedString], tuple[str]] = (
        constrained_value.__reduce__()
    )

    assert reduced_value == (RequestExecutionDigest, ("a" * 64,))


@pytest.mark.parametrize("pickle_protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_roundtrip_preserves_exact_constrained_subtype(
    pickle_protocol: int,
) -> None:
    source_value = RequestExecutionDigest("a" * 64)

    serialized_value = pickle.dumps(source_value, protocol=pickle_protocol)
    restored_value = pickle.loads(serialized_value)

    assert_exact_typed_string_instance(
        restored_value,
        expected_plain_value="a" * 64,
        expected_type=RequestExecutionDigest,
    )


def test_pickle_roundtrip_preserves_exact_second_level_constrained_subtype() -> None:
    source_value = SpecializedRequestExecutionDigest("b" * 64)

    serialized_value = pickle.dumps(source_value)
    restored_value = pickle.loads(serialized_value)

    assert_exact_typed_string_instance(
        restored_value,
        expected_plain_value="b" * 64,
        expected_type=SpecializedRequestExecutionDigest,
    )
