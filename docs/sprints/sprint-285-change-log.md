# Sprint 285 Change Log - Anthropic Env Whitespace Fail-Closed

## Summary

- Anthropic provider env parsing now rejects non-empty values with leading or trailing whitespace instead of silently trimming them.
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MAX_TOKENS` all use the same fail-closed whitespace boundary.
- Optional blank `ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MAX_TOKENS` values still behave as absent and use defaults.
- Existing direct provider setting validators for empty, oversized, raw-control, encoded-control, URL shape, and token-budget bounds remain intact.
- Added failing regressions proving malformed Anthropic env values were previously accepted after normalization.
- Documented the Anthropic env whitespace boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_settings_from_env_rejects_leading_or_trailing_whitespace -q` - 4 tests failed before implementation because malformed Anthropic env values were accepted after normalization.
- `python3 -m pytest tests/test_anthropic_provider.py -q` - 62 passed.
- `python3 -m pytest tests/test_anthropic_provider.py tests/test_project_docs.py::test_sprint_two_hundred_eighty_five_documents_anthropic_env_whitespace -q` - 63 passed.
- `python3 -m ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 359 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1742 passed; total coverage 93.95%.
