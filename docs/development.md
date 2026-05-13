# Development Guide

## Baseline

This project is built test-first. Production code must not be added until a failing test demonstrates the intended behavior.

## Local Verification

Run the full local quality gate before treating any sprint task as complete:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

The same commands are recorded in `pyproject.toml` under `tool.jedi-devproject.commands`:

- `python3 -m ruff check src tests`
- `python3 -m mypy src tests`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90`

## Engineering Rules

- Write the failing test first.
- Keep modules small and typed.
- Maintain at least 90% coverage.
- Prefer re-engineering over hacks or hidden bypasses.
- Document assumptions in the sprint plan or an ADR.
- Never put secrets, credentials, tokens, or regulated customer data into tests, prompts, artifacts, or logs.
