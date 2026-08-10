from pathlib import Path

import pytest

from jedi_devproject import cli_io
from jedi_devproject.cli_io import (
    load_json_list,
    load_json_object,
    render_cli_error,
    render_summary,
)


class _UnstringifiableCliError(RuntimeError):
    def __str__(self) -> str:
        raise ValueError("client-secret-value")


class _HostileSummaryText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=summary-text-secret")


class _HostileSummaryValue:
    def __str__(self) -> str:
        raise AssertionError("client_secret=summary-object-secret")


def test_load_json_object_rejects_oversized_input_without_read_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text('{"ok": true}', encoding="utf-8")
    monkeypatch.setattr(cli_io, "CLI_JSON_INPUT_MAX_BYTES", 4, raising=False)

    def fail_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        raise AssertionError(f"unexpected whole-file text read for {self}")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(ValueError, match="json_input_too_large"):
        load_json_object(payload_path)


def test_load_json_object_oversized_error_does_not_echo_input_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload_path = tmp_path / "client_secret=json-loader-secret.json"
    payload_path.write_text('{"ok": true}', encoding="utf-8")
    monkeypatch.setattr(cli_io, "CLI_JSON_INPUT_MAX_BYTES", 4, raising=False)

    with pytest.raises(ValueError) as exc_info:
        load_json_object(payload_path)

    diagnostic = str(exc_info.value)
    assert "json_input_too_large" in diagnostic
    assert "json-loader-secret" not in diagnostic
    assert str(payload_path) not in diagnostic


def test_load_json_list_rejects_oversized_input_without_read_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text('[{"ok": true}]', encoding="utf-8")
    monkeypatch.setattr(cli_io, "CLI_JSON_INPUT_MAX_BYTES", 4, raising=False)

    def fail_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        raise AssertionError(f"unexpected whole-file text read for {self}")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(ValueError, match="json_input_too_large"):
        load_json_list(payload_path, "artifact handoff jobs file")


def test_load_json_object_rejects_symlinked_input(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text('{"ok": true}', encoding="utf-8")
    payload_link = tmp_path / "payload.json"
    payload_link.symlink_to(target_path)

    with pytest.raises(ValueError, match="json_input_must_be_regular_file"):
        load_json_object(payload_link)


def test_load_json_object_regular_file_error_does_not_echo_input_path(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text('{"ok": true}', encoding="utf-8")
    payload_link = tmp_path / "client_secret=json-link-secret.json"
    payload_link.symlink_to(target_path)

    with pytest.raises(ValueError) as exc_info:
        load_json_object(payload_link)

    diagnostic = str(exc_info.value)
    assert "json_input_must_be_regular_file" in diagnostic
    assert "json-link-secret" not in diagnostic
    assert str(payload_link) not in diagnostic
    assert exc_info.value.__cause__ is None


def test_load_json_object_invalid_utf8_error_does_not_echo_input_path_or_bytes(
    tmp_path: Path,
) -> None:
    payload_path = tmp_path / "client_secret=json-utf8-secret.json"
    payload_path.write_bytes(b'{"token":"\xff"}')

    with pytest.raises(ValueError) as exc_info:
        load_json_object(payload_path)

    diagnostic = str(exc_info.value)
    assert "json_input_invalid_utf8" in diagnostic
    assert "json-utf8-secret" not in diagnostic
    assert str(payload_path) not in diagnostic
    assert "token" not in diagnostic
    assert exc_info.value.__cause__ is None


def test_load_json_object_rejects_non_finite_json_without_payload_leak(
    tmp_path: Path,
) -> None:
    payload_path = tmp_path / "client_secret=json-nan-secret.json"
    payload_path.write_text(
        '{"score": NaN, "client_secret": "payload-secret"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        load_json_object(payload_path)

    diagnostic = str(exc_info.value)
    assert diagnostic == "json_input_invalid_json"
    assert "score" not in diagnostic
    assert "NaN" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "payload-secret" not in diagnostic
    assert "json-nan-secret" not in diagnostic
    assert str(payload_path) not in diagnostic
    assert exc_info.value.__cause__ is None


def test_load_json_list_rejects_symlinked_input(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text('[{"ok": true}]', encoding="utf-8")
    payload_link = tmp_path / "payload.json"
    payload_link.symlink_to(target_path)

    with pytest.raises(ValueError, match="json_input_must_be_regular_file"):
        load_json_list(payload_link, "artifact handoff jobs file")


def test_render_summary_redacts_and_normalizes_untrusted_keys_and_values() -> None:
    summary = {
        "handoff_plans\nclient_secret=key-secret": "2\napi_key=value-secret",
        "ok": True,
    }

    rendered = render_summary(summary)

    assert "key-secret" not in rendered
    assert "value-secret" not in rendered
    assert "client_secret=***REDACTED***" in rendered
    assert "api_key=***REDACTED***" in rendered
    assert "\n" not in rendered
    assert "ok=True" in rendered


def test_render_summary_bounds_untrusted_keys_and_values() -> None:
    summary = {
        f"handoff_plans {'A' * 2200}": f"2 {'B' * 2200}",
        "ok": True,
    }

    rendered = render_summary(summary)

    assert rendered.count("...[truncated]") == 2
    assert len(rendered) < 1100
    assert "ok=True" in rendered


def test_render_summary_does_not_coerce_hostile_keys_or_values() -> None:
    summary = {
        _HostileSummaryText("client_secret=summary-key-payload"): _HostileSummaryValue(),
        "ok": True,
    }

    rendered = render_summary(summary)

    assert "summary-key-payload" not in rendered
    assert "summary-object-secret" not in rendered
    assert "[non-string work note value]=[unsupported summary value]" in rendered
    assert "ok=True" in rendered


def test_render_cli_error_handles_unstringifiable_exceptions_without_leaking_secret() -> None:
    rendered = render_cli_error(_UnstringifiableCliError("unused"))

    assert rendered == "CLI raised unstringifiable _UnstringifiableCliError"
    assert "client-secret-value" not in rendered
