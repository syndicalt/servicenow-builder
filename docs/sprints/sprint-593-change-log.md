# Sprint 593 Change Log

## ServiceNow API diagnostic cycle safety

Sprint 593 continued production hardening by preventing ServiceNow API exception diagnostic traversal from recursing indefinitely on cyclic response payloads. `_servicenow_diagnostic_value()` already bounded wide dictionaries, lists, and tuples, projected unsafe keys, normalized unsafe scalar values, redacted sensitive fields, and capped the final exception diagnostic, but a cyclic structure supplied by an alternate transport could still raise `RecursionError` while formatting `ServiceNowApiError`.

ServiceNow API diagnostic projection now tracks active container ids while traversing dictionaries, lists, and tuples. If traversal encounters an active container again, it renders `[circular reference]` and continues formatting the diagnostic instead of recursing. The public `_servicenow_diagnostic_value()` helper keeps the same call signature and delegates to the cycle-aware traversal helper internally.

This keeps ServiceNow API failure reporting reliable when malformed in-process response bodies contain cycles, and prevents a secondary diagnostic-formatting failure from hiding the original upstream/API failure.

Verification:

- Added 1 failing-first ServiceNow API diagnostic cycle-safety test proving a self-referential response payload raised `RecursionError` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_diagnostic_value_handles_circular_response_payload -q`: failed before implementation with `RecursionError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_diagnostic_value_handles_circular_response_payload tests/test_servicenow.py::test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response tests/test_servicenow.py::test_servicenow_api_failure_rejects_non_json_diagnostic_keys tests/test_servicenow.py::test_servicenow_api_failure_rejects_string_subclass_diagnostic_text -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_593_documents_servicenow_api_diagnostic_cycle_safety -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 196 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 667 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2658 passed, 93.27% coverage.
