import re
from pathlib import Path

CI_WORKFLOW = Path(".github/workflows/ci.yml")


def test_ci_workflow_enforces_production_verification_gates() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "name: CI" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "branches: [master]" in workflow
    assert "python-version: \"3.13\"" in workflow
    assert "pip install -e .[dev]" in workflow
    assert "python3 -m ruff check src tests" in workflow
    assert "python3 -m bandit -q -r src" in workflow
    assert "python3 -m pip_audit . --progress-spinner off" in workflow
    assert "python3 -m mypy src tests" in workflow
    assert (
        "python3 -m pytest --cov=jedi_devproject --cov-report=term "
        "--cov-fail-under=90 -q"
    ) in workflow


def test_ci_workflow_runs_security_gates_before_typecheck_and_tests() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.index("python3 -m ruff check src tests") < workflow.index(
        "python3 -m bandit -q -r src"
    )
    assert workflow.index("python3 -m bandit -q -r src") < workflow.index(
        "python3 -m pip_audit . --progress-spinner off"
    )
    assert workflow.index("python3 -m pip_audit . --progress-spinner off") < workflow.index(
        "python3 -m mypy src tests"
    )
    assert workflow.index("python3 -m mypy src tests") < workflow.index(
        "python3 -m pytest --cov=jedi_devproject"
    )


def test_ci_workflow_uses_safe_shell_defaults() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "shell: bash" in workflow
    assert "set -euo pipefail" in workflow


def test_ci_workflow_uses_read_only_token_permissions() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "permissions:" in workflow
    assert "  contents: read" in workflow
    assert "contents: write" not in workflow
    assert "pull-requests: write" not in workflow


def test_ci_workflow_cancels_stale_verification_runs() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "concurrency:" in workflow
    assert "group: ${{ github.workflow }}-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow
    assert workflow.index("concurrency:") < workflow.index("jobs:")


def test_ci_workflow_does_not_persist_checkout_credentials() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "uses: actions/checkout@" in workflow
    assert "persist-credentials: false" in workflow
    assert workflow.index("uses: actions/checkout@") < workflow.index(
        "persist-credentials: false"
    )


def test_ci_workflow_pins_third_party_actions_to_commit_shas() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    action_refs = re.findall(r"uses:\s+(actions/[a-z-]+)@([^\s]+)", workflow)

    assert action_refs == [
        ("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262"),
        ("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065"),
    ]
    for _action, ref in action_refs:
        assert re.fullmatch(r"[0-9a-f]{40}", ref)
