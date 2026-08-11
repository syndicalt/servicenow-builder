# Sprint 166 Change Log

## Scope

Production observability and audit correlation hardening. This sprint closes the remaining
operator-traceability gap between artifacts, job event timelines, lifecycle events, and admin
diagnostic views without adding any ServiceNow mutation surface.

## Changes

- Added `get_job()` and `job_events_for_job()` to the runtime store contract used by the API.
- Added `GET /jobs/{job_id}/events` as an admin-only timeline endpoint for ordered
  `job_events`.
- Added source `event_id`, story number, and `correlation_id` to job artifact list responses.
- Added source `event_id` and `correlation_id` to direct artifact blob responses.
- Redacted job event diagnostic messages before returning them from the admin API.
- Updated `docs/operator-guide.md` to document the job timeline and artifact correlation shape.

## Verification

- Focused red/green tests:
  `python3 -m pytest tests/test_runtime.py -k "artifact_read_returns_metadata_and_payload or job_artifacts_lists_only_refs_for_requested_job or job_events_returns_correlation_metadata_and_redacted_messages" -q`
  — 3 passed after implementation.
- Runtime regression:
  `python3 -m pytest tests/test_runtime.py -q`
  — 64 passed.
- Full quality gate:
  `python3 -m ruff check src tests`
  — passed.
- Full type gate:
  `python3 -m mypy src tests`
  — passed.
- Full coverage gate:
  `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  — 1312 passed, 93.82% coverage.

## Notes

- This sprint intentionally keeps the lifecycle event payload as the canonical source for
  `correlation_id`.
- This sprint does not add admin mutation actions, retries, preview, commit, or ServiceNow
  writeback behavior.
- Job event messages are still operational diagnostics, not a safe place to intentionally store
  secrets. Redaction is a defense-in-depth boundary for accidental leaks.
