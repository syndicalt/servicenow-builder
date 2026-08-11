# Sprint 351 Change Log

Scope: Production hardening - Anthropic retry-after response normalization.

## Summary

- Anthropic retry delay parsing no longer strips upstream `retry-after` response header values.
- Padded, whitespace-bearing, control-character-bearing, negative, non-numeric, and non-finite `retry-after` values are ignored instead of controlling worker sleep.
- Safe finite non-negative retry values still honor the provider retry hint up to the existing 30-second cap.
- Malformed retry metadata now falls back to deterministic exponential backoff.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_ignores_malformed_retry_after_header -q` - 3 tests failed before implementation because padded and non-finite retry headers influenced worker sleep.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "retry_after or backs_off_exponentially"` - 6 passed after implementation.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_fifty_one_documents_anthropic_retry_after_no_trim -q` - 1 passed.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 187 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 425 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 2026 passed, total coverage 94.08%.
