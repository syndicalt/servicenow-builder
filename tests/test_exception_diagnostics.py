from __future__ import annotations

import ast
from pathlib import Path

from jedi_devproject.exception_diagnostics import exception_diagnostic_message


class _UnstringifiableDiagnosticError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


def test_exception_diagnostic_message_preserves_stringifiable_errors() -> None:
    error = RuntimeError("provider failed client_secret=secret-value")

    assert (
        exception_diagnostic_message(error, fallback_subject="worker")
        == "provider failed client_secret=secret-value"
    )


def test_exception_diagnostic_message_falls_back_for_unstringifiable_errors() -> None:
    error = _UnstringifiableDiagnosticError("unused")

    assert (
        exception_diagnostic_message(error, fallback_subject="worker")
        == "worker raised unstringifiable _UnstringifiableDiagnosticError"
    )


def test_exception_diagnostic_message_drops_unsafe_type_labels() -> None:
    _UnstringifiableDiagnosticError.__name__ = "client-secret-value"
    error = _UnstringifiableDiagnosticError("unused")

    try:
        message = exception_diagnostic_message(error, fallback_subject="worker")
    finally:
        _UnstringifiableDiagnosticError.__name__ = "_UnstringifiableDiagnosticError"

    assert message == "worker raised unstringifiable exception"
    assert "client-secret-value" not in message


def test_exception_diagnostic_message_rejects_unsafe_fallback_subjects() -> None:
    error = _UnstringifiableDiagnosticError("unused")

    assert (
        exception_diagnostic_message(error, fallback_subject="worker client_secret=value")
        == "error raised unstringifiable _UnstringifiableDiagnosticError"
    )


def test_source_uses_only_suppressed_explicit_exception_causes() -> None:
    unsafe_causes: list[str] = []
    for source_path in sorted(Path("src/jedi_devproject").rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise) or node.cause is None:
                continue
            if isinstance(node.cause, ast.Constant) and node.cause.value is None:
                continue
            unsafe_causes.append(
                f"{source_path}:{node.lineno}: {ast.unparse(node.cause)}"
            )

    assert unsafe_causes == []
