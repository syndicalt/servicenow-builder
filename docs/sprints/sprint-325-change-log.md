# Sprint 325 Change Log - Model and Packet Validation Input Redaction

## Summary

- Core model and implementation packet validation now suppress rejected input values in Pydantic validation errors.
- `Story`, project context, provider policy, retrieval citations, candidate changes, candidate scripts, Update Set candidates, run manifests, packet stories, and implementation packets still name invalid fields without echoing raw rejected values.
- The redaction boundary covers rejected story text, model confidence fragments, generated script content, review notes, citation values, packet context, and model-facing contract snippets before diagnostics can reach logs, artifacts, or ServiceNow work notes.
- Existing story validation, candidate status transitions, implementation packet generation, payload minimization, and model-provider gates remain intact.
- Documented the core model and packet diagnostic boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_models.py::test_core_model_validation_errors_do_not_echo_rejected_inputs tests/test_implementation_packet.py::test_implementation_packet_validation_errors_do_not_echo_rejected_inputs -q` - 5 tests failed before implementation because core model and packet validation errors included `input_value`.
- `python3 -m pytest tests/test_models.py::test_core_model_validation_errors_do_not_echo_rejected_inputs tests/test_implementation_packet.py::test_implementation_packet_validation_errors_do_not_echo_rejected_inputs tests/test_models.py tests/test_implementation_packet.py -q` - 71 passed after implementation.
- `python3 -m pytest tests/test_models.py::test_core_model_validation_errors_do_not_echo_rejected_inputs tests/test_implementation_packet.py::test_implementation_packet_validation_errors_do_not_echo_rejected_inputs tests/test_project_docs.py::test_sprint_three_hundred_twenty_five_documents_model_packet_error_redaction -q` - 6 passed.
- `python3 -m ruff check src/jedi_devproject/models.py src/jedi_devproject/packet_model.py tests/test_models.py tests/test_implementation_packet.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/models.py src/jedi_devproject/packet_model.py tests/test_models.py tests/test_implementation_packet.py tests/test_project_docs.py` - no issues found in 5 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 181 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 399 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1951 passed, total coverage 93.88%.
