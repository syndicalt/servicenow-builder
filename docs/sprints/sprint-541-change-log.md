# Sprint 541 Change Log

## ServiceNow field-name type guard

Sprint 541 continued production hardening by tightening the shared ServiceNow field-name validator. `_servicenow_field_name()` previously assumed field names were strings and called `.strip()` before type checking, so hostile non-string field keys could raise Python `AttributeError` diagnostics containing object representations before the fixed ServiceNow validation diagnostic was used.

The shared field-name validator now rejects non-string values before any string operations or regex matching. Non-string, padded, delimiter-bearing, control-character, or malformed field names fail with the fixed `ServiceNow API field name is unsafe` diagnostic. The diagnostic does not echo object type names, object string output, field names, body fragments, projection fragments, or credential-like payloads.

This protects every caller that uses the shared field-name guard, including `sysparm_fields` projection construction, story PATCH body fields, generic Table API upsert body fields, and dictionary `element` creation.

Verification:

- Added 1 failing-first ServiceNow non-string field-name test proving hostile PATCH body keys are rejected before OAuth token acquisition or request construction and without calling `str()` or `repr()` for diagnostics.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_patch_field_before_request -q`: failed before implementation because `_servicenow_field_name()` raised `AttributeError` with the hostile object representation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_upsert_field_before_lookup_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_table_record_fields_before_request tests/test_servicenow.py::test_servicenow_client_creates_story_dictionary_field -q`: 5 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 120 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 615 tests passed after documentation updates.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues across 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2530 tests passed with 93.45% coverage.
