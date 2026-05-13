# Sprint 36 Change Log

## Lifecycle Smoke Runner

- Added `run-lifecycle-smoke` for a dry-run lifecycle test.
- Fetched a ServiceNow story, built an implementation packet, validated a provider response, wrote a candidate artifact, wrote a candidate batch report, and produced a writeback plan.
- Kept writeback in dry-run mode; the command does not mutate ServiceNow.
- Added fail-closed missing-story handling before artifact creation.

## Operator Boundary

- Printed a safe lifecycle summary without tokens, secrets, or ServiceNow sys_id values.
- Preserved the external-build boundary; this smoke test validates orchestration surfaces but does not implement or import Update Sets.
