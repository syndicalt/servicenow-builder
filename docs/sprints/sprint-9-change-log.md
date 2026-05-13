# Sprint 9 Change Log

## Scope

Sprint 9 added hardening and review artifacts for engineering, security, and product stakeholders.

## Changes

- Threat model in `docs/security/threat-model.md`.
- Data flow documentation in `docs/security/data-flow.md`.
- Security control mapping draft in `docs/security/control-mapping.md`.
- Operator guide in `docs/operator-guide.md`.
- Risk register in `docs/risk-register.md`.
- Default provider policy module in `src/jedi_devproject/security_defaults.py`.
- No public model provider enabled by default.

## Assumptions Challenged

- This is not an ATO package; it is a development evidence package that makes remaining ATO work explicit.
- Rules-only default provider policy is intentionally conservative.
- Live PDI access remains manual and read-only until a stronger integration test environment is defined.

## Verification Evidence

Target command:

```bash
python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest --cov=jedi_devproject --cov-report=term-missing --cov-fail-under=90
```

Expected result:

- Ruff passes.
- Mypy passes.
- Pytest passes.
- Coverage remains above the 90% gate.
