# Sprint 75 Change Log

## Goal

Prepare the safe container lifecycle smoke from ServiceNow-style `Draft` to `Ready` event intake through worker build-claim dry-run.

## Changes

- Added `jedi_devproject.container_smoke`.
- Added `plan_container_lifecycle_smoke()` to produce the ordered local smoke steps.
- Added a deterministic `Draft` to `Ready` event payload for a selected story number.
- Required apply disabled for the smoke plan.
- Added a secret-safe smoke summary.
- Packaged the reviewed PostgreSQL migration inside the Python wheel so containerized runtime startup does not depend on repository-relative paths.
- Installed the runtime PostgreSQL client library in the container image for psycopg.
- Enabled autocommit on runtime PostgreSQL connections while preserving explicit write transactions, preventing read operations from leaving hidden uncommitted request state.

## Verification

- Added tests for the smoke sequence, event payload, secret-safe summary, and fail-closed apply-enabled behavior.
- Added a packaging regression test that the wheel migration matches the reviewed SQL migration.
- Added a connection regression test that runtime PostgreSQL connections use autocommit for request-safe reads.
- Documented the manual container smoke in the operator guide.
- Ran the full quality gate: `ruff`, `mypy`, and `pytest --cov` passed with 380 tests and 92.64% coverage.
- Ran the local container lifecycle smoke with `JEDI_BUILD_CLAIM_APPLY=false`.
- Verified the API health endpoint, accepted the synthetic `Draft` to `Ready` event, and confirmed the event and queued fulfillment job were visible from a separate PostgreSQL session.
- Ran one worker pass. The worker claimed the job and failed closed with `fresh_story_state_mismatch` because the live PDI story state no longer matched the synthetic event.

## Architecture Notes

The smoke starts the containerized API and PostgreSQL services, posts a lifecycle event, and runs one worker pass. The worker should execute the build-claim path with apply disabled so ServiceNow is not mutated during local runtime verification.

Synthetic lifecycle events are useful for local runtime checks, but a full fulfillment smoke must use a live ServiceNow story transition. The worker correctly refuses to build from stale lifecycle context when the fetched story state disagrees with the event that created the job.
