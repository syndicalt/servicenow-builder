# Sprint 1025 Change Log - Runtime CSV exact-string guard

## Summary

Hardened runtime CSV parsing so malformed public-web CSV setting values are rejected before splitting
or item validation.

## Security

`_csv_values()` now routes input through the shared exact-string runtime setting reader before
calling `.split(",")`. Values must be exact strings or `None`; string subclasses and non-string
objects fail with `<SETTING> must be a string runtime setting`.

This prevents malformed runtime configuration maps from executing caller-controlled CSV string hooks
and prevents Python attribute diagnostics from leaking object type names while parsing
`JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` or `JEDI_PUBLIC_WEB_DOC_URLS`.

## Tests

- Added 1 failing-first runtime CSV non-string assertion:
  `test_runtime_csv_values_rejects_non_string_without_truthiness_leak`.
- Added 1 failing-first runtime CSV string-subclass assertion:
  `test_runtime_csv_values_rejects_string_subclass_without_method_leak`.
- Added 1 documentation assertion:
  `test_sprint_1025_documents_runtime_csv_exact_string_guard`.

## Verification

- `pytest tests/test_runtime.py::test_runtime_csv_values_rejects_non_string_without_truthiness_leak tests/test_runtime.py::test_runtime_csv_values_rejects_string_subclass_without_method_leak -q`
  failed before implementation because non-string values raised Python attribute errors and string
  subclasses executed `.split()`.
