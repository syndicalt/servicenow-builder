# Sprint 311 Change Log - Dotenv Key Syntax Guard

## Summary

- Local `.env` parsing now rejects assignment keys that are not shell-compatible uppercase environment variable names.
- Assignment keys must start with a letter or underscore and contain only uppercase letters, digits, and underscores.
- Lowercase, hyphenated, dotted, digit-prefixed, padded, empty, whitespace, and control-character keys all fail with the fixed `dotenv_invalid_key` diagnostic.
- Duplicate-key, value-quote, comment, blank-line, non-assignment-line, and 1 MiB bounded-read behavior remain intact.
- This prevents local env files from silently accepting typo-prone or shell-incompatible config keys that would not behave like real deployment environment variables.
- Added failing regressions proving lowercase, hyphenated, dotted, and digit-prefixed assignment keys were previously accepted during dotenv parsing.
- Documented the dotenv key syntax boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 4 tests failed before implementation because unsupported key shapes were accepted.
- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 17 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py -q` - 69 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_eleven_documents_dotenv_key_syntax_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 385 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1857 passed, total coverage 93.90%.
