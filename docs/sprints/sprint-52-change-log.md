# Sprint 52 Change Log

## Attachment Hash Gate

- Carried `artifact_sha256` from the handoff report into `attach-delivery-artifacts` jobs.
- Recomputed each delivery artifact hash before ServiceNow attachment apply.
- Failed closed with `reason=artifact_hash_mismatch` before ServiceNow calls when a reviewed artifact changed after handoff.
- Added the reviewed hash to each uploaded attachment audit entry.
- Documented the attachment audit and hash verification behavior for operators.
