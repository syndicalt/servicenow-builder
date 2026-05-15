# Sprint 132 Change Log

## Flow Preview/Commit Review Strategy

Sprint 132 added validation-only Flow preview/commit review strategy metadata for the Flow Designer path.

## Changes

- Added `flow_preview_commit_review_strategy`.
- Added `flow-preview-commit-review-strategy-v1`.
- Defined the review boundary as `retrieved_update_set_preview_commit`.
- Required preview before commit.
- Required human commit.
- Rejected auto-commit because Flow Designer auto-commit is not supported.
- Added `preview_commit_review_strategy_version` to Flow builder preflight output.
- Updated ADR 0011, the operator guide, and the production hardening backlog.

## Boundary

There is still no Flow XML builder and no retrieved Update Set handoff for Flow Designer. This sprint only makes the ServiceNow preview/commit review boundary explicit before future builder work starts.

## Verification

- Added positive strategy coverage for required ServiceNow preview/commit review.
- Added negative strategy coverage for auto-commit requests.
- Added negative strategy coverage for missing preview requests.
- Added documentation coverage for the Sprint 132 boundary.
