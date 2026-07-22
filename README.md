# base-typed-string

`base_typed_string` is a small Python library for building callable,
domain-specific string classes that remain real `str` objects at runtime.

It provides both unconstrained and declaratively constrained branded strings with
exact runtime subtype preservation.

It is designed for codebases where values such as `UserName`, `EmailAddress`, `AccountKey`, or `RawInputStr` should be:

- strongly named in type annotations
- real `str` objects at runtime
- serializable as plain strings
- reconstructable at validation boundaries
- lightweight and predictable
- easy for humans and coding agents to declare correctly

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

## Choose a base class

| Need | Base class |
| --- | --- |
| A callable branded string with no intrinsic value rules | `BaseTypedString` |
| A callable branded string with length or regex rules | `BaseConstrainedTypedString` |

Both choices create real classes. A public domain type never needs a private backing
class plus an `Annotated` alias.

---

## What it guarantees

- accepts only `str`
- preserves the exact subclass type at construction time
- behaves like normal `str`
- normal string operations return plain `str`
- preserves subtype through pickle roundtrip
- supports Pydantic v2, but does not require it
- ships `py.typed`
- optionally enforces `min_length`, `max_length`, and `pattern`
- exposes declared constraints in Pydantic-generated JSON Schema

---

## What it intentionally does not do

- no normalization
- no string coercion
- no domain-specific methods
- no Pydantic dependency for direct construction and validation

`BaseTypedString` has no built-in value rules. `BaseConstrainedTypedString` provides
only deterministic length and Python regular-expression checks.

More complex domain rules should live in your application layer.

---

## Why not plain `str` / `NewType` / custom wrapper?

### Why not plain `str`?

Because plain `str` does not communicate domain intent.

```python
def create_user(user_name: str, email_address: str) -> None:
    ...
```

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

## Constrained typed strings

Use `BaseConstrainedTypedString` when a rule belongs to the named type itself:

```python
from base_typed_string import BaseConstrainedTypedString


class RequestExecutionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


digest: RequestExecutionDigest = RequestExecutionDigest("a" * 64)

assert type(digest) is RequestExecutionDigest
assert isinstance(digest, str)
```

The public symbol is a real, callable class. Construction validates the value even
when Pydantic is not installed:

```python
from base_typed_string import BaseTypedStringConstraintViolationError


try:
    RequestExecutionDigest("not-a-digest")
except BaseTypedStringConstraintViolationError:
    pass
```

### Constraint properties

| Property | Meaning |
| --- | --- |
| `min_length` | Inclusive minimum `len(value)` |
| `max_length` | Inclusive maximum `len(value)` |
| `pattern` | Python regular expression searched with `re.search` |

All properties default to `None`. Length is measured using Python `len`, which
counts Unicode code points rather than encoded bytes. An unanchored pattern may
match part of a value. Use anchors when the whole value must follow a format. Under
Python regex rules, `$` may also match immediately before one trailing newline; use
`\A...\Z` when that distinction matters, while noting that those Python-specific
anchors may not be portable to every JSON Schema consumer.

Constraint declarations are sealed when the class is created because Pydantic caches
schemas. Declare them in the class body. Changing or deleting an effective value later
is rejected the next time the class is constructed, validated, serialized, or used to
build a schema. Detection on use avoids imposing a custom metaclass, so constrained
types remain compatible with `ABC` and other independently metaclassed bases. A
constrained subtype may tighten inherited length limits, but it cannot weaken them or
replace an inherited pattern.

### Canonical declaration for coding agents

When constraints are invariants of a named domain string, declare one public class:

```python
from base_typed_string import BaseConstrainedTypedString


class ScheduledActionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"
```

Do not create a private backing class plus a public `Annotated` type alias:

```python
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from base_typed_string import BaseTypedString


# Avoid this for invariants of a named domain type (Python 3.12+).
class _ScheduledActionDigest(BaseTypedString):
    pass


type ScheduledActionDigest = Annotated[
    _ScheduledActionDigest,
    StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$"),
    AfterValidator(_ScheduledActionDigest),
]
```

A PEP 695 `type` alias is not callable and splits one domain concept across two
runtime names. The older assignment form, `ScheduledActionDigest = Annotated[...]`,
may appear callable because it forwards construction to its origin, but direct calls
do not apply the Pydantic metadata and the alias is still not a class.

Do not wrap a branded class in field-level Pydantic `StringConstraints` either.
Pydantic's outer string processing can turn the validated subtype back into plain
`str`. Put every reusable invariant on the `BaseConstrainedTypedString` subclass.
`Annotated[str, ...]` remains appropriate for a local field constraint that does not
define a reusable branded type.

### Static typing

The constrained class is the annotation as well as the constructor:

```python
def store_digest(value: RequestExecutionDigest) -> None:
    ...


store_digest(RequestExecutionDigest("a" * 64))  # accepted
store_digest("a" * 64)  # static type error
```

