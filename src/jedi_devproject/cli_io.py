"""Shared JSON payload loading and summary rendering for CLI commands."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path


def load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("provider response file must contain a JSON object")
    return payload


def load_json_list(path: Path, description: str) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{description} must contain a JSON list")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{description} entries must be JSON objects")
    return payload


def render_summary(summary: Mapping[str, object]) -> str:
    return " ".join(f"{key}={value}" for key, value in summary.items())
