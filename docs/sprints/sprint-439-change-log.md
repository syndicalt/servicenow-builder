# Sprint 439 Change Log

## ServiceNow transport successful response parse hardening

Hardened successful ServiceNow HTTP response parsing so invalid UTF-8 and malformed JSON do not escape raw parser exceptions. Prior behavior decoded successful response bodies with `body.decode("utf-8")` and passed the result directly to `json.loads()`, so a bad upstream response could surface `UnicodeDecodeError` or `JSONDecodeError` diagnostics outside the transport boundary.

`UrllibTransport` now parses successful response bodies through `_success_response_body_to_json()`. The parser raises bounded `ServiceNowApiError` diagnostics for invalid UTF-8, malformed JSON, or non-object JSON response bodies without echoing upstream body fragments, credential-like keys, or response values.

HTTP error responses continue to use the existing bounded diagnostic projection path.

## Verification

- Added 2 failing-first transport tests covering successful invalid UTF-8 and malformed JSON response bodies with credential-like fields.
- `python3 -m pytest tests/test_servicenow.py -q -k "invalid_utf8_success_response or malformed_success_json or oversized_success_response"`: failed before implementation because raw `UnicodeDecodeError` and `JSONDecodeError` escaped from `UrllibTransport.send()`.
- `python3 -m pytest tests/test_servicenow.py -q -k "invalid_utf8_success_response or malformed_success_json or oversized_success_response or encodes_query_and_form_body"`: 4 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 513 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2305 total tests passed at 93.96% coverage.
