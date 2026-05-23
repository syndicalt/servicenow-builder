# Data Flow

The canonical architecture and diagram set is `docs/system-architecture.md`. This file keeps the security-focused data-flow summary.

## Local Development Flow

1. Developer stores PDI connection settings in local `.env`.
2. `OAuthClientCredentials` requests a token from the PDI.
3. `ServiceNowClient` makes read-only Table API requests for `rm_story`.
4. Records are mapped into validated `Story` models.
5. Rules-first safety gates classify stories as eligible, manual review, or rejected.
6. Specialized local RAG interfaces provide citations.
7. Template-only generation creates `UpdateSetCandidate` JSON.
8. Review workflow records approval or rejection.
9. Export preflight blocks export unless candidate status and feature flags allow it.

## Default Test Flow

Default tests do not call the PDI. Tests use fake transports and synthetic records.

## Prohibited Flow

No data may flow to a public model endpoint unless an approved Federal authorization path, provider policy, data-class allowance, and task allowance exist.
