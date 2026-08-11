# Sprint 627 Change Log

## Context escalation exact-string routing boundary

Sprint 627 continued production hardening by tightening `plan_context_escalation()`, the deterministic routing boundary that decides whether fulfillment should retrieve more live ServiceNow context, call the model, or route to manual review. The previous path coerced `status` and `missing_context` values with `str()`, so malformed context sufficiency payloads could execute custom string conversion before the model-call decision was made.

Context escalation now reads `status` and `missing_context` entries only when they are exact `str` instances. String subclasses, objects, numbers, and other malformed values are treated as absent without coercion. Unsafe `status` values fail closed to manual review, and unsafe missing-context entries are skipped before `context_insufficient:<surface>` reasons are built.

Verification:

- Added 2 failing-first context escalation tests proving hostile status and missing-context values executed before implementation.
- `python3 -m pytest tests/test_context_escalation.py::test_context_escalation_fails_closed_for_string_subclass_status tests/test_context_escalation.py::test_context_escalation_skips_unsafe_missing_context_without_coercion -q`: failed before implementation with hostile assertion errors.
- `python3 -m pytest tests/test_context_escalation.py -q`: 5 tests passed.
- `python3 -m pytest tests/test_context_escalation.py tests/test_project_docs.py::test_sprint_627_documents_context_escalation_exact_string_boundary -q`: 6 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 701 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed with no issues in 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2742 tests passed at 93.07% coverage.
