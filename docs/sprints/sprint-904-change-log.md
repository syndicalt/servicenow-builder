# Sprint 904 Change Log

## Packet-intent catalog UI Policy tristate guard

Hardened normalized-intent catalog UI Policy action parsing so deterministic catalog candidate generation no longer stringifies arbitrary action tristate values before validation.

`_catalog_item_changes_from_normalized_intent()` now accepts exact strings `true`, `false`, and `ignore`, plus actual JSON booleans, for catalog UI Policy action `visible`, `mandatory`, and `disabled` values. String subclasses and arbitrary objects fail with fixed diagnostics such as `catalog variable rule Show schedule action visible must be true, false, or ignore`.

The diagnostic does not echo subclass names, overridden string output, credential-like fragments, action values, variable names, generated candidate fields, or downstream XML. This keeps the normalized-intent boundary closed before stringification, trimming, lowercase normalization, candidate-change construction, downstream XML generation, ServiceNow import planning, or story writeback can execute caller-controlled methods.

## Tests

- Added 1 failing-first normalized-intent string-subclass assertion: `test_catalog_changes_reject_string_subclass_rule_action_without_leak`.
- Focused red: `pytest tests/test_implementation_packet.py::test_catalog_changes_reject_string_subclass_rule_action_without_leak tests/test_project_docs.py::test_sprint_904_documents_packet_intent_catalog_ui_policy_tristate_guard -q` failed because the string subclass executed its overridden `__str__()` method during catalog UI Policy action parsing.
- Focused green: `pytest tests/test_implementation_packet.py::test_catalog_changes_reject_string_subclass_rule_action_without_leak tests/test_project_docs.py::test_sprint_904_documents_packet_intent_catalog_ui_policy_tristate_guard -q` passed with 2 tests.
- Implementation packet suite: `pytest tests/test_implementation_packet.py -q` passed with 71 tests.
- Documentation suite: `pytest tests/test_project_docs.py -q` passed with 977 tests.
- Static gates: `python3 -m ruff check src tests` and `python3 -m mypy src tests` passed.
- Full coverage gate: `pytest --cov=src/jedi_devproject --cov-report=term:skip-covered -q` passed with 3518 tests at 93.51% coverage.
