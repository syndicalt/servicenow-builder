# Sprint 274 Change Log - Anthropic Retry Count Bound

## Summary

- Anthropic provider retry configuration is now bounded at construction time.
- `AnthropicMessagesProvider` rejects negative retry counts and retry counts above five before any request can be sent.
- The default retry behavior and existing `retry-after` handling remain intact, including the 30-second provider backoff cap.
- Added a failing regression proving an unbounded `max_retries=6` value is rejected instead of accepted.
- Documented the Anthropic retry bound in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_rejects_unbounded_max_retries -q` - 1 test failed before implementation because `max_retries=6` was accepted.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_rejects_unbounded_max_retries tests/test_anthropic_provider.py -q` - 38 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_seventy_four_documents_anthropic_retry_count_bound -q` - 39 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 175 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 348 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1683 passed; total coverage 93.96%.
