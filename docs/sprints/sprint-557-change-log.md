# Sprint 557 Change Log

## ServiceNow field-name length guard

Sprint 557 continued production hardening by bounding the shared ServiceNow field-name guard. `_servicenow_field_name()` already rejected non-string, padded, delimiter-unsafe, and regex-unsafe field identifiers before projection or body construction, but it did not cap otherwise valid identifier-shaped values. An oversized field name made only of allowed characters could therefore reach OAuth acquisition and request construction as an unbounded `sysparm_fields` projection or body key.

Field-name validation now rejects values longer than 256 characters before OAuth token acquisition, request construction, field projection assembly, or PATCH/upsert body construction. Oversized field names fail with the fixed `ServiceNow API field name is unsafe` diagnostic. The diagnostic does not echo field names, body fragments, projection fragments, lookup values, or credential-like payloads.

This shared guard covers Table API field projections, story PATCH body fields, generic Table API upsert fields, and dictionary element names before ServiceNow requests can be constructed.

Verification:

- Added 1 failing-first ServiceNow field-name length test proving a 257-character field name is rejected before OAuth acquisition or request construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_field_before_request -q`: failed before implementation because the oversized field name reached OAuth token acquisition.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_record_fields_before_request tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_upsert_field_before_lookup_request tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 159 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 631 passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2585 passed, 93.41% total coverage.
