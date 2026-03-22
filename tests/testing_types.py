from __future__ import annotations

from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


class AdminUserName(UserName):
    pass


class EmailAddress(BaseTypedString):
    pass


class Account:
    def __init__(self, user_name: UserName) -> None:
        self.user_name: UserName = user_name
