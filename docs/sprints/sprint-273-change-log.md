# Sprint 273 Change Log - Anthropic Stop Reason Diagnostic Sanitization

## Summary

- Anthropic unexpected `stop_reason` values are now treated as untrusted successful-response metadata before being included in provider exceptions.
- Stop-reason diagnostics pass through the shared diagnostic redactor, remove the configured Anthropic API key if it appears, and replace control characters before logs, artifacts, or ServiceNow work notes can receive them.
- Stop-reason diagnostics are capped with the standard `...[truncated]` marker, preventing oversized model metadata from dominating provider errors.
- Added a failing regression proving newline-bearing, secret-bearing, oversized Anthropic `stop_reason` metadata cannot leak the configured API key or inject log lines.
- Documented the Anthropic stop-reason diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_sanitizes_unexpected_stop_reason_diagnostic -q` - 1 test failed before implementation because the unexpected stop reason leaked the configured API key and raw oversized metadata.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_sanitizes_unexpected_stop_reason_diagnostic tests/test_anthropic_provider.py -q` - 37 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_three_documents_anthropic_stop_reason_safety -q` - 38 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 347 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1681 passed; total coverage 93.96%.
