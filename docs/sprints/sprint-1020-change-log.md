# Sprint 1020 Change Log - Validation helper slug string-subclass guard

## Summary

Hardened shared generation-field slug creation so `slug()` rejects string subclasses for both the
requested value and fallback default before any string method or fallback return can occur.

## Security

`slug()` is used to derive ServiceNow update names for generated Business Rules, Client Scripts,
Script Includes, UI Policies, catalog items, catalog UI policies, and catalog client scripts. It now
requires exact strings for `value` and `default`; unsupported values fail with
`generation field scalar value contains non-JSON value`.

This prevents malformed in-process generation fields from executing caller-controlled `.strip()`,
`.lower()`, `__str__()`, or fallback-return behavior while deterministic builders derive
ServiceNow record names.

## Tests

- Added 1 failing-first slug value string-subclass assertion:
  `test_slug_rejects_string_subclass_without_string_method_execution`.
- Added 1 failing-first slug default string-subclass assertion:
  `test_slug_rejects_default_string_subclass_without_value_leak`.
- Added 1 documentation assertion:
  `test_sprint_1020_documents_validation_helper_slug_string_subclass_guard`.

## Verification

- `pytest tests/test_validation_helpers.py::test_slug_rejects_string_subclass_without_string_method_execution tests/test_validation_helpers.py::test_slug_rejects_default_string_subclass_without_value_leak -q`
  failed before implementation because the slug value subclass executed `.strip()` and the default
  subclass was accepted.
