# Sprint 309 Change Log - Dotenv Key Ambiguity Guard

## Summary

- Local `.env` parsing now rejects duplicate assignment keys instead of silently using the last value.
- Local `.env` assignment keys must be non-empty, unpadded, and free of whitespace or control characters.
- Comments, blank lines, non-assignment lines, existing value quote stripping, and the 1 MiB bounded-read guard remain intact.
- Duplicate-key diagnostics name only the assignment key and do not echo secret values.
- Malformed-key diagnostics use the fixed `dotenv_invalid_key` error and do not echo malformed key text or configured values.
- This prevents ambiguous local env files from hiding which ServiceNow target, credential, model provider, or runtime control value was actually loaded.
- Added failing regressions proving duplicate keys and malformed key names were previously normalized or overwritten during dotenv parsing.
- Documented the dotenv key-shape and duplicate-key boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 5 tests failed before implementation because duplicate keys and malformed key names were accepted.
- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 8 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py -q` - 60 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_nine_documents_dotenv_key_ambiguity_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 383 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1846 passed, total coverage 93.89%.
