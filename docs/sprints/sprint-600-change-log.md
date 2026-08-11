# Sprint 600 Change Log

## ServiceNow diagnostic truncation marker collision safety

Sprint 600 continued production hardening by preventing internal ServiceNow diagnostic truncation markers from overwriting user-provided diagnostic keys. Parsed HTTP error diagnostics, ServiceNow API exception diagnostics, and secret-redacted request/response diagnostic copies all inserted `__jedi_response_truncated__` directly after sampling wide dictionaries. If a sampled upstream payload already contained that key, the internal marker replaced the user diagnostic value.

Dictionary truncation metadata now uses a shared `_add_servicenow_truncation_marker()` helper. The helper routes the internal marker through `_unique_servicenow_diagnostic_key()`, preserving any user-provided `__jedi_response_truncated__` value and placing the internal metadata at a deterministic duplicate key such as `__jedi_response_truncated__ (2)`.

This improves auditability for wide malformed payloads: internal truncation metadata remains visible without silently deleting caller-supplied diagnostic content.

Verification:

- Added 3 failing-first ServiceNow truncation marker collision tests proving parsed HTTP error diagnostics, ServiceNow API diagnostics, and secret-redacted diagnostic copies overwrote a sampled user `__jedi_response_truncated__` value before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_preserves_user_truncation_marker_key tests/test_servicenow.py::test_servicenow_diagnostic_value_preserves_user_truncation_marker_key tests/test_servicenow.py::test_redact_secrets_preserves_user_truncation_marker_key -q`: failed before implementation because the internal truncation marker overwrote `user marker`.
- `python3 -m pytest tests/test_servicenow.py::test_bound_http_error_diagnostics_preserves_user_truncation_marker_key tests/test_servicenow.py::test_servicenow_diagnostic_value_preserves_user_truncation_marker_key tests/test_servicenow.py::test_redact_secrets_preserves_user_truncation_marker_key tests/test_servicenow.py::test_bound_http_error_diagnostics_does_not_consume_all_fields_for_wide_payload tests/test_servicenow.py::test_servicenow_diagnostic_value_does_not_consume_all_fields_for_wide_response tests/test_servicenow.py::test_redact_secrets_does_not_consume_all_fields_for_wide_diagnostic tests/test_servicenow.py::test_bound_http_error_diagnostics_keeps_duplicate_keys_inside_cap tests/test_servicenow.py::test_servicenow_diagnostic_value_keeps_duplicate_keys_inside_cap -q`: 8 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_600_documents_servicenow_diagnostic_truncation_marker_collision_safety -q`: 1 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 206 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 674 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2675 passed, 93.16% coverage.
