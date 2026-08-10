"""Strict numeric parsing for deployment configuration."""

from __future__ import annotations

import re
from math import isfinite

from jedi_devproject.url_query_safety import has_whitespace_or_control_character

ASCII_DECIMAL_FLOAT_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def parse_optional_base10_int(value: str | None, *, name: str) -> int | None:
    if value is None or value == "":
        return None
    if value != value.strip() or has_whitespace_or_control_character(value):
        raise ValueError(f"{name} must be an integer without padding or control characters")
    if not value.isascii() or not value.isdecimal():
        raise ValueError(f"{name} must be an integer using ASCII base-10 digits only")
    return int(value)


def parse_optional_ascii_decimal_float(value: str | None, *, name: str) -> float | None:
    if value is None or value == "":
        return None
    if value != value.strip() or has_whitespace_or_control_character(value):
        raise ValueError(f"{name} must be a number without padding or control characters")
    try:
        parsed = float(value)
    except ValueError:
        parsed = None
    if parsed is not None and not isfinite(parsed):
        raise ValueError(f"{name} must be a finite number")
    if not value.isascii() or ASCII_DECIMAL_FLOAT_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a number using ASCII decimal number format")
    if parsed is None:
        return float(value)
    return parsed
