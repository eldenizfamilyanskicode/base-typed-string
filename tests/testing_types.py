from __future__ import annotations

from base_typed_string import BaseConstrainedTypedString, BaseTypedString


class UserName(BaseTypedString):
    pass


class AdminUserName(UserName):
    pass


class EmailAddress(BaseTypedString):
    pass


class MisleadingUserName(BaseTypedString):
    """Test type whose display hook must not change its stored payload."""

    def __str__(self) -> str:
        return "spoofed-display-value"


class RequestExecutionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


class SpecializedRequestExecutionDigest(RequestExecutionDigest):
    pass


class Account:
    def __init__(self, user_name: UserName) -> None:
        self.user_name: UserName = user_name
