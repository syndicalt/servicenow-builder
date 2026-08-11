# Sprint 989 Change Log - Pipeline CLI story lookup guard

## Summary

Hardened PDI-backed pipeline and implementation CLI commands so ServiceNow story lookup results are validated before downstream processing. The commands now fail closed with `story_lookup_result_unsafe` when a story fetch returns a list subclass, alternate iterable, model subclass, or malformed story entry.

## Security

`run_pdi_command()`, `_load_stories_from_args()`, and `run_lifecycle_smoke_command()` now route ServiceNow story fetches through `_pipeline_story_lookup_results()`. The helper accepts only exact Python lists containing exact `Story` records. Unsafe shapes are rejected before truthiness hooks, indexing hooks, pipeline execution, packet generation, candidate artifact writing, lifecycle manifest writing, or dry-run writeback planning can execute caller-controlled behavior.

## Tests

- Added 1 failing-first implementation packet story collection assertion: `test_cli_build_implementation_packet_rejects_story_collection_subclass_without_leak`.
- Added 1 failing-first lifecycle smoke story collection assertion: `test_cli_run_lifecycle_smoke_rejects_story_collection_subclass_without_leak`.
- Added 1 failing-first PDI pipeline story collection assertion: `test_cli_run_pdi_rejects_story_collection_subclass_without_leak`.
- Added 1 documentation assertion: `test_sprint_989_documents_pipeline_cli_story_lookup_guard`.

## Verification

- `pytest tests/test_cli.py::test_cli_build_implementation_packet_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_run_lifecycle_smoke_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_run_pdi_rejects_story_collection_subclass_without_leak -q` failed before implementation because malformed story collections reached truthiness hooks or were accepted into the PDI pipeline.
- `pytest tests/test_cli.py::test_cli_build_implementation_packet_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_run_lifecycle_smoke_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_run_pdi_rejects_story_collection_subclass_without_leak tests/test_cli.py::test_cli_build_implementation_packet_fetches_story_from_pdi tests/test_cli.py::test_cli_build_implementation_candidate_fetches_story_from_pdi tests/test_cli.py::test_cli_run_lifecycle_smoke_builds_artifacts_and_plans_writeback tests/test_cli.py::test_cli_run_pdi_fetches_stories_and_prints_safe_summary -q` - 7 passed.
- `python3 -m ruff check src/jedi_devproject/cli_pipeline.py tests/test_cli.py` - passed.
- `python3 -m mypy src/jedi_devproject/cli_pipeline.py tests/test_cli.py` - passed.
