# Sprint 271 Change Log - Anthropic Provider Diagnostic Redaction Bounds

## Summary

- Anthropic provider API error diagnostics now redact free-form upstream message text with the shared diagnostic redactor.
- The configured Anthropic API key is removed from provider error messages if an upstream response echoes it.
- Anthropic free-form API error message text is capped before structured metadata is appended, so `type` and `request_id` remain visible for operator triage.
- Anthropic provider diagnostic messages are capped at 4096 characters with the standard `...[truncated]` marker.
- Added a failing regression proving secret-bearing oversized Anthropic error details are redacted and bounded.
- Documented the Anthropic provider diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_redacts_and_bounds_error_details -q` - 1 test failed before implementation because the provider returned secret-bearing oversized error details.
- `python3 -m pytest tests/test_anthropic_provider.py -q` - 35 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_one_documents_anthropic_diagnostic_bounds -q` - 36 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 345 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1677 passed; total coverage 93.97%.
