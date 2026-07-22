from __future__ import annotations

from base_typed_string import (
    BaseConstrainedTypedString,
    BaseTypedStringConstraintViolationError,
)


class RequestExecutionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


def is_runtime_string(value: object) -> bool:
    return isinstance(value, str)


def main() -> None:
    digest = RequestExecutionDigest("a" * 64)

    print(f"value: {digest}")
    print(f"runtime type: {type(digest).__name__}")
    print(f"is real str: {is_runtime_string(digest)}")

    try:
        RequestExecutionDigest("invalid")
    except BaseTypedStringConstraintViolationError as constraint_error:
        print(f"rejected: {constraint_error}")


if __name__ == "__main__":
    main()
