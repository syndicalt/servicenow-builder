# Sprint 487 Change Log

## Writeback batch report scalar diagnostic normalization

Hardened `build_writeback_batch_report()` diagnostic projection so corrupted in-process report values cannot return Python-only scalar values into JSON-ready batch report artifacts. Sprint 486 made traversal cycle-safe and depth-bounded; this sprint closes unsupported scalar leakage.

`_diagnostic_report_value()` now normalizes unsupported scalar diagnostics through a fixed `[non-json value]` marker. Non-finite floats (`NaN`, `Infinity`, `-Infinity`), bytes, and arbitrary Python objects do not appear in reports as raw values, reprs, or type names. Finite JSON primitives such as ordinary numbers, booleans, and `None` remain typed.

## Verification

- Added 1 failing-first writeback orchestration test covering bytes, Python objects, non-finite floats, and ordinary JSON primitives in batch report diagnostics.
- `python3 -m pytest tests/test_writeback_orchestration.py::test_build_writeback_batch_report_normalizes_unsupported_scalar_diagnostics -q`: failed before implementation because raw unsupported diagnostics could break capability serialization before the report sanitizer ran.
- `python3 -m pytest tests/test_writeback_orchestration.py -q`: 24 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 561 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2417 total tests passed at 93.82% coverage.
