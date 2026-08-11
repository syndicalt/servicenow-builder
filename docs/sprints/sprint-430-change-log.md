# Sprint 430 Change Log

## Flow XML evidence invalid-shape safe diagnostics

Hardened Flow XML evidence collection so invalid-shape evidence records remain durable when the shape validator exception cannot be stringified. Prior behavior caught `ValueError` from `validate_flow_xml_shape_evidence()`, then called `str(exc)` directly while populating `FlowXmlShapeEvidenceRecord.reason`.

The collector now formats shape validation failures through `exception_diagnostic_message(..., fallback_subject="flow xml evidence")`. Normal invalid-shape reasons are preserved. If a validator dependency or future XML evidence check raises an exception that cannot be stringified, the evidence record stores `flow xml evidence raised unstringifiable <ExceptionType>` or the generic `flow xml evidence raised unstringifiable exception` instead of letting a secondary stringification failure break collection.

This keeps Flow builder readiness evidence auditable even when one retrieved XML shape is malformed or a validator fails unexpectedly.

## Verification

- Added 1 failing-first Flow XML evidence test covering an unstringifiable shape validation error.
- `python3 -m pytest tests/test_flow_xml_evidence.py -q -k "unstringifiable_shape_validation_error"`: failed before implementation because `ValueError: client-secret-value` escaped during invalid-shape reason rendering.
- `python3 -m pytest tests/test_flow_xml_evidence.py -q -k "empty_and_malformed_payloads or unstringifiable_shape_validation_error"`: 2 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 504 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2279 total tests passed at 93.97% coverage.
