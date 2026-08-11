# Sprint 931 Change Log - Alert sink response scalar-subclass diagnostic boundary

## Scope

- Hardened `_redact_alert_response_node()` for alert sink response scalar diagnostics.
- Added a failing-first regression for hostile scalar-subclass response values.
- Documented the exact JSON scalar boundary for alert sink response diagnostics.

## Production Hardening

- Alert sink response diagnostics preserve exact booleans, exact integers, finite floats, exact strings, nulls, arrays, tuples, and dictionaries after the existing redaction and traversal bounds.
- Boolean and integer subclasses render as `[non-json value]` instead of being preserved as ordinary response numbers or booleans.
- Malformed alert sink responses cannot mint operator diagnostics from Python scalar subclasses that differ from plain JSON primitives, and diagnostics do not echo subclass names, credential-like fragments, or hostile string output.

## Tests

- Added `test_alert_response_diagnostic_rejects_scalar_subclass_values`.
- Added `test_sprint_931_documents_alert_sink_response_scalar_subclass_boundary`.
- Captured 1 failing-first alert response diagnostic scalar-subclass assertion.
- Focused sprint tests passed: 2 tests.
- Alert delivery tests passed: 79 tests.
- Project documentation tests passed: 1004 tests.
- Static checks passed: `python3 -m ruff check src tests` and `python3 -m mypy src tests`.
- Full coverage passed: 3572 tests at 93.53% total coverage.
