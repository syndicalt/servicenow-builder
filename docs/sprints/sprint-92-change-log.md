# Sprint 92 Change Log

## Goal

Fix UAT failure handling for `STRY0010001` and make runtime failure state explicit.

## Live UAT Finding

`STRY0010001` failed with `candidate is not ready for Update Set handoff`. The persisted artifacts showed the root cause:

- implementation packet safety decision: `manual_review`
- safety reasons: `missing affected tables`, `story type not allowed: unknown`, `operation allowed: update`
- implementation candidate status: `Manual Build`
- candidate confidence: `0.0`
- candidate risk score: `1.0`

The story is an Incident-form field request. The current automated Update Set handoff supports the allowlisted Story-table dictionary/form pattern, not generalized Incident form placement. The bug was that orchestration attempted a retrieved Update Set handoff even after the deterministic gates correctly produced a `Manual Build` candidate.

## Changes

- Changed model fulfillment post-persist behavior so only `Ready for Review` candidates create retrieved Update Set handoffs.
- Manual-build candidates now write `u_ai_status=Human Review Required` and a work note containing the candidate artifact reference and eligibility reasons.
- Runtime failure notification now discovers the active `Draft` state choice and, when found, updates the failed story with `state=<Draft value>` and `u_ai_status=Automation Failed`.
- Failure work notes still include the lifecycle event id, job id, and redacted error.

## Tests

- Added a regression test for the `STRY0010001` shape proving a `Manual Build` candidate does not call the importer and writes a human-review story note instead.
- Updated runtime failure tests to prove failed jobs fetch `sys_choice`, set `state=-6` for the PDI Draft value, and set `u_ai_status=Automation Failed`.
- Preserved secret-redaction coverage for failure work notes after the extra Draft-state lookup.

## Decision

Unknown or unsupported story shapes should complete as manual-review outcomes, not fail the worker after artifacts are already persisted. Actual execution failures should reset the visible story state out of active build progress.
