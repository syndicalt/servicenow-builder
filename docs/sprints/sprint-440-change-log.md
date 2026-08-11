# Sprint 440 Change Log

## ServiceNow successful result-list shape validation

Hardened ServiceNow table/list response handling so successful `200` responses with malformed `result` shapes fail as bounded `ServiceNowApiError` diagnostics instead of raw Python exceptions or silent drops. Prior behavior let methods such as `fetch_ready_stories()` iterate whatever `response.json_body.get("result", [])` returned; a string result or list containing non-object entries could escape as `TypeError` while parsing records.

List-style ServiceNow client methods now use `_required_result_record_list()`. The validator requires `result` to be a list and every entry to be an object. Failures use fixed diagnostics:

- `ServiceNow API response result must be a list`
- `ServiceNow API response result entries must be objects`

The diagnostics do not echo the malformed `result` value, credential-like keys, or upstream response fragments.

## Verification

- Added 2 failing-first tests covering successful malformed `result` payloads with credential-like values.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_result_list_shape_error or success_result_record_shape_error"`: failed before implementation because raw `TypeError` escaped from story parsing.
- `python3 -m pytest tests/test_servicenow.py -q -k "success_result_list_shape_error or success_result_record_shape_error or builds_read_only_story_query or fetches_story_state_choices or fetches_dictionary_fields or fetch_table_record or fetch_table_records"`: 5 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 514 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2308 total tests passed at 93.97% coverage.
