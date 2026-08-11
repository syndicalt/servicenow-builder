# Sprint 191 Change Log

Scope: Production hardening - sanitized ServiceNow request URL redaction.

## Changes

- Updated `HttpRequest.sanitized()` to redact the diagnostic copy of the request `url`.
- Covered URL passwords and sensitive query parameters embedded directly in the `url` field.
- Preserved non-sensitive query parameters in sanitized URLs so operator diagnostics remain useful.
- Kept the original request URL unchanged for transport behavior.
- Documented sanitized request URL redaction in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py::test_http_request_sanitized_redacts_url_credentials_and_sensitive_query tests/test_servicenow.py::test_http_request_sanitized_redacts_body_bytes_without_mutating_original tests/test_servicenow.py::test_servicenow_client_builds_read_only_story_query_without_credentials -q` - 3 passed.
- `python3 -m ruff check src tests` - passed.
- `python3 -m pytest tests/test_project_docs.py -q` - 265 passed.
- `python3 -m mypy src tests` - passed; 172 source files checked.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1404 passed, 93.91% coverage.
