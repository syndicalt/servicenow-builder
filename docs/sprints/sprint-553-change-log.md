# Sprint 553 Change Log

## ServiceNow story response story-points type guard

Sprint 553 continued production hardening by tightening ServiceNow story response decimal parsing. `_story_from_record()` previously converted the story `story_points` response field with `float(record.get("story_points") or 0)`. A hostile or corrupted alternate transport response could therefore raise Python float-conversion diagnostics containing object type names before the fixed ServiceNow story response diagnostic was used.

Story response story-point parsing now accepts only actual non-boolean finite non-negative integers or floats and simple ASCII decimal strings from ServiceNow. Missing, null, or blank story-point values still map to the operational default `0.0`; non-string objects, booleans, negative values, signed strings, whitespace-padded values, non-ASCII digits, exponent notation, non-finite values, and malformed strings fail with the fixed `ServiceNow API story response field is unsafe` diagnostic before `Story` models are constructed. The diagnostic does not echo object type names, object string output, story-point values, story values, or credential-like payloads.

This protects story ingestion before story-point estimates influence automation eligibility, routing, operational views, work notes, or audit artifacts.

Verification:

- Added 1 failing-first ServiceNow story response story-points test proving a hostile non-numeric story-points value is rejected without stringifying object output or surfacing Python conversion diagnostics, plus malformed-story-points coverage for booleans, negative values, signed strings, whitespace-padded strings, non-ASCII digits, exponent notation, non-finite strings, and malformed decimal strings.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_numeric_story_points_without_stringifying -q`: failed before implementation because `_story_from_record()` called `float()` on the hostile object.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_non_numeric_story_points_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_malformed_story_points_values tests/test_servicenow.py::test_servicenow_client_maps_decimal_story_points_to_validated_stories tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults tests/test_servicenow.py::test_servicenow_client_maps_records_to_validated_stories -q`: 14 tests passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 154 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 627 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success with no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2576 tests passed; required 90% coverage reached with 93.41% total coverage.
