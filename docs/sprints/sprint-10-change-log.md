# Sprint 10 Change Log

## Scope

Sprint 10 added the end-to-end local pipeline that wires the earlier MVP pieces into a working vertical slice.

## Changes

- End-to-end local pipeline in `src/jedi_devproject/pipeline.py`.
- `PipelineInputs` and `PipelineResult` models.
- Pipeline flow from `Story` list to safety gates, template candidate generation, write-once artifacts, metrics, and summary output.
- `run-local CLI` command in `src/jedi_devproject/cli.py`.
- Sample-file mode for deterministic local runs without live PDI calls.
- Safe summary output that excludes sys_ids, tokens, and secrets.
- ServiceNow client `limit` parameter for bounded read-only Table API calls.
- Missing affected tables route to manual review instead of being treated as eligible.

## Assumptions Challenged

- The first end-to-end pipeline should use sample-file mode before live PDI mode so the vertical slice remains deterministic under test.
- Stories without affected table metadata are not safe to generate candidates for.
- Model integration is still deferred until template-only artifacts can be evaluated.

## Verification Evidence

Latest full gate run before this change log was added:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result:

- Ruff passed.
- Mypy passed.
- Pytest passed with 87 tests.
- Coverage was 97.18%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
