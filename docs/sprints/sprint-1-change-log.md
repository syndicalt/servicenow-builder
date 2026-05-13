# Sprint 1 Change Log

## Scope

Sprint 1 created the typed schema foundation and provider authorization contract for the regulated MVP.

## Changes

- Core Pydantic schemas in `src/jedi_devproject/models.py`.
- `Story` model with required ServiceNow identifiers, point/priority bounds, data classification, dependencies, and affected-scope fields.
- `ProjectContext` model with non-empty name validation and regulated-environment metadata fields.
- `ProviderPolicy` model for the Provider policy registry contract.
- Provider allow/deny behavior based on approval status, task allowlist, and data-class allowlist.
- `RetrievalCitation` model with confidence bounds.
- `UpdateSetCandidate` model with eligibility decision, reasons, confidence, risk score, citations, assumptions, reviewer notes, changes, and scripts.
- Update Set candidate status transitions through `can_transition_to`.
- `RunManifest` model with non-empty run ID validation.
- Stable artifact hashing through deterministic JSON serialization and SHA-256.
- `pydantic>=2.12` added as a production dependency.

## Assumptions Challenged

- Coverage alone was not accepted as proof of schema quality; additional tests were added for status transitions and fail-closed identifiers.
- Provider authorization is intentionally static in Sprint 1 so later model integrations must pass through a small, testable policy contract.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 22 tests.
- Coverage was 96.41%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
