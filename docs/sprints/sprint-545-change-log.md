# Sprint 545 Change Log

## ServiceNow sysparm_limit type guard

Sprint 545 continued production hardening by tightening ServiceNow Table API result-limit construction. Sprint 532 bounded `sysparm_limit` values to the supported range, but `_servicenow_result_limit()` still compared caller-provided values before proving they were integers. Hostile non-integer limit objects could therefore raise Python `TypeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

Result-limit construction now accepts only real integers before range comparison. Non-integer, boolean, non-positive, or oversized values fail with the fixed `ServiceNow API result limit is unsafe` diagnostic before OAuth token acquisition, GET construction, or Table API transport. The diagnostic does not echo object type names, object string output, query values, lookup values, or credential-like payloads.

This protects every caller that builds `sysparm_limit` through `ServiceNowClient.fetch_stories()` and `ServiceNowClient.fetch_table_records()`.

Verification:

- Added 1 failing-first ServiceNow result-limit type test proving a hostile non-integer story limit is rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_story_limit_before_request -q`: failed before implementation because `_servicenow_result_limit()` raised `TypeError` with a hostile object representation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_story_limit_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_positive_story_limit_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_limit_before_request tests/test_servicenow.py::test_servicenow_client_fetch_stories_allows_explicit_query tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 5 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 125 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 619 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2539 tests passed with 93.46% coverage.
