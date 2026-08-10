from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jedi_devproject.artifacts import ArtifactReadError, open_regular_artifact_file
from jedi_devproject.unicode_controls import is_control_character
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
)


class ConfigError(ValueError):
    """Raised when project configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    servicenow_instance_url: str
    artifact_dir: Path
    target_boundary: str


REQUIRED_SETTINGS = ("servicenow_instance_url", "artifact_dir", "target_boundary")
PROJECT_CONFIG_MAX_BYTES = 1024 * 1024


def load_config(path: Path) -> AppConfig:
    data = tomllib.loads(_read_bounded_config_text(path))
    missing = [setting for setting in REQUIRED_SETTINGS if not _present(data.get(setting))]

    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"Missing required settings: {joined}")
    errors = _config_value_errors(data)
    if errors:
        raise ConfigError("; ".join(errors))

    return AppConfig(
        servicenow_instance_url=str(data["servicenow_instance_url"]),
        artifact_dir=Path(str(data["artifact_dir"])),
        target_boundary=str(data["target_boundary"]),
    )


def _config_value_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    servicenow_instance_url = str(data["servicenow_instance_url"])
    parsed_servicenow_url = urlparse(servicenow_instance_url)
    if (
        has_whitespace_or_control_character(servicenow_instance_url)
        or has_encoded_whitespace_or_control_character(servicenow_instance_url)
        or parsed_servicenow_url.scheme.lower() != "https"
        or parsed_servicenow_url.username
        or parsed_servicenow_url.password
        or parsed_servicenow_url.fragment
        or not parsed_servicenow_url.hostname
    ):
        errors.append(
            "servicenow_instance_url must be an HTTPS ServiceNow URL without "
            "credentials, fragments, whitespace, encoded whitespace/control "
            "characters, or control characters"
        )
    for setting in ("artifact_dir", "target_boundary"):
        value = str(data[setting])
        if value != value.strip() or _has_control_character(value):
            errors.append(f"{setting} must not be empty, padded, or contain control characters")
    return errors


def _has_control_character(value: str) -> bool:
    return any(is_control_character(character) for character in value)


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _read_bounded_config_text(path: Path) -> str:
    try:
        with open_regular_artifact_file(path) as config_file:
            payload = config_file.read(PROJECT_CONFIG_MAX_BYTES + 1)
    except ArtifactReadError:
        raise ConfigError("project_config_must_be_regular_file") from None
    if len(payload) > PROJECT_CONFIG_MAX_BYTES:
        raise ConfigError(f"project_config_too_large: exceeds {PROJECT_CONFIG_MAX_BYTES} bytes")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        raise ConfigError("project_config_invalid_utf8") from None
