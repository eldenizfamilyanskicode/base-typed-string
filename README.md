# base-typed-string

Strict typed string base class with exact runtime subtype preservation.

`base_typed_string` is a small Python library for building domain-specific string types that remain real `str` objects at runtime.

It is designed for codebases where values such as `UserName`, `EmailAddress`, `AccountKey`, or `RawInputStr` should be:

- strongly named in type annotations
- real `str` objects at runtime
- serializable as plain strings
- reconstructable at validation boundaries
- lightweight and predictable

---

## Why

Sometimes a value is semantically important enough to deserve its own type, but operationally it should still behave like a normal Python string.

Examples:

- `UserName`
- `EmailAddress`
- `AccountKey`
- `RawInputStr`
- `IntegrationName`
- `ValidatedInputStr`

Using plain `str` everywhere loses domain meaning.
Using wrappers changes runtime behavior.
Using `NewType` helps only static typing.

`base_typed_string` gives you a middle ground:
domain-specific names in type annotations, while keeping real `str` behavior at runtime.

---

## What it guarantees

- accepts only `str`
- preserves the exact subclass type at construction time
- behaves like normal `str`
- normal string operations return plain `str`
- preserves subtype through pickle roundtrip
- supports Pydantic v2, but does not require it
- ships `py.typed`

---

## What it intentionally does not do

- no built-in validation rules
- no normalization
- no regex engine
- no domain-specific methods

This package is intentionally minimal.

Domain rules should live in your subclasses or in your application layer.

---

## Why not plain `str` / `NewType` / custom wrapper?

### Why not plain `str`?

Because plain `str` does not communicate domain intent.

```python
def create_user(user_name: str, email_address: str) -> None:
    ...
````

This is easy to misuse:

* parameters can be swapped accidentally
* type annotations do not explain domain meaning
* static analysis cannot distinguish semantic string types

With typed subclasses:

```python
def create_user(user_name: UserName, email_address: EmailAddress) -> None:
    ...
```

the intent is explicit.

### Why not `typing.NewType`?

`NewType` is a static typing tool, not a runtime type.

```python
from typing import NewType

UserName = NewType("UserName", str)

user_name: UserName = UserName("alice")

assert type(user_name) is str
assert isinstance(user_name, str)
```

This means:

* runtime values are still plain `str`
* there is no real subclass at runtime
* runtime boundaries cannot preserve a concrete semantic subtype
* introspection and runtime behavior cannot distinguish `UserName` from plain `str`

`base_typed_string` creates a real runtime subtype instead.

### Why not a custom wrapper class?

A wrapper can model a domain value, but it stops being a real string.

Typical trade-offs:

* `isinstance(value, str)` becomes `False`
* JSON serialization often needs custom handling
* many libraries expect plain `str`, not wrapper objects
* you often need explicit `.value` extraction
* interoperability becomes noisier

A wrapper is useful when you want rich behavior and strict encapsulation.

`base_typed_string` is for the opposite case:
keep the value operationally identical to `str`, while still having a named domain type.

### When `base_typed_string` is the right choice

Use it when you want:

* semantic string types in annotations
* real `str` behavior at runtime
* plain string serialization
* clean interoperability with Python and library code

Do not use it when you need:

* heavy domain logic on the value object
* mutable state
* multiple fields
* non-string runtime representation

---

## Installation

### Base package

```bash
pip install base-typed-string
```

### With Pydantic v2 support

```bash
pip install "base-typed-string[pydantic]"
```

If Pydantic v2 is already installed in your project, integration works automatically.

### For development

```bash
pip install "base-typed-string[dev]"
```

---

## Quick start

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


user_name: UserName = UserName("alice")

assert user_name == "alice"
assert isinstance(user_name, str)
assert isinstance(user_name, UserName)
assert type(user_name) is UserName
```

---

## How to use it in your project

Create a module for your domain string types.

For example, create a file named `domain_typings.py`:

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    """User login name."""


class EmailAddress(BaseTypedString):
    """User email address."""
```

Then use these types in your application code:

```python
from .domain_typings import EmailAddress, UserName


def create_user(user_name: UserName, email_address: EmailAddress) -> None:
    print(user_name, email_address)
```

This gives you:

* domain-specific names in type annotations
* real `str` values at runtime
* plain string serialization behavior
* reconstruction through validation layers such as Pydantic

---

## Runtime behavior

`BaseTypedString` is a real `str` subclass.

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


user_name: UserName = UserName("alice")

assert isinstance(user_name, str)
assert isinstance(user_name, UserName)
assert type(user_name) is UserName
assert user_name == "alice"
```

### Normal string operations return plain `str`

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


