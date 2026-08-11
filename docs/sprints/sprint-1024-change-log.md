# Sprint 1024 Change Log - Runtime store and audit exact-string guard

## Summary

Hardened required runtime store and audit setting resolution so `DATABASE_URL` and
`JEDI_AUDIT_ROOT` are rejected before URL parsing or path construction when malformed in-process
configuration values are supplied.

## Security

`load_runtime_settings()` now routes `DATABASE_URL` and `JEDI_AUDIT_ROOT` through the shared
exact-string runtime setting reader before `_database_url_value_errors()`, `_audit_root_value_errors()`,
`Path(...)`, or `RuntimeSettings` construction.

String subclasses and non-string objects fail with `<SETTING> must be a string runtime setting`.
This prevents malformed dotenv/config maps from being accepted through `str()` or filesystem path
conversion hooks and keeps database credential fragments out of diagnostics.

## Tests

- Added 1 failing-first database URL scalar assertion:
  `test_load_runtime_settings_rejects_non_string_database_url_without_value_leak`.
- Added 1 failing-first audit root scalar assertion:
  `test_load_runtime_settings_rejects_non_string_audit_root_without_value_leak`.
- Added 1 documentation assertion:
  `test_sprint_1024_documents_runtime_store_and_audit_exact_string_guard`.

## Verification

- `pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_string_database_url_without_value_leak tests/test_runtime.py::test_load_runtime_settings_rejects_non_string_audit_root_without_value_leak -q`
  failed before implementation because malformed store and audit values were accepted after direct
  string/path coercion.
