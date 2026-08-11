# Sprint 552 Change Log

## ServiceNow story response priority type guard

Sprint 552 continued production hardening by tightening ServiceNow story response integer parsing. `_story_from_record()` previously converted the story `priority` response field with `int(record.get("priority") or 5)`. A hostile or corrupted alternate transport response could therefore raise Python integer-conversion diagnostics containing object type names before the fixed ServiceNow story response diagnostic was used.

Story response priority parsing now accepts only actual non-boolean integers and simple ASCII decimal strings from ServiceNow. Missing, null, or blank priority values still map to the operational default `5`; non-string objects, booleans, signed values, whitespace-padded values, non-ASCII digits, and malformed strings fail with the fixed `ServiceNow API story response field is unsafe` diagnostic before `Story` models are constructed. The diagnostic does not echo object type names, object string output, priority values, story values, or credential-like payloads.

This protects story ingestion before priority values influence automation routing, operational views, work notes, or audit artifacts.

Verification:

- Added 1 failing-first ServiceNow story response priority test proving a hostile non-integer story priority is rejected without stringifying object output or surfacing Python conversion diagnostics, plus malformed-priority coverage for booleans, signed strings, whitespace-padded strings, non-ASCII digits, and decimal strings.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_story_priority_without_stringifying -q`: failed before implementation because `_story_from_record()` called `int()` on the hostile object.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_integer_story_priority_without_stringifying tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults tests/test_servicenow.py::test_servicenow_client_maps_records_to_validated_stories tests/test_servicenow.py::test_servicenow_client_rejects_non_string_story_response_text_without_stringifying -q`: 4 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 142 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 626 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2563 tests passed; required 90% coverage reached with 93.42% total coverage.
