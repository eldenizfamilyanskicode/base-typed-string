from __future__ import annotations

from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


class Account:
    def __init__(self, user_name: UserName) -> None:
        self.user_name: UserName = user_name


def print_section(title: str) -> None:
    separator: str = "=" * len(title)
    print()
    print(separator)
    print(title)
    print(separator)


def print_value_state(label: str, value: object) -> None:
    print(f"{label}:")
    print(f"  repr                  : {value!r}")
    print(f"  runtime type          : {type(value).__name__}")
    print(f"  isinstance(value, str): {isinstance(value, str)}")
    print()


def print_runtime_membership(label: str, value: object) -> None:
    print(f"isinstance({label}, UserName)   : {isinstance(value, UserName)}")
    print(f"isinstance({label}, str)        : {isinstance(value, str)}")


def demonstrate_direct_runtime_identity() -> None:
    print_section("1. direct construction")

    user_name: UserName = UserName("alice")

    print_value_state("constructed value", user_name)
    print(f"value == 'alice'                  : {user_name == 'alice'}")
    print(f"type(user_name) is UserName       : {type(user_name) is UserName}")
    print_runtime_membership("user_name", user_name)


def demonstrate_container_and_attribute_behavior() -> None:
    print_section("2. containers and class attributes")

    source_user_name: UserName = UserName("alice")

    user_name_list: list[UserName] = [source_user_name]
    user_name_by_field_name: dict[str, UserName] = {
        "user_name": source_user_name,
    }
    values_by_user_name: dict[str, str] = {
        source_user_name: "present",
    }
    account: Account = Account(user_name=source_user_name)

    retrieved_from_list: UserName = user_name_list[0]
    retrieved_from_dict_value: UserName = user_name_by_field_name["user_name"]
    retrieved_from_attribute: UserName = account.user_name
    retrieved_by_typed_key: str = values_by_user_name[source_user_name]
    retrieved_by_plain_string_key: str = values_by_user_name["alice"]

    stored_keys: tuple[str, ...] = tuple(values_by_user_name.keys())
    stored_key_object: str = stored_keys[0]

    print_value_state("source_user_name", source_user_name)
    print_value_state("retrieved_from_list", retrieved_from_list)
    print_value_state("retrieved_from_dict_value", retrieved_from_dict_value)
    print_value_state("retrieved_from_attribute", retrieved_from_attribute)
    print_value_state("stored_key_object", stored_key_object)

    print(
        f"list keeps same object            : {retrieved_from_list is source_user_name}"
    )
    print(
        f"dict value keeps same object      : "
        f"{retrieved_from_dict_value is source_user_name}"
    )
    print(
        f"class attribute keeps same object : "
        f"{retrieved_from_attribute is source_user_name}"
    )
    print(
        f"dict key object is same object    : {stored_key_object is source_user_name}"
    )
    print(f"typed key lookup works            : {retrieved_by_typed_key == 'present'}")
    print(
        f"plain str key lookup works        : "
        f"{retrieved_by_plain_string_key == 'present'}"
    )
    print(f"stored key exact subtype kept     : {type(stored_key_object) is UserName}")


def demonstrate_normal_string_operations() -> None:
    print_section("3. normal string operations")

    user_name: UserName = UserName("alice")

    uppercased_value: str = user_name.upper()
    replaced_value: str = user_name.replace("a", "A")
    concatenated_value: str = user_name + "!"

    print_value_state("user_name", user_name)
    print_value_state("uppercased_value", uppercased_value)
    print_value_state("replaced_value", replaced_value)
    print_value_state("concatenated_value", concatenated_value)

    print(f"type(uppercased_value) is str     : {type(uppercased_value) is str}")
    print(f"type(replaced_value) is str       : {type(replaced_value) is str}")
    print(f"type(concatenated_value) is str   : {type(concatenated_value) is str}")
    print("verdict                           : normal str operations return plain str")


def main() -> None:
    demonstrate_direct_runtime_identity()
    demonstrate_container_and_attribute_behavior()
    demonstrate_normal_string_operations()


if __name__ == "__main__":
    main()
