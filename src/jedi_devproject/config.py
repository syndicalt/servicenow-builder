from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when project configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    servicenow_instance_url: str
    artifact_dir: Path
    target_boundary: str


REQUIRED_SETTINGS = ("servicenow_instance_url", "artifact_dir", "target_boundary")


def load_config(path: Path) -> AppConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    missing = [setting for setting in REQUIRED_SETTINGS if not _present(data.get(setting))]

    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"Missing required settings: {joined}")

    return AppConfig(
        servicenow_instance_url=str(data["servicenow_instance_url"]),
        artifact_dir=Path(str(data["artifact_dir"])),
        target_boundary=str(data["target_boundary"]),
    )


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""
