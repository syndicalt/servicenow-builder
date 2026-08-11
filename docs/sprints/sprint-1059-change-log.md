# Sprint 1059 Change Log - Security Verification Gate

## Scope

Production hardening for verification. The local and CI quality gates now include
static security scanning and project-scoped dependency vulnerability auditing in
addition to lint, type checking, and the 90% coverage gate.

## Changes

- Added `bandit[toml]`, `pip-audit`, and `types-defusedxml` to development
  dependencies.
- Added `defusedxml` as a runtime dependency and replaced runtime
  `xml.etree.ElementTree.fromstring()` parsing on ServiceNow XML payload paths.
- Replaced runtime `assert` validation with explicit exceptions in lifecycle
  bootstrap generation.
- Added CI security audit steps:
  - `python3 -m bandit -q -r src`
  - `python3 -m pip_audit . --progress-spinner off`
- Updated the documented local verification command and `tool.jedi-devproject`
  verification command set.

## Tests

- `test_ci_workflow_enforces_production_verification_gates`
- `test_ci_workflow_runs_security_gates_before_typecheck_and_tests`
- `test_sprint_1059_documents_security_verification_gate`
- `test_production_hardening_completion_audit_documents_current_evidence`

## Verification

Final verification for this sprint must include:

```bash
python3 -m ruff check src tests
python3 -m bandit -q -r src
python3 -m pip_audit . --progress-spinner off
python3 -m mypy src tests
python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90 -q
```

## Residual Risk

`pip-audit .` audits the project dependency graph resolved from this package,
not unrelated packages in a developer workstation or Conda base environment.
Production image and platform vulnerability scanning remain separate deployment
controls.
