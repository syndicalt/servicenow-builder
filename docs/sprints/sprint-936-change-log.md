# Sprint 936 Change Log - Alert response exact-container diagnostic boundary

## Scope
- Hardened `_redact_alert_response_node()` to traverse only exact dictionaries, lists, and tuples.
- Preserved wide alert sink response truncation coverage using an ordinary dictionary instead of a subclass probe.
- Documented the exact-container boundary for alert sink response diagnostics.

## Production Hardening
- Alert sink response diagnostics now treat container subclasses as malformed diagnostic values.
- Dictionary, list, and tuple subclasses render as `[non-json value]` before `items()`, `len()`, iteration, or subclass hooks can execute.
- Ordinary exact dictionaries, lists, and tuples still retain bounded traversal, cycle handling, depth handling, duplicate-key handling, and truncation markers.

## Tests
- Added `test_alert_response_diagnostic_rejects_container_subclasses`.
- Added `test_sprint_936_documents_alert_response_exact_container_boundary`.
- Captured 1 failing-first alert response diagnostic container-subclass assertion.
- Focused verification: `5 passed`.
- Scoped verification: `tests/test_alert_delivery.py` passed with 80 tests and `tests/test_project_docs.py` passed with 1009 tests.
- Static verification: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage verification: `3585 passed`; total coverage remained 93.57%.
