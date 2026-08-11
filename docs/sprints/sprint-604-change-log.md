# Sprint 604 Change Log

## Alert delivery text normalization

Sprint 604 continued production hardening by normalizing alert webhook outbound text and alert sink response string diagnostics after redaction and before size caps. Generated alert constructors already redacted and bounded many details, but direct `emit_alert_webhook()` callers could still send raw multiline `summary`, `detail`, or `operator_action` text, and alert sink response string values could still retain newline or tab characters inside `AlertDeliveryError` diagnostics.

Alert serialization now builds a sanitized payload for outbound compact JSON bytes: `summary`, `detail`, and `operator_action` are redacted, whitespace/control-character-normalized, and bounded before transport. Alert sink response string diagnostics use the same normalization before the response diagnostic cap. Non-JSON and non-finite payload checks still run before sanitization, so malformed payload objects fail closed without stringifying unsafe values.

Verification:

- Added 2 failing-first alert delivery tests proving outbound webhook body text and alert sink response diagnostics preserved newline and tab characters before implementation.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_normalizes_alert_body_text_before_send tests/test_alert_delivery.py::test_alert_response_diagnostic_normalizes_string_values -q`: failed before implementation because alert body text and response diagnostics retained raw newline and tab characters.
- `python3 -m pytest tests/test_alert_delivery.py::test_emit_alert_webhook_normalizes_alert_body_text_before_send tests/test_alert_delivery.py::test_alert_response_diagnostic_normalizes_string_values tests/test_alert_delivery.py::test_emit_alert_webhook_failure_bounds_redacted_response_diagnostics tests/test_alert_delivery.py::test_alert_response_diagnostic_redacts_sensitive_response_keys tests/test_alert_delivery.py::test_worker_failure_alert_bounds_generated_detail_after_redaction -q`: 5 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_604_documents_alert_delivery_text_normalization tests/test_project_docs.py::test_sprint_three_hundred_sixty_two_documents_alert_response_bounds -q`: 2 passed.
- `python3 -m pytest tests/test_alert_delivery.py -q`: 67 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 678 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2686 passed, total coverage 93.16%, required 90% coverage reached.
