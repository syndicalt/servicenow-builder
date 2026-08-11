# Sprint 353 Change Log

## ServiceNow API error diagnostic metadata normalization

Hardened ServiceNow API failure diagnostics so remote response bodies are treated as
untrusted diagnostic input before they are formatted into exceptions. ServiceNow Table API,
Attachment API, OAuth-adjacent client calls, and shared response helpers now use one diagnostic
formatter that recursively applies the shared sensitive-key vocabulary and normalizes whitespace
and control characters inside plain diagnostic strings. In short, it normalizes whitespace and
control characters before ServiceNow error payloads become operator diagnostics.

This keeps upstream ServiceNow, proxy, or load-balancer error strings useful for triage while
preventing newline or tab injection into worker failures, candidate artifacts, ServiceNow work
notes, and operator logs. Structured non-sensitive keys remain visible for debugging, and common
secret-bearing values such as URL passwords, sensitive query parameters, and assignment-style
`api_key=value` or `client_secret=value` fragments are redacted before formatting.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving ServiceNow API errors could
  preserve escaped newline and tab control sequences in raised diagnostics.
- Focused verification: `python3 -m pytest tests/test_servicenow.py -q -k "normalizes_untrusted_error_diagnostics"` passed after implementation.
- ServiceNow regression verification: `python3 -m pytest tests/test_servicenow.py -q` passed with 82 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 427 documentation tests passed, and 2030 total tests passed at 94.05% coverage.
