# Development Guide

This guide covers local setup, the quality gate, and contribution conventions for
JEDI DevProject, the FedRAMP-aligned, AI-assisted ServiceNow sidecar runtime. For the
runtime architecture and data flows, see `docs/system-architecture.md`. For operating
the deployed runtime, see `docs/operator-guide.md`. For test strategy and test-writing
conventions, see `docs/testing.md`.

## Baseline

This project is built test-first. Production code must not be added until a failing
test demonstrates the intended behavior (ADR 0001). The system is dry-run by default
and fails closed on every safety path; keep that posture intact in every change.

## Repository Layout

| Path | Contents |
|---|---|
| `src/jedi_devproject/` | Application package: pipeline, capabilities, providers, ServiceNow client, runtime API/worker, operational store |
| `src/jedi_devproject/migrations/` | Numbered raw SQL migrations (`NNNN_name.sql`) applied by `connect_operational_store`; shipped as package data |
| `src/jedi_devproject/discovery/` | ServiceNow surface discovery subpackage (context bundles, catalog, CMDB, flows) |
| `tests/` | Flat pytest suite, one `test_<module>.py` per source module; no `conftest.py` |
| `docs/` | Architecture, operator guide, ADRs (`adr/`), policies (`policies/`), sprint change logs (`sprints/`), release notes (`releases/`), security docs (`security/`) |
| `db/migrations/` | Deployment-facing copy of the operational store migrations |
| `deploy/railway/` | Hosted deployment manifests |
| `examples/` | Example story payloads used by the example-validation tests |
| `artifacts/` | Local run output (audit evidence, handoff reports); not source |
| `pyproject.toml` | Build metadata, dependencies, tool configuration (ruff, mypy, coverage, pytest, bandit), quality-gate commands |
| `Dockerfile`, `Dockerfile.worker`, `docker-compose.yml` | API and worker container definitions plus local PostgreSQL compose stack |
| `.env.example` | Documented, non-secret template for local configuration |

## Prerequisites

- Python 3.11 or newer (`requires-python = ">=3.11"`; CI runs 3.13).
- `pip` and a virtual environment tool (`python3 -m venv`).
- Docker, only if you want the local PostgreSQL service from `docker-compose.yml`.
  The test suite never touches a live database; PostgreSQL is needed only to run the
  runtime locally.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Editable Install

Install the package in editable mode with the development toolchain:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e .[dev]
```

The `dev` extra installs `bandit[toml]`, `coverage`, `mypy`, `pip-audit`, `pytest`,
`pytest-cov`, `ruff`, and `types-defusedxml`. Runtime dependencies are exactly
`defusedxml`, `fastapi`, `pydantic`, `psycopg`, and `uvicorn`; adding a dependency is
an ADR-level decision, not a drive-by edit.

The install exposes the `jedi-devproject` console script (`jedi_devproject.cli:main`).
All modules are also runnable as `python3 -m jedi_devproject.<module>`.

Copy `.env.example` to `.env` for local configuration. Never commit `.env`; it is
gitignored and excluded from the Docker build context.

## Local Verification

Run the full local quality gate before treating any sprint task as complete:

```bash
python3 -m ruff check src tests && python3 -m bandit -q -r src && python3 -m pip_audit . --progress-spinner off && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

This must pass before every commit. The same gate runs in CI
(`.github/workflows/ci.yml`) on every pull request and every push to `master`.

The individual commands are recorded in `pyproject.toml` under
`tool.jedi-devproject.commands`:

| Command | Purpose |
|---|---|
| `python3 -m ruff check src tests` | Lint (`E`, `F`, `I`, `UP`, `B`, `SIM`; line length 100; target `py311`) |
| `python3 -m ruff format src tests` | Format source and tests |
| `python3 -m bandit -q -r src` | Static security scan of `src` (`tests/` excluded via `tool.bandit`) |
| `python3 -m pip_audit . --progress-spinner off` | Audit installed dependencies for known vulnerabilities |
| `python3 -m mypy src tests` | Strict type check of source **and** tests |
| `python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90` | Test suite with branch coverage gate |

Configuration values that shape these commands:

- `tool.ruff`: `line-length = 100`, `target-version = "py311"`, lint select `E,F,I,UP,B,SIM`.
- `tool.mypy`: `strict = true`, `python_version = "3.11"`, `mypy_path = "src"`. Strict
  mode applies to `tests/` too — every test function is fully annotated (`-> None`).
- `tool.pytest.ini_options`: `testpaths = ["tests"]`, `pythonpath = ["src"]`, so the
  suite imports the package from `src` without installation side effects.
- `tool.coverage.run`: `branch = true`, `source = ["jedi_devproject"]`. Coverage is
  **branch** coverage, not line coverage.
- `tool.coverage.report`: `fail_under = 90`, `show_missing = true`,
  `skip_covered = true`. The 90% gate is mandatory; do not lower it and do not add
  `# pragma: no cover` to game it.
- `tool.bandit`: `exclude_dirs = ["tests"]` — security scanning applies to shipped
  code only.

## Pre-Commit Expectations

No pre-commit framework is configured in this repository; there is no
`.pre-commit-config.yaml` and no git hook tooling. The expectation is manual and
absolute: the full verify command above exits 0 before every commit.

Concretely, before committing:

1. Run `python3 -m ruff format src tests` and `python3 -m ruff check src tests`.
2. Run the full verify command and confirm a clean exit with coverage at or above 90%.
3. Confirm no secrets, credentials, tokens, or regulated customer data appear in code,
   tests, prompts, artifacts, docs, or the commit message.
4. Confirm the commit contains code, tests, and docs together — docs whose statements
   the change falsifies are updated in the same commit. Several docs (change logs,
   operator guide, this guide, Docker files) are protected by text-assertion tests
   (`tests/test_project_docs.py`, `tests/test_container_runtime.py`); update the paired
   assertions in the same commit when you change the documented text.

## Branch and PR Conventions

- One sprint of scope per PR. Branch naming: `syndicalt/sprint-NNN-<topic>` for
  implementation work, `syndicalt/docs-<topic>` for docs-only work.
- Merge commits, not squash merges, so the sprint history stays inspectable.
- Every implementation commit includes `src/`, `tests/`, and
  `docs/sprints/sprint-NNN-change-log.md` together, plus operator-guide,
  system-architecture, or risk-register updates when behavior they describe changes.
- Commit style: short imperative subject, no prefix (example: "Harden structured
  business rule metadata"). The PR head commit body ends with a `Verified:` line
  carrying real numbers (ruff clean, mypy clean, test count, coverage %).
- ADRs (`docs/adr/NNNN-slug.md`) are written and merged **before** implementing a new
  capability family or architecture/policy decision. Sprint change logs record work
  done; release docs (`docs/releases/`) exist only for milestone releases.
- CI must be green: lint, security audit (`bandit` + `pip-audit`), strict mypy, and
  the coverage-gated test suite all run on every pull request.

## Engineering Rules

- Write the failing test first.
- Keep modules small and typed.
- Maintain at least 90% branch coverage.
- Prefer re-engineering over hacks or hidden bypasses.
- Document assumptions in the sprint plan or an ADR.
- Never put secrets, credentials, tokens, or regulated customer data into tests,
  prompts, artifacts, or logs.
- Keep the safety invariants intact: no `sys_id` in model input or output, provider
  calls gated by `ProviderPolicy.allows`, model output as structured changes (never
  raw XML), export gated on explicit approval, write-once audit artifacts, secrets
  redacted from all error text, and `apply_*` flags defaulting to `False`.
