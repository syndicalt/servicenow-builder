# Sprint 851 Change Log - Runtime redaction literal secret-values guard

## Intent

Harden runtime handler error redaction so malformed `secret_values` cannot crash
exception wrapping or replace the original handler failure with hostile iterator
or non-string secret-entry diagnostics.

## Changes

- Added 2 failing-first runtime redaction secret-values assertions: `tests/test_runtime_redaction.py::test_redacting_handler_ignores_hostile_secret_iterator_without_leaking` and `tests/test_runtime_redaction.py::test_redacting_handler_ignores_non_exact_literal_secret_values`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_851_documents_runtime_redaction_secret_values_guard`.
- Runtime literal `secret_values` are projected to a bounded exact-string set before replacement.
- Hostile iterators such as `_HostileSecretValues` fail closed without surfacing iterator exception text.
- Non-string and string-subclass entries such as `_SecretValueSubclass` are ignored before literal redaction.

## Verification

- `pytest tests/test_runtime_redaction.py::test_redacting_handler_ignores_hostile_secret_iterator_without_leaking tests/test_runtime_redaction.py::test_redacting_handler_ignores_non_exact_literal_secret_values tests/test_project_docs.py::test_sprint_851_documents_runtime_redaction_secret_values_guard -q` - 3 passed.
- `pytest tests/test_project_docs.py -q` - 924 passed.
- `pytest tests/test_runtime_redaction.py tests/test_runtime.py tests/test_runtime_worker_retention.py tests/test_fulfillment_worker.py tests/test_alert_delivery.py tests/test_work_note_safety.py tests/test_servicenow.py -q` - 892 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` - 3398 passed, 93.44% coverage.
