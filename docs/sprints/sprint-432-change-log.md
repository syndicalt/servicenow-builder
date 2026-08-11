# Sprint 432 Change Log

## Flow graph diff structural validation-error routing

Hardened Flow graph diff candidate validation so unsupported-operation routing no longer depends on stringifying Pydantic validation errors. Prior behavior caught `ValidationError` in `validate_flow_graph_diff_candidate()`, then searched `str(exc)` for `requested_graph_diff` and `operation` before converting unsupported graph rewrites into the stable `unsupported Flow graph diff operation` diagnostic.

The validator now inspects `ValidationError.errors()[].loc` structurally. If the validation failure is located at the `requested_graph_diff` `operation` path, it raises the stable unsupported-operation error without stringifying the original validation error. Other validation failures continue to propagate as `ValidationError`.

This keeps Flow graph diff rejection deterministic and safe even if a validation error object cannot be stringified, and it avoids treating human-readable validation text as an API contract.

## Verification

- Added 1 failing-first Flow graph diff validator test covering an unstringifiable Pydantic validation error with the unsupported-operation location.
- `python3 -m pytest tests/test_generation_validators.py -q -k "unsupported_operation_without_stringifying_error"`: failed before implementation because `ValueError: client-secret-value` escaped from `str(exc)` during unsupported-operation routing.
- `python3 -m pytest tests/test_generation_validators.py -q -k "unsupported_graph_rewrite or unsupported_operation_without_stringifying_error"`: 2 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 506 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2283 total tests passed at 93.96% coverage.
