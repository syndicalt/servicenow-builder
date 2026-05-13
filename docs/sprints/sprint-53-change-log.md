# Sprint 53 Change Log

## Dry-Run Hash Preflight

- Moved delivery artifact hash verification ahead of the dry-run/apply branch in `attach-delivery-artifacts`.
- Made dry-run attachment planning fail closed with `reason=artifact_hash_mismatch` when a reviewed file has changed.
- Removed the gap where dry-run could report a planned attachment before apply-only validation caught the changed artifact.
- Kept dry-run local and non-mutating; it does not call ServiceNow.
- Updated operator documentation to state that dry-run planning verifies reviewed artifact hashes.
