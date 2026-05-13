# Sprint 44 Change Log

## Handoff Evidence Hashing

- Added SHA-256 hashes to each artifact decision in the handoff report.
- Made handoff report generation read every referenced artifact before writing the report.
- missing artifact paths now fail closed instead of producing path-only evidence.

## Product Boundary

- The handoff report remains a planning artifact.
- Hashing proves which evidence file the handoff decision evaluated.
- The command still does not attach files to ServiceNow.
