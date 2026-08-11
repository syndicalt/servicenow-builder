# Sprint 272 Change Log - Anthropic Request ID Diagnostic Sanitization

## Summary

- Anthropic upstream `request-id` headers are now treated as untrusted diagnostic data before being appended to provider errors.
- Request-id diagnostics pass through the shared diagnostic redactor, remove the configured Anthropic API key if it appears, and replace control characters before logs, artifacts, or ServiceNow work notes can receive them.
- Request-id diagnostics are capped separately before the final provider diagnostic cap, preserving useful correlation metadata without allowing an oversized header to dominate the error.
- Added a failing regression proving a newline-bearing, cookie-shaped, secret-bearing Anthropic request id cannot inject log lines or leak the configured API key.
- Documented the Anthropic request-id diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_sanitizes_request_id_diagnostic -q` - 1 test failed before implementation because a malformed upstream request id injected a newline into the provider exception.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_sanitizes_request_id_diagnostic tests/test_anthropic_provider.py -q` - 36 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_two_documents_anthropic_request_id_safety -q` - 37 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 346 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1679 passed; total coverage 93.96%.
