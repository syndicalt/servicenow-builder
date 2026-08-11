# Sprint 354 Change Log

## ServiceNow API final diagnostic size cap

Hardened ServiceNow API failure diagnostics with a final post-redaction size cap. Sprint 353 made
ServiceNow API diagnostics recursively redacted and whitespace/control-character-normalized; this
sprint adds a last line of defense at exception formatting time so alternate transports, tests,
future HTTP clients, or direct `HttpResponse` values cannot create oversized worker failures,
candidate artifacts, ServiceNow work notes, or operator logs.

The final formatter now redacts the structured response body, normalizes untrusted diagnostic
strings, formats the diagnostic representation, and truncates it with the existing ServiceNow
HTTP diagnostic truncation marker. This keeps status code and useful structured context available
while preventing remote error payloads from becoming unbounded diagnostic strings.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving a mocked ServiceNow error
  payload larger than the diagnostic limit could create an unbounded exception string.
- Focused verification: `python3 -m pytest tests/test_servicenow.py -q -k "bounds_final_error_diagnostic or normalizes_untrusted_error_diagnostics"` passed with 2 tests after implementation.
- ServiceNow regression verification: `python3 -m pytest tests/test_servicenow.py -q` passed with 83 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 428 documentation tests passed, and 2032 total tests passed at 94.05% coverage.
