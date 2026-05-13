# Sprint 0 Change Log

## Scope

Sprint 0 established the engineering baseline and governance controls required before feature development.

## Changes

- Python package baseline under `src/jedi_devproject`.
- CLI smoke behavior for `jedi-devproject --version`.
- Configuration loader that fails closed when required settings are missing.
- `pyproject.toml` project metadata, package discovery, pytest config, coverage config, ruff config, mypy config, and documented local commands.
- 90% coverage gate enforced through pytest-cov and coverage configuration.
- Development guide with the full local verification command.
- Test-first and no-hacks ADR.
- FedRAMP-aligned boundary ADR.
- Local regulated data policy.
- Sprint 0 tests for CLI behavior, config validation, quality-gate configuration, and governance documentation.

## Verification Evidence

Latest full gate run:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Observed result before this change log was added:

- Ruff passed.
- Mypy passed.
- Pytest passed with 9 tests.
- Coverage was 100%, above the 90% gate.

The change log itself is covered by `tests/test_project_docs.py`.
