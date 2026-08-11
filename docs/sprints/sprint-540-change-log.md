# Sprint 540 Change Log

## ServiceNow generic upsert field-name guard

Sprint 540 continued production hardening by tightening generic ServiceNow Table API upserts. `ServiceNowClient.upsert_table_record()` previously validated table names and lookup query parts, but copied create/update body field names directly into POST and PATCH bodies. Unsafe field names could trigger OAuth token acquisition and lookup requests before failing downstream.

Generic upserts now validate every body field name with the shared ServiceNow field identifier guard before lookup, POST construction, PATCH construction, or Table API transport. Unsafe field names fail with the fixed `ServiceNow API field name is unsafe` diagnostic before OAuth token acquisition. The diagnostic does not echo field names, body fragments, lookup values, or credential-like payloads.

This protects bootstrap and infrastructure upsert paths, including REST message, scripted REST operation, business rule, and other ServiceNow configuration records, while preserving existing successful create and update behavior and values.

Verification:

- Added 1 failing-first ServiceNow generic upsert field-name test proving unsafe upsert body field names are rejected before OAuth token acquisition, lookup, POST, or PATCH construction.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_upsert_field_before_lookup_request -q`: failed before implementation because OAuth token acquisition was attempted before upsert body field-name validation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_upsert_field_before_lookup_request tests/test_servicenow.py::test_servicenow_client_upserts_table_record_with_lookup_query tests/test_servicenow.py::test_servicenow_client_upsert_updates_existing_table_record -q`: 3 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 119 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 614 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2528 tests passed with 93.45% coverage.
