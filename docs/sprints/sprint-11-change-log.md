# Sprint 11 Change Log

## Scope

Sprint 11 added live PDI pipeline mode while keeping the default test suite offline and deterministic.

## Changes

- Live PDI pipeline mode through `jedi-devproject run-pdi`.
- Module entrypoint support for `python -m jedi_devproject.cli`.
- `ServiceNowClient.fetch_stories` for configurable Table API queries.
- `ServiceNowClient.fetch_ready_stories` retained as a compatibility wrapper.
- Configurable sysparm query through `--sysparm-query`.
- Default `run-pdi` mode fetches bounded stories without a hardcoded `state=Ready` filter.
- `run-pdi` still prints only safe summary counts.

## Live PDI Result

Manual live run:

```bash
PYTHONPATH=src python3 -m jedi_devproject.cli run-pdi --env-file .env --artifact-root artifacts --run-id <timestamped-run-id> --limit 1
```

Observed safe summary:

- `stories_processed=1`
- `eligible=0`
- `manual_review=1`
- `rejected=0`
- `generated_candidates=0`
- `artifact_count=0`

The manual review result is expected: real PDI stories currently do not provide the affected-table metadata required by the safety gate for candidate generation.

## Assumptions Challenged

- `state=Ready` is not portable enough to hardcode for PDI smoke runs.
- A story without affected-table metadata should remain manual review, even if it looks simple.
- Live PDI execution should not print sys_ids, secrets, tokens, or story content.

## Verification Evidence

Latest full gate before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 93 tests.
- Coverage was 96.75%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
