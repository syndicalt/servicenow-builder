# Sprint 62 Change Log

## Build Claim Execution

- Added `BuildClaimExecutionRequest` for applying a story claim from `Ready` to `Work in Progress`.
- Added `execute_build_claim()` as the application boundary for automated build-claim writeback.
- Required a fresh story read before mutation and failed closed with `fresh_story_state_mismatch` when the story is no longer in the expected source state.
- Added a dedicated build claim audit artifact instead of reusing external build completion audit records.
- Required actor identity, confirmation, and audit root before live apply.
- Made claim retries idempotent with `build_claim_already_recorded`.

## Verification

- Added dry-run execution tests that prove no mutation and no audit write occur.
- Added apply tests that verify `state=Work in Progress`, `u_ai_status=Build In Progress`, work notes, and build claim audit output.
- Added stale-story tests that prove the claim fails closed before ServiceNow update calls.
