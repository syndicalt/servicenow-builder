# Sprint 5 Change Log

## Scope

Sprint 5 added a model-provider adapter path without weakening the regulated controls built in earlier sprints.

## Changes

- Provider adapter contract in `src/jedi_devproject/providers.py`.
- `ModelProvider` protocol with a single `generate` boundary.
- Policy enforcement before prompt construction or provider invocation.
- `ProviderBlocked` error for disallowed task or data-class access.
- Minimized story payload containing only story number, short description, and acceptance criteria.
- Model response validation for allowed tables, operations, and known sys_ids.
- `ModelResponseError` for unsafe or malformed model output.
- Tests proving blocked providers receive no payload.

## Assumptions Challenged

- Approved providers are optional execution paths, not architectural dependencies.
- Prompt minimization should be enforced in code and tests before any real model integration exists.
- Model output must be treated as untrusted and validated before candidate construction.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 46 tests.
- Coverage was 96.81%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
