# Sprint 270 Change Log - OpenAI Provider Diagnostic Redaction Bounds

## Summary

- OpenAI provider API error diagnostics now redact free-form upstream message text with the shared diagnostic redactor.
- The configured OpenAI API key is removed from provider error messages if an upstream response echoes it.
- OpenAI provider diagnostic messages are capped at 4096 characters with the standard `...[truncated]` marker.
- Structured OpenAI error `type` and `code` fields remain visible so operators can distinguish quota, model access, project, and service failures without exposing free-form secrets.
- Added a failing regression proving secret-bearing oversized OpenAI error details are redacted and bounded.
- Documented the OpenAI provider diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_redacts_and_bounds_error_details -q` - 1 test failed before implementation because the provider returned secret-bearing oversized error details.
- `python3 -m pytest tests/test_openai_provider.py -q` - 7 passed.
- `python3 -m pytest tests/test_openai_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_documents_openai_diagnostic_bounds -q` - 8 passed.
- `python3 -m ruff check src/jedi_devproject/openai_provider.py tests/test_openai_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/openai_provider.py tests/test_openai_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 344 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1675 passed; total coverage 94.00%.
