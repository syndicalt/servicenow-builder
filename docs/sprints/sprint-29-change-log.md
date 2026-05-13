# Sprint 29 Change Log

## Implementation Packet CLI

- Added `build-implementation-packet` to create a reviewable implementation packet artifact from local story JSON.
- Added read-only PDI story fetch support by story number for the same packet artifact path.
- Reused deterministic eligibility, risk, provider-policy, allowed-table, allowed-operation, and specialized RAG gates before artifact creation.
- Shaped packet output for the Now Assist provider path while making no model call in this operator command.
- Preserved audit safety by excluding ServiceNow story sys_id values from packet artifacts and CLI output.

## Operational Boundary

- Documented packet review as the next step before real provider invocation.
- Kept model execution separate from artifact generation so packet quality can be inspected independently.
