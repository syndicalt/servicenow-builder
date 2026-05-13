# Sprint 38 Change Log

## Bootstrap Field Apply

- Added `apply-bootstrap-fields` to create missing custom `rm_story` writeback fields.
- Required explicit `--confirm-table rm_story` and `--confirm-fields` flags before mutation.
- Wrote a write-once bootstrap audit artifact for apply attempts.
- Kept scope limited to `u_ai_status`, `u_ai_build_reference`, and `u_ai_candidate_artifact`.

## Product Boundary

- The apply path does not create `state`.
- The apply path makes no form layout changes.
- Story form visibility remains a project team decision.
