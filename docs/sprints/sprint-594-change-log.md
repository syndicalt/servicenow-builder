# Sprint 594 Change Log

## ServiceNow HTTP error diagnostic cycle safety

Sprint 594 continued production hardening by preventing parsed ServiceNow HTTP error diagnostic traversal from recursing indefinitely on cyclic payloads. `_bound_http_error_diagnostics()` already bounded wide dictionaries, lists, and tuples, projected unsafe keys, normalized unsafe scalar values, and truncated diagnostic text, but a cyclic structure supplied by an alternate transport could still raise `RecursionError` while shaping a transport error response.

Parsed HTTP error diagnostic projection now tracks active container ids while traversing dictionaries, lists, and tuples. If traversal encounters an active container again, it renders `[circular reference]` and continues shaping the diagnostic instead of recursing. The public `_bound_http_error_diagnostics()` helper keeps the same call signature and delegates to the cycle-aware traversal helper internally.

This keeps ServiceNow HTTP transport failure reporting reliable when malformed in-process parsed error bodies contain cycles, and prevents a secondary diagnostic-shaping failure from hiding the original upstream/API failure.

Verification:

- Added 1 failing-first ServiceNow HTTP error diagnostic cycle-safety test proving a self-referential parsed error payload raised `RecursionError` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_handles_circular_payload -q`: failed before implementation with `RecursionError`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_handles_circular_payload tests/test_servicenow.py::test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload tests/test_servicenow.py::test_bound_http_error_diagnostics_rejects_non_json_keys tests/test_servicenow.py::test_bound_http_error_diagnostics_normalizes_non_json_scalar_values -q`: 4 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_594_documents_servicenow_http_error_diagnostic_cycle_safety -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 197 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 668 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2660 passed, 93.19% coverage.
