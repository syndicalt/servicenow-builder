# Sprint 1023 Change Log - Split ServiceNow env fallback exact-string guard

## Summary

Hardened split ServiceNow PM/DEV runtime fallback resolution so malformed in-process configuration
values are rejected before truthiness checks, fallback selection, or blank override validation.

## Security

`_env_value()` and `_blank_split_servicenow_override_errors()` now route ServiceNow PM/DEV split
settings through the shared exact-string runtime setting reader. Values must be exact strings or
`None`; string subclasses and non-string objects fail with the fixed diagnostic
`<SETTING> must be a string runtime setting`.

This prevents malformed runtime configuration maps from executing caller-controlled `__bool__()` or
`__str__()` hooks while deciding whether to use split PM/DEV credentials or legacy single-instance
fallback values.

## Tests

- Added 1 failing-first split ServiceNow fallback assertion:
  `test_runtime_env_value_rejects_non_string_primary_without_truthiness_leak`.
- Added 1 failing-first blank split ServiceNow override assertion:
  `test_blank_split_servicenow_overrides_reject_non_string_without_value_leak`.
- Added 1 documentation assertion:
  `test_sprint_1023_documents_split_servicenow_env_fallback_exact_string_guard`.

## Verification

- `pytest tests/test_runtime.py::test_runtime_env_value_rejects_non_string_primary_without_truthiness_leak tests/test_runtime.py::test_blank_split_servicenow_overrides_reject_non_string_without_value_leak -q`
  failed before implementation because `_env_value()` executed truthiness hooks and blank split
  override validation stringified unsupported objects.
