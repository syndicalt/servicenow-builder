# Sprint 80 Change Log

## Goal

Make hosted OpenAI provider failures diagnosable without exposing secrets or mutating the ServiceNow story repeatedly.

## Changes

- Updated `UrllibTransport` to return structured `HttpResponse` objects for HTTP error responses instead of letting `urllib` raise generic `HTTPError` exceptions.
- Preserved JSON error bodies from upstream providers, including OpenAI 429 responses.
- Added a non-JSON HTTP error fallback shape so callers still receive a consistent `{"error": {"message": ...}}` payload.
- Updated OpenAI provider failures to include sanitized provider diagnostics: HTTP status, message, error type, and error code.

## Verification

- Added regression coverage for JSON and non-JSON HTTP error bodies at the transport boundary.
- Added OpenAI provider coverage for rate-limit/quota diagnostic messages.
- Ran the full local quality gate:
  - `ruff check .`
  - `mypy src tests`
  - `pytest --cov=jedi_devproject --cov-fail-under=90`

Result: 409 tests passed with 92.07% coverage.

## Architecture Notes

The root issue was not the new Railway key itself; it was that the runtime could not see the provider's error payload. A production orchestration worker needs typed boundary behavior for failed HTTP responses so failures can be audited and written back cleanly. This sprint keeps the OpenAI provider fail-closed while making account, project, quota, and model-access failures distinguishable.
