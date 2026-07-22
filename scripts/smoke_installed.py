from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
from collections.abc import Sequence
from importlib.metadata import version as distribution_version

import base_typed_string
from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedString,
    BaseTypedStringConstraintViolationError,
)


class AgentKey(BaseTypedString):
    __slots__ = ()


class Digest(BaseConstrainedTypedString):
    __slots__ = ()

    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test an installed base-typed-string distribution."
    )
    parser.add_argument("--expected-version", required=True)
    pydantic_mode = parser.add_mutually_exclusive_group(required=True)
    pydantic_mode.add_argument("--with-pydantic", action="store_true")
    pydantic_mode.add_argument("--without-pydantic", action="store_true")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed_arguments = build_argument_parser().parse_args(arguments)

    expected_version = parsed_arguments.expected_version
    if base_typed_string.__version__ != expected_version:
        raise AssertionError(base_typed_string.__version__)
    if distribution_version("base-typed-string") != expected_version:
        raise AssertionError(distribution_version("base-typed-string"))

    key = AgentKey("agent")
    digest = Digest("a" * 64)
    if type(key) is not AgentKey or type(digest) is not Digest:
        raise AssertionError("Exact runtime subtype was not preserved.")
    if json.dumps({"digest": digest}) != '{"digest": "' + "a" * 64 + '"}':
        raise AssertionError("JSON serialization did not use a plain string.")
    if type(pickle.loads(pickle.dumps(digest))) is not Digest:
        raise AssertionError("Pickle roundtrip did not preserve the subtype.")

    try:
        Digest("invalid")
    except BaseTypedStringConstraintViolationError:
        pass
    else:
        raise AssertionError("Invalid constrained value was accepted.")

    pydantic_is_installed = importlib.util.find_spec("pydantic") is not None
    if parsed_arguments.without_pydantic:
        if pydantic_is_installed:
            raise AssertionError("Pydantic unexpectedly exists in the base-only venv.")
    else:
        if not pydantic_is_installed:
            raise AssertionError("The pydantic extra did not install Pydantic.")

        from pydantic import TypeAdapter

        restored_digest = TypeAdapter(Digest).validate_python("b" * 64)
        if type(restored_digest) is not Digest:
            raise AssertionError("Pydantic did not construct the exact subtype.")

    mode = "with Pydantic" if parsed_arguments.with_pydantic else "without Pydantic"
    print(f"Installed distribution smoke passed for {expected_version} {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