user_name: UserName = UserName("alice")

uppercased_value: str = user_name.upper()
concatenated_value: str = user_name + "!"
replaced_value: str = user_name.replace("a", "A")

assert type(uppercased_value) is str
assert type(concatenated_value) is str
assert type(replaced_value) is str
```

This behavior is intentional.

The typed subtype is preserved at construction and validation boundaries, not across ordinary string operations.

---

## Constructor rules

Only `str` values are accepted.

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


UserName("alice")     # valid
UserName(123)         # raises BaseTypedStringInvalidInputValueError
UserName(None)        # raises BaseTypedStringInvalidInputValueError
```

Existing typed string instances are also accepted because they are still real strings:

```python
from base_typed_string import BaseTypedString


class UserName(BaseTypedString):
    pass


source_user_name: UserName = UserName("alice")
copied_user_name: UserName = UserName(source_user_name)

assert copied_user_name == "alice"
assert type(copied_user_name) is UserName
```

Direct instantiation of the base class is also supported:

```python
from base_typed_string import BaseTypedString


plain_typed_value: BaseTypedString = BaseTypedString("value")

assert plain_typed_value == "value"
assert type(plain_typed_value) is BaseTypedString
```

---

## Pydantic v2 support

When used as a Pydantic field type:

* validation accepts strict strings
* runtime model values preserve the exact subtype
* exported payloads are plain strings

```python
from pydantic import BaseModel

from base_typed_string import BaseTypedString


class EmailAddress(BaseTypedString):
    pass


class ContactModel(BaseModel):
    primary_email: EmailAddress
    backup_email: EmailAddress


contact_model: ContactModel = ContactModel.model_validate(
    {
        "primary_email": "primary@example.com",
        "backup_email": "backup@example.com",
    }
)

assert type(contact_model.primary_email) is EmailAddress
assert type(contact_model.backup_email) is EmailAddress

dumped_python: dict[str, object] = contact_model.model_dump()

assert dumped_python == {
    "primary_email": "primary@example.com",
    "backup_email": "backup@example.com",
}
assert type(dumped_python["primary_email"]) is str
```

### Important boundary

Inside the validated model, the exact subtype is preserved.

After serialization or export, values intentionally become plain strings.

This is a feature, not a bug.

---

## Pickle support

Pickle roundtrip preserves the exact subtype.

```python
import pickle

from base_typed_string import BaseTypedString


class EmailAddress(BaseTypedString):
    pass


source_email: EmailAddress = EmailAddress("hello@example.com")
serialized_email: bytes = pickle.dumps(source_email)
restored_email: object = pickle.loads(serialized_email)

assert restored_email == "hello@example.com"
assert type(restored_email) is EmailAddress
```

---

## JSON behavior

Since `BaseTypedString` inherits from `str`, standard JSON serialization naturally produces plain JSON strings.

```python
import json

from base_typed_string import BaseTypedString


class EmailAddress(BaseTypedString):
    pass


value: EmailAddress = EmailAddress("hello@example.com")
serialized_value: str = json.dumps(value)
restored_value: object = json.loads(serialized_value)

assert serialized_value == '"hello@example.com"'
assert restored_value == "hello@example.com"
assert type(restored_value) is str
```

This behavior is intentional.

JSON is a plain data boundary.

The exact runtime subtype exists only inside Python objects.
After serialization, values become plain strings and do not carry subtype information.

---


## Public API

```python
from base_typed_string import BaseTypedString
from base_typed_string import BaseTypedStringError
from base_typed_string import BaseTypedStringInvalidInputValueError
from base_typed_string import BaseTypedStringInvariantViolationError
```

### Exceptions

#### `BaseTypedStringError`

Root exception for all package-specific errors.

#### `BaseTypedStringInvalidInputValueError`

Raised when a non-string input value is provided.

#### `BaseTypedStringInvariantViolationError`

Raised when an internal invariant or contract is violated.

---

## Design notes

`BaseTypedString` is intended for projects that want domain-specific names without giving up normal `str` runtime behavior.

This is especially useful when you have many semantic string types such as:

* `AccountKey`
* `PromptKeyStr`
* `RawInputStr`
* `IntegrationName`
* `UserTextInputStr`
* `ValidatedInputStr`

The base class stays intentionally small so that your domain layer remains explicit and predictable.

---

## Development

### Run tests

```bash
pytest
```

### Run lint

```bash
ruff check .
```

### Run type checking

```bash
mypy .
pyright
```

### Build package

```bash
python -m build
```

### Validate distribution metadata

```bash
twine check dist/*
```

---

## Compatibility

* Python 3.10+
* CPython
* optional Pydantic v2 support

---

## License

MIT