# Sprint 352 Change Log

Scope: Production hardening - OpenAI structured error metadata normalization.

## Summary

- OpenAI provider error diagnostics now treat upstream structured `error.type` and `error.code` values as untrusted diagnostic metadata.
- Structured OpenAI error metadata is redacted with the configured API key before inclusion in provider exceptions.
- Newline, tab, and other whitespace/control runs in structured error metadata are collapsed before diagnostics can reach worker logs, artifacts, or ServiceNow work notes.
- Free-form OpenAI error message redaction, diagnostic bounding, and valid error detail reporting remain unchanged.

## Verification

- `python3 -m pytest tests/test_openai_provider.py::test_openai_responses_provider_redacts_structured_error_metadata -q` - 1 test failed before implementation because raw structured metadata could inject control characters into provider diagnostics.
- `python3 -m pytest tests/test_openai_provider.py -q -k "error or settings"` - 24 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_fifty_two_documents_openai_error_metadata_redaction -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 426 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2028 passed, total coverage 94.08%.
