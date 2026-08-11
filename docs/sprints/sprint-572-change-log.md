# Sprint 572 Change Log

## ServiceNow story response story-points numeric-subclass guard

Sprint 572 continued production hardening by preventing ServiceNow story response story-point parsing from dispatching comparisons on hostile numeric subclasses. `_servicenow_story_response_float()` already rejected non-numeric objects, booleans, negative values, signed strings, whitespace-padded strings, non-ASCII digits, exponent notation, non-finite values, and malformed decimal strings before `Story` models were constructed, but it still accepted `int` and `float` subclasses and compared them against the non-negative boundary.

Story response story-point parsing now accepts exact `int` values, exact `float` values, and exact `str` decimal values only. Numeric subclasses fail with the fixed `ServiceNow API story response field is unsafe` diagnostic before finite checks, range comparisons, `Story` validation, automation routing, operational views, artifact persistence, or failure-writeback decisions. This preserves normal JSON integer and float handling while preventing alternate transports from surfacing custom exception text, object representations, or credential-like payloads through story-point comparisons.

This keeps ServiceNow story ingestion fail-closed when a test transport, mock transport, or future response adapter returns a hostile numeric subclass for the story `story_points` field.

Verification:

- Added 1 failing-first ServiceNow story response story-points float-subclass test proving a hostile `float` subclass could execute comparison methods and raise credential-bearing exception text before implementation.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_points_float_subclass_without_comparing -q`: failed before implementation because the hostile float subclass raised `RuntimeError` during comparison instead of `ServiceNowApiError`.
- `python3 -m pytest tests/test_servicenow.py::test_servicenow_client_rejects_story_points_float_subclass_without_comparing tests/test_servicenow.py::test_servicenow_client_rejects_non_numeric_story_points_without_stringifying tests/test_servicenow.py::test_servicenow_client_rejects_malformed_story_points_values tests/test_servicenow.py::test_servicenow_client_maps_decimal_story_points_to_validated_stories tests/test_servicenow.py::test_servicenow_client_maps_missing_optional_record_values_to_safe_defaults tests/test_servicenow.py::test_servicenow_client_maps_records_to_validated_stories -q`: 15 passed.
- `python3 -m pytest tests/test_servicenow.py -q`: 174 passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 646 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 196 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2615 passed, total coverage 93.38%.
