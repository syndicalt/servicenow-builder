# Threat Model

## Scope

This threat model covers local development and the MVP path through read-only ServiceNow ingestion, rules-first classification, retrieval, candidate generation, review, and export preflight.

## Assets

- ServiceNow OAuth client credentials.
- ServiceNow `rm_story` and related project context.
- Generated `UpdateSetCandidate` artifacts.
- Retrieval citations and prompt/model metadata.
- Reviewer decisions and audit records.

## Primary Threats

- Credential leakage through logs, prompts, artifacts, tests, or committed files.
- Unauthorized use of public model endpoints.
- Generated candidate artifacts that modify unsafe tables or operations.
- Silent mutation of story estimates or review state.
- Cross-domain retrieval leakage between instance metadata and compliance context.
- Live ServiceNow mutation before explicit approval.

## Mitigations

- `.env` is ignored and `.env.example` contains key names only.
- OAuth client credentials are loaded locally and redacted from request summaries.
- Default provider policy enables only rules-only classification.
- Safety gates reject or route risky story types to manual review.
- Export preflight blocks unapproved candidates and keeps XML export disabled by default.
- Tests use fake transports by default; live PDI calls are manual smoke tests only.
