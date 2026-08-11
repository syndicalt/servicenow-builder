# Sprint 770 Change Log - Operational store initialization command

## Scope

Added an explicit operator command for initializing and verifying the PostgreSQL operational store
schema before hosted API or worker services are opened to traffic.

## Tests First

- Added 3 failing-first initialization command assertions:
  - `tests/test_cli.py::test_cli_init_operational_store_verifies_schema_without_echoing_database_url`
  - `tests/test_cli.py::test_cli_init_operational_store_fails_when_schema_is_not_ready`
  - `tests/test_project_docs.py::test_sprint_770_documents_operational_store_initialization_command`
- Initial failures proved `init-operational-store` did not exist, `connect_operational_store` was
  not exposed for the CLI command boundary, and this sprint log was absent.

## Changes

- Added `init-operational-store` to the CLI.
- The command loads runtime settings from `--env-file`, opens the operational store through the
  existing migration-aware store connector, and calls `verify_schema_ready()`.
- Successful initialization prints only `operational_store_schema_ready=true` and exits `0`.
- Missing schema after initialization prints only `operational_store_schema_ready=false` and exits
  `1`.
- Documented the command in the operator guide as the pre-traffic schema initialization step.

## Verification

- `python3 -m pytest tests/test_cli.py tests/test_project_docs.py -q -k "init_operational_store or sprint_770"` - 3 passed, 914 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3132 passed, 93.36% coverage.
