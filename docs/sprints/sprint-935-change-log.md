# Sprint 935 Change Log - ServiceNow diagnostic exact-container boundary

## Scope
- Hardened `_bound_http_error_diagnostics()` to traverse only exact dictionaries, lists, and tuples.
- Hardened `_servicenow_diagnostic_value()` to traverse only exact dictionaries, lists, and tuples.
- Hardened `redact_secrets()` to traverse only exact dictionaries, lists, and tuples.
- Preserved wide-payload truncation coverage using ordinary dictionaries instead of subclass probes.

## Production Hardening
- ServiceNow HTTP error diagnostics, API diagnostics, and diagnostic secret redaction now treat container subclasses as malformed diagnostic values.
- Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.
- Ordinary exact dictionaries, lists, and tuples still retain bounded traversal, cycle handling, duplicate-key handling, and truncation markers.

## Tests
- Added `test_bound_http_error_diagnostics_rejects_dict_subclass_payloads`.
- Added `test_servicenow_diagnostic_value_rejects_dict_subclass_payloads`.
- Added `test_redact_secrets_rejects_dict_subclass_payloads`.
- Added `test_sprint_935_documents_servicenow_diagnostic_exact_container_boundary`.
- Captured 3 failing-first ServiceNow diagnostic container-subclass assertions.
- Focused verification: `7 passed`.
- Scoped verification: `tests/test_servicenow.py` passed with 307 tests and `tests/test_project_docs.py` passed with 1008 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3583 passed`; total coverage increased to 93.57%.
