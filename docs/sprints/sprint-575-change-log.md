# Sprint 575 Change Log

## ServiceNow field-name string-subclass guard

Sprint 575 continued production hardening by preventing ServiceNow field-name validation from dispatching string methods on hostile string subclasses. `_servicenow_field_name()` already rejected non-string, padded, delimiter-unsafe, oversized, and malformed field names before OAuth token acquisition or request construction, but it still accepted `str` subclasses and called `strip()` before returning the fixed `ServiceNow API field name is unsafe` diagnostic.

Field-name validation now accepts exact `str` values only. String subclasses fail with the fixed `ServiceNow API field name is unsafe` diagnostic before `strip()`, length checks, regex matching, OAuth token acquisition, PATCH body construction, projection construction, dictionary-field creation, upsert lookup, or transport calls. This preserves normal field-name handling while preventing internal caller wiring, tests, or future adapters from surfacing custom exception text, object representations, or credential-like payloads through field-name string methods.

This keeps `ServiceNowClient.update_story_fields()`, `ServiceNowClient.fetch_table_records(fields=...)`, `ServiceNowClient.upsert_table_record()`, and `ServiceNowClient.create_story_dictionary_field()` fail-closed before constructing request bodies or `sysparm_fields` projections from unsafe field-name objects.

Verification:

- Added 1 failing-first ServiceNow field-name string-subclass test proving a hostile `str` subclass raised `RuntimeError` from overridden `strip()` before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_patch_field_str_subclass_without_methods -q`: failed before implementation because the hostile string subclass raised `RuntimeError` from overridden `strip()` instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_patch_field_str_subclass_without_methods tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_unsafe_story_patch_field_before_request tests/test_servicenow.py::test_servicenow_client_rejects_oversized_table_record_field_before_request tests/test_servicenow.py::test_servicenow_client_fetches_table_records_by_lookup_and_fields tests/test_servicenow.py::test_servicenow_client_updates_story_fields_with_patch_without_secret_leakage -q`: 6 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 177 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 649 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2621 passed, total coverage 93.38%.
