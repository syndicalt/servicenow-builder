# Sprint 457 Change Log

## ServiceNow outbound JSON non-finite number rejection

Hardened the urllib ServiceNow transport so outbound `application/json` request bodies cannot
serialize Python non-finite floats into invalid JSON tokens such as `NaN`, `Infinity`, or `-Infinity`.
The transport now uses strict JSON encoding for ServiceNow JSON bodies and fails closed with a stable
`ServiceNowApiError` before any network request is opened.

The rejection diagnostic is intentionally non-reflective: it does not echo request field names,
body values, URL fragments, or credential-like payload strings. Form-encoded requests and binary
attachment uploads continue to use their existing encoding paths.

## Verification

- Added 1 failing-first ServiceNow urllib transport test proving a non-finite JSON body is rejected
  before opener construction and without reflecting a body secret.
- `python3 -m pytest tests/test_servicenow.py -q -k "non_finite_json_request_body"`: failed
  before implementation because the transport reached opener construction with malformed JSON.
- `python3 -m pytest tests/test_servicenow.py -q -k "non_finite_json_request_body or encodes_query_and_form_body or handles_request_without_params_or_body or uploads_story_attachment_with_binary_body"`:
  4 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 531 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2352 total tests passed at 93.81% coverage.
