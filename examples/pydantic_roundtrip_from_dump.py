from __future__ import annotations

import json

from pydantic import BaseModel

from base_typed_string import BaseTypedString


class EmailAddress(BaseTypedString):
    pass


class ContactModel(BaseModel):
    primary_email: EmailAddress
    backup_email: EmailAddress


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
    source_model: ContactModel = ContactModel.model_validate(
        {
            "primary_email": "primary@example.com",
            "backup_email": "backup@example.com",
        }
    )

    dumped_python: dict[str, object] = source_model.model_dump()
    dumped_json: str = source_model.model_dump_json()
    loaded_json_payload: dict[str, object] = json.loads(dumped_json)

    restored_from_python_dump: ContactModel = ContactModel.model_validate(dumped_python)
    restored_from_json_payload: ContactModel = ContactModel.model_validate(
        loaded_json_payload
    )

    print_section("1. source model runtime values")

    print_value_state("source_model.primary_email", source_model.primary_email)
    print_value_state("source_model.backup_email", source_model.backup_email)

    print_section("2. exported payload loses subtype")

    print(f"dumped_python                     : {dumped_python}")
    print(f"dumped_json                       : {dumped_json}")
    print(f"loaded_json_payload               : {loaded_json_payload}")

    print_value_state(
        "dumped_python['primary_email']",
        dumped_python["primary_email"],
    )
    print_value_state(
        "loaded_json_payload['primary_email']",
        loaded_json_payload["primary_email"],
    )

    print(
        f"python dump is plain str          : "
        f"{type(dumped_python['primary_email']) is str}"
    )
    print(
        f"json payload is plain str         : "
        f"{type(loaded_json_payload['primary_email']) is str}"
    )

    print_section("3. validation rebuilds exact subtype")

    print_value_state(
        "restored_from_python_dump.primary_email",
        restored_from_python_dump.primary_email,
    )
    print_value_state(
        "restored_from_json_payload.primary_email",
        restored_from_json_payload.primary_email,
    )

    print(
        f"restored from python dump         : "
        f"{type(restored_from_python_dump.primary_email) is EmailAddress}"
    )
    print(
        f"restored from json payload        : "
        f"{type(restored_from_json_payload.primary_email) is EmailAddress}"
    )

    print_section("4. final verdict")

    print("dump/export boundary              : subtype is flattened to plain str")
    print("validation boundary               : subtype is reconstructed correctly")
    print(
        f"original model unchanged          : "
        f"{type(source_model.primary_email) is EmailAddress}"
    )


if __name__ == "__main__":
    main()
