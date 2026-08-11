# Sprint 863 Change Log

## ServiceNow field-list truthiness guard

- Added 1 failing-first ServiceNow field-list truthiness assertion covering hostile `fields` list subclasses: `test_servicenow_client_rejects_table_record_fields_before_truthiness`.
- `ServiceNowClient.fetch_table_records(fields=...)` now validates provided field lists before truthiness branching.
- `None` still omits `sysparm_fields`; any provided field list must pass the exact-list guard before the method includes the projection parameter.

## Verification

- `pytest tests/test_servicenow.py::test_servicenow_client_rejects_table_record_fields_before_truthiness tests/test_project_docs.py::test_sprint_863_documents_servicenow_field_list_truthiness_guard -q` -> 2 passed.
- `pytest tests/test_servicenow.py -q` -> 291 passed.
- `pytest tests/test_project_docs.py -q` -> 936 passed.
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q` -> 3423 passed, total coverage 93.48%.
