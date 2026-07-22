# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-22

### Added

- Added the public callable `BaseConstrainedTypedString` class alongside
  `BaseTypedString`.
- Added declarative `min_length`, `max_length`, and Python `re.search` pattern
  constraints that work without Pydantic.
- Added fail-fast class configuration checks, immutable-on-use constraint
  declarations, constraint-safe inheritance, and precompiled regular expressions.
- Added exact-subtype Pydantic v2 validation, plain-string serialization, and
  validation and serialization JSON Schema constraints.
- Added `BaseTypedStringConstraintConfigurationError` and
  `BaseTypedStringConstraintViolationError`.
- Added direct, inheritance, metaclass compatibility, pickle, Pydantic, schema,
  optional-dependency, and adversarial regression coverage.
- Added complete examples for direct and Pydantic constrained-string usage.

### Changed

- Hardened `BaseTypedString` construction, representation, pickle support, and
  Pydantic serialization to use the stored string payload rather than an
  overridable `__str__` result.
- Pydantic model-level string normalization can no longer silently alter typed
  strings; typed-string inputs remain strict and unmodified.
- Pydantic serialization now rejects invalid unvalidated model state instead of
  coercing an unrelated object to `str`.
- Package documentation now treats `BaseTypedString` as the unconstrained brand
  and `BaseConstrainedTypedString` as the intrinsic-invariant form.
- The minimum supported versions remain Python 3.10 and Pydantic 2.6; Python 3.14
  is now explicitly classified and tested.
- The project version now has one source of truth in
  `base_typed_string._version`.

### Migration notes

- Replace private backing classes plus
  `Annotated[..., StringConstraints(...), AfterValidator(...)]` aliases with one
  public `BaseConstrainedTypedString` subclass.
- `pattern` retains Python `re.search` semantics; it is not implicitly a full
  match.
- Removing an old private backing class can make previously stored pickle payloads
  unresolvable. Migrate those payloads before deleting the old import path.
- Applications that relied on Pydantic model-level stripping or case conversion
  for `BaseTypedString` fields must normalize explicitly before construction.

[Unreleased]: https://github.com/eldenizfamilyanskicode/base-typed-string/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/eldenizfamilyanskicode/base-typed-string/compare/v0.1.2...v0.2.0
