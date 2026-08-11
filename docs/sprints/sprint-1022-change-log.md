# Sprint 1022 Change Log - Runtime config scalar exact-string guard

## Summary

Hardened runtime boolean, enum, and environment-mode parsing so malformed in-process configuration
values are rejected before truthiness checks or string conversion.

## Security

`_bool_value()`, `_enum_value()`, and `_runtime_environment_value()` now use a shared exact-string
runtime setting reader. Values must be exact strings or `None`; string subclasses and non-string
objects fail with `<SETTING> must be a string runtime setting`.

This prevents malformed runtime configuration maps from executing caller-controlled `__bool__()` or
`__str__()` hooks and prevents misleading enum diagnostics from hiding non-string configuration
objects while production startup settings are loaded.

## Tests

- Added 1 failing-first runtime boolean scalar assertion:
  `test_runtime_config_bool_value_rejects_non_string_without_truthiness_leak`.
- Added 1 failing-first runtime enum scalar assertion:
  `test_runtime_config_enum_value_rejects_string_subclass_without_string_leak`.
- Added 1 failing-first runtime environment scalar assertion:
  `test_runtime_environment_value_rejects_non_string_without_value_leak`.
- Added 1 documentation assertion:
  `test_sprint_1022_documents_runtime_config_scalar_exact_string_guard`.

## Verification

- `pytest tests/test_runtime.py::test_runtime_config_bool_value_rejects_non_string_without_truthiness_leak tests/test_runtime.py::test_runtime_config_enum_value_rejects_string_subclass_without_string_leak tests/test_runtime.py::test_runtime_environment_value_rejects_non_string_without_value_leak -q`
  failed before implementation because malformed runtime setting values executed truthiness or string
  conversion hooks, or were coerced into misleading enum diagnostics.
