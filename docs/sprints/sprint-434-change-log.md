# Sprint 434 Change Log

## CLI external-build delivery typed success requirement

Hardened external-build result processing so delivery-artifact planning no longer depends on a magic exception message. Prior behavior in `process_external_build_result_command()` caught `ValueError` from `reviewed_delivery_jobs_from_build_result()` and compared `str(exc) != "successful_build_required"` to decide whether a failed external build should skip reviewed delivery jobs or fail the CLI command.

`reviewed_delivery_jobs_from_build_result()` now raises `SuccessfulBuildRequiredError` when reviewed delivery jobs are requested for a failed or blocked build. The CLI catches that type directly and treats it as the expected no-delivery-artifacts path. Other `ValueError` failures still render through the CLI redaction path and return a non-zero exit code.

The legacy message text remains on the exception for compatibility with older diagnostics, but it is no longer used as control flow.

## Verification

- Added 2 failing-first tests covering the external-build typed exception contract and CLI processing with a non-sentinel `SuccessfulBuildRequiredError` message.
- `python3 -m pytest tests/test_external_build_contract.py tests/test_cli.py -q -k "failed_build_contract or typed_successful_build_requirement"`: failed before implementation because `SuccessfulBuildRequiredError` did not exist.
- `python3 -m pytest tests/test_external_build_contract.py tests/test_cli.py -q -k "failed_external_build_contract or typed_successful_build_requirement or failed_external_build_result"`: 3 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 508 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2288 total tests passed at 93.96% coverage.
