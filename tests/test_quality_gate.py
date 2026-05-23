import tomllib
from pathlib import Path


def test_coverage_gate_is_configured_at_90_percent() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    coverage_options = pyproject["tool"]["coverage"]["report"]
    assert coverage_options["fail_under"] == 90


def test_test_command_includes_coverage_enforcement() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    test_command = pyproject["tool"]["jedi-devproject"]["commands"]["test"]
    assert "--cov=jedi_devproject" in test_command
    assert "--cov-fail-under=90" in test_command


def test_verify_command_runs_lint_typecheck_and_coverage_tests() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    verify_command = pyproject["tool"]["jedi-devproject"]["commands"]["verify"]
    assert "ruff check src tests" in verify_command
    assert "mypy src tests" in verify_command
    assert "--cov-fail-under=90" in verify_command


def test_env_file_is_ignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert ".env" in gitignore.splitlines()


def test_env_example_documents_required_servicenow_keys() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "SERVICENOW_PM_INSTANCE_URL=" in env_example
    assert "SERVICENOW_PM_CLIENT_ID=" in env_example
    assert "SERVICENOW_PM_CLIENT_SECRET=" in env_example
    assert "SERVICENOW_DEV_INSTANCE_URL=" in env_example
    assert "SERVICENOW_DEV_CLIENT_ID=" in env_example
    assert "SERVICENOW_DEV_CLIENT_SECRET=" in env_example
    assert "SERVICENOW_INSTANCE_URL=" in env_example
    assert "SERVICENOW_CLIENT_ID=" in env_example
    assert "SERVICENOW_CLIENT_SECRET=" in env_example