A constrained value can be used wherever `str` is expected. A plain `str` or a
different branded string is not implicitly the constrained type.

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

`BaseConstrainedTypedString` applies the same type guard first, then checks its
declared constraints. A string that violates a constraint raises
`BaseTypedStringConstraintViolationError`. Package exception messages include the
class and failed rule, but never echo the input value because it may contain
sensitive data.

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

* validation accepts only real `str` inputs, even when `strict=False` is requested
* runtime model values preserve the exact subtype
* exported payloads are plain strings
* constrained types publish `minLength`, `maxLength`, and `pattern` in JSON Schema

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

Constrained classes are used directly as field annotations—no `Annotated`,
`StringConstraints`, or `AfterValidator` is required:

```python
from pydantic import BaseModel, ValidationError

from base_typed_string import BaseConstrainedTypedString


class RequestExecutionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


class RequestModel(BaseModel):
    digest: RequestExecutionDigest


request_model = RequestModel.model_validate({"digest": "a" * 64})

assert type(request_model.digest) is RequestExecutionDigest
assert RequestModel.model_json_schema()["properties"]["digest"]["pattern"] == (
    "^[0-9a-f]{64}$"
)

try:
    RequestModel.model_validate({"digest": "invalid"})
except ValidationError:
    pass
```

The package deliberately uses Python `re.search` itself instead of delegating regex
matching to Pydantic. This keeps behavior identical across supported Pydantic v2
versions and direct construction. Patterns are trusted class configuration: avoid
expressions vulnerable to catastrophic backtracking, and remember that Python regex
features may not be understood by every JSON Schema consumer.

Pydantic does not validate ordinary field defaults unless its
`validate_default=True` option is enabled. Enable default validation when a model
declares typed-string defaults from plain strings.

Pydantic string-normalization settings such as `str_strip_whitespace`, `str_to_lower`,
and `str_to_upper` do not alter either typed-string base class. Normalize explicitly
before construction when normalization is part of an input-boundary policy rather
than an invariant of the stored domain value.

APIs such as `model_construct()` and unchecked assignment can bypass Pydantic
validation. If they leave a typed-string field holding a different runtime type,
serialization raises an error instead of silently coercing that value to `str`.

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

When migrating an existing private backing class plus `Annotated` alias, remember that
old pickle payloads reference the private class by module and name. Keep that class
available while old payloads exist, or migrate those payloads explicitly.

Unpickling calls the typed-string constructor again. If a later release of your
application tightens a class constraint, old payloads that no longer satisfy the
invariant fail explicitly during restoration.

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
from base_typed_string import BaseConstrainedTypedString
from base_typed_string import BaseTypedString
from base_typed_string import BaseTypedStringConstraintConfigurationError
from base_typed_string import BaseTypedStringConstraintViolationError
from base_typed_string import BaseTypedStringError
from base_typed_string import BaseTypedStringInvalidInputValueError
from base_typed_string import BaseTypedStringInvariantViolationError
```

### Exceptions

#### `BaseTypedStringError`

Root exception for all package-specific errors.

#### `BaseTypedStringConstraintConfigurationError`

Raised when a declaration is invalid or a post-definition change is detected.

#### `BaseTypedStringConstraintViolationError`

Raised when a direct constructor receives a string that violates declared constraints.

#### `BaseTypedStringInvalidInputValueError`

Raised when a non-string input value is provided.

#### `BaseTypedStringInvariantViolationError`

Raised when an internal invariant or contract is violated.

---

## Design notes

`BaseTypedString` is intended for projects that want domain-specific names without giving up normal `str` runtime behavior.

`BaseConstrainedTypedString` adds reusable intrinsic value invariants while preserving
the same callable class, runtime subtype, serialization, and static typing model.

This is especially useful when you have many semantic string types such as:

* `AccountKey`
* `PromptKeyStr`
* `RawInputStr`
* `IntegrationName`
* `UserTextInputStr`
* `ValidatedInputStr`

Both base classes stay intentionally small so that domain typing remains explicit and
predictable for human authors, static analyzers, and coding agents.

---

## Development

### Run tests

```bash
uv run pytest
```

### Run lint

```bash
uv run ruff check .
uv run ruff format --check .
```

### Run type checking

```bash
uv run mypy
uv run pyright
```

### Build package

```bash
uv run python -m build
```

### Validate distribution metadata

```bash
uv run twine check --strict dist/*
```

### Release process

The version has one source of truth in
`src/base_typed_string/_version.py`. See [CHANGELOG.md](CHANGELOG.md) for release
history and [RELEASING.md](RELEASING.md) for the guarded tag, GitHub Release, and
PyPI Trusted Publishing procedure.

---

## Compatibility

* Python 3.10+
* CPython
* optional Pydantic v2 support

---

## License

MIT
