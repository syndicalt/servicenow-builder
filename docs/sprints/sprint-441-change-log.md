# Sprint 441 Change Log

## ServiceNow successful result-object shape validation

Hardened ServiceNow single-record response handling so successful `200` responses with malformed `result` object shapes fail as bounded `ServiceNowApiError` diagnostics instead of silently returning `{}`. Prior behavior let create, update, upsert, and attachment paths accept an explicit non-object `result` value and continue as if ServiceNow returned no metadata.

Single-object ServiceNow client methods now use `_required_result_object()`. The validator preserves the existing missing-`result` compatibility behavior by returning `{}`, but rejects any present `result` value that is not an object. Failures use the fixed diagnostic:

- `ServiceNow API response result must be an object`

The diagnostic does not echo the malformed `result` value, credential-like keys, or upstream response fragments.

## Verification

- Added 1 failing-first test covering a successful malformed single-object `result` payload with credential-like values.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_result_object_shape_error"`: failed before implementation because `update_story_fields()` silently returned `{}`.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_result_object_shape_error or success_result_list_shape_error or success_result_record_shape_error or create_story_dictionary_field or update_story_fields or upsert_table_record or attach_story_file"`: 3 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 515 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2310 total tests passed at 93.97% coverage.
