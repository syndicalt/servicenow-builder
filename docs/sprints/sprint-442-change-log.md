# Sprint 442 Change Log

## CI/CD capability malformed-result classification

Hardened the CI/CD Update Set API capability evaluator so successful probe responses with malformed `result` shapes fail closed with a specific operator-facing reason instead of collapsing into ambiguous `status_200` diagnostics. Prior behavior treated a present non-object `result` payload as empty metadata, which hid the actual response-contract problem from capability checks.

The evaluator now classifies a present non-object `result` as:

- `malformed_result_payload`

Capability output remains non-throwing for probe workflows, but it records the fixed malformed-payload reason and does not echo the malformed `result` value, credential-like keys, or upstream response fragments.

## Verification

- Added 1 failing-first CI/CD capability test covering a successful malformed `result` payload with credential-like values.
- `python3 -m pytest tests/test_cicd_update_sets.py -q -k "malformed_result"`: failed before implementation because the probe reason was only `status_200`.
- `python3 -m pytest tests/test_cicd_update_sets.py -q`: 3 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 516 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2312 total tests passed at 93.98% coverage.
