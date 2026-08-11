# Sprint 310 Change Log - Dotenv Value Quote Guard

## Summary

- Local `.env` parsing now rejects unmatched or mixed boundary quotes in assignment values.
- Matching single-quoted and double-quoted values remain supported and have only the matched outer quotes removed.
- Unquoted values still use the existing trimmed value behavior.
- Malformed quote diagnostics use `dotenv_invalid_value_quotes`, name only the assignment key, and do not echo configured secret values.
- Duplicate-key, strict-key, comment, blank-line, non-assignment-line, existing value quote stripping, and 1 MiB bounded-read behavior remain intact.
- This prevents malformed local env files from silently changing ServiceNow credentials, model provider values, or runtime controls by stripping one side of an accidental quote.
- Added failing regressions proving unmatched and mixed quote boundaries were previously accepted during dotenv parsing.
- Documented the dotenv value quote boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 4 tests failed before implementation because unmatched and mixed value quotes were accepted.
- `python3 -m pytest tests/test_servicenow.py -q -k "load_dotenv_values"` - 13 passed after implementation.
- `python3 -m pytest tests/test_servicenow.py -q` - 65 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py` - no issues found in 2 source files.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_three_hundred_ten_documents_dotenv_value_quote_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/servicenow.py tests/test_servicenow.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 384 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1852 passed, total coverage 93.90%.
