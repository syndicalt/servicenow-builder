"""Shared Unicode control-character predicates.

Centralises the definition of "control character" so URL, config, provider-response,
and packet validation gates reject the same character categories instead of duplicating
inconsistent ASCII-only checks.
"""

from __future__ import annotations

import unicodedata


def is_control_character(character: str) -> bool:
    """Return True if *character* is a Unicode control, surrogate, or format character.

    Raises ``ValueError`` for non-exact strings or non-single-character inputs so
    malformed helper inputs cannot fall through to category lookup.
    """
    if type(character) is not str:
        raise ValueError("character must be an exact string")
    if len(character) != 1:
        raise ValueError("character must be a single character")
    return unicodedata.category(character).startswith("C")
