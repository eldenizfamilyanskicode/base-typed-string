from __future__ import annotations

import pickle

from base_typed_string import BaseTypedString


class EmailAddress(BaseTypedString):
    pass


def print_section(title: str) -> None:
    separator: str = "=" * len(title)
    print()
    print(separator)
    print(title)
    print(separator)


def print_value_state(label: str, value: object) -> None:
    print(f"{label}:")
    print(f"  repr         : {value!r}")
    print(f"  runtime type : {type(value).__name__}")
    print()


def main() -> None:
    print_section("pickle roundtrip preserves exact subtype")

    source_email: EmailAddress = EmailAddress("hello@example.com")
    serialized_email: bytes = pickle.dumps(source_email)
    restored_email: object = pickle.loads(serialized_email)

    print_value_state("source_email", source_email)
    print_value_state("restored_email", restored_email)

    print(
        f"plain value preserved             : {restored_email == 'hello@example.com'}"
    )
    print(f"exact subtype preserved           : {type(restored_email) is EmailAddress}")
    print(f"isinstance(restored_email, str)   : {isinstance(restored_email, str)}")
    print(
        f"isinstance(restored_email, EmailAddress): "
        f"{isinstance(restored_email, EmailAddress)}"
    )
    print(f"serialized byte length            : {len(serialized_email)}")


if __name__ == "__main__":
    main()
