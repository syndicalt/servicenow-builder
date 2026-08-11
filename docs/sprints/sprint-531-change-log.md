# Sprint 531 Change Log

## ServiceNow sysparm_fields projection guard

Sprint 531 continued production hardening by tightening `ServiceNowClient.fetch_table_records(fields=...)`. The method joins requested fields into the Table API `sysparm_fields` projection parameter. Previously each field value was accepted raw, so a malformed field containing comma separators, encoded-query delimiters, controls, or credential-like fragments could alter the projection string after OAuth token acquisition started.

Requested fields are now validated before `sysparm_fields` construction. Field names must be unpadded ServiceNow identifiers and may include dotted reference paths made of identifier parts. Unsafe field names fail with the fixed `ServiceNow API field name is unsafe` diagnostic before OAuth token acquisition, GET construction, or Table API transport. The diagnostic does not echo field values, projection fragments, or credential-like payloads.

This preserves explicit encoded-query behavior where the caller intentionally supplies `fetch_stories(sysparm_query=...)`, while the typed `fields=` projection path now fails closed.

Verification:

- Added 1 failing-first ServiceNow `sysparm_fields` projection test proving unsafe field delimiters are rejected before OAuth token acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_record_fields_before_request -q`: failed before implementation because OAuth token acquisition was attempted before field-name validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_record_fields_before_request tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 2 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 109 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 605 documentation tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2509 tests passed with 93.44% coverage.
