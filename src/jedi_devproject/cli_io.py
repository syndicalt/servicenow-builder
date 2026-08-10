"""Shared JSON payload loading and summary rendering for CLI commands."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from jedi_devproject.artifacts import ArtifactReadError, open_regular_artifact_file
from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.work_note_safety import safe_work_note_value

CLI_JSON_INPUT_MAX_BYTES = 10 * 1024 * 1024


def load_json_object(path: Path) -> dict[str, object]:
    payload = load_json_payload(path)
    if not isinstance(payload, dict):
        raise ValueError("provider response file must contain a JSON object")
    return cast(dict[str, object], payload)


def load_json_list(path: Path, description: str) -> list[dict[str, object]]:
    payload = load_json_payload(path)
    if not isinstance(payload, list):
        raise ValueError(f"{description} must contain a JSON list")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{description} entries must be JSON objects")
    return cast(list[dict[str, object]], payload)


def load_json_payload(path: Path) -> Any:
    payload_bytes = _read_bounded_json_bytes(path)
    try:
        payload_text = payload_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("json_input_invalid_utf8") from None
    try:
        return json.loads(payload_text, parse_constant=_reject_cli_json_constant)
    except (json.JSONDecodeError, ValueError):
        raise ValueError("json_input_invalid_json") from None


def render_summary(summary: Mapping[str, object]) -> str:
    return " ".join(
        f"{safe_work_note_value(key)}={safe_work_note_value(_summary_scalar_value(value))}"
        for key, value in summary.items()
    )


def _summary_scalar_value(value: object) -> str:
    if type(value) is str:
        return value
    if value is None:
        return "None"
    if type(value) is bool:
        return "True" if value else "False"
    if type(value) is int:
        return str(value)
    if type(value) is float and math.isfinite(value):
        return str(value)
    return "[unsupported summary value]"


def render_cli_error(exc: BaseException) -> str:
    return _redact_diagnostic_text(exception_diagnostic_message(exc, fallback_subject="CLI")) or ""


def _read_bounded_json_bytes(path: Path) -> bytes:
    try:
        with open_regular_artifact_file(path) as payload_file:
            payload = payload_file.read(CLI_JSON_INPUT_MAX_BYTES + 1)
    except ArtifactReadError:
        raise ValueError("json_input_must_be_regular_file") from None
    if len(payload) > CLI_JSON_INPUT_MAX_BYTES:
        raise ValueError(f"json_input_too_large: exceeds {CLI_JSON_INPUT_MAX_BYTES} bytes")
    return payload


def _reject_cli_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")
