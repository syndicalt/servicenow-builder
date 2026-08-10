"""Shared URL content and query validation helpers for outbound URL guards."""

from __future__ import annotations

from urllib.parse import parse_qsl, unquote

from jedi_devproject.sensitive_keys import is_sensitive_key
from jedi_devproject.unicode_controls import is_control_character

MAX_QUERY_DECODE_PASSES = 3


def has_whitespace_or_control_character(value: str) -> bool:
    _require_exact_string(value, label="value")
    return any(character.isspace() or is_control_character(character) for character in value)


def has_encoded_whitespace_or_control_character(value: str) -> bool:
    _require_exact_string(value, label="value")
    if "%" not in value:
        return False
    current = value
    for _ in range(MAX_QUERY_DECODE_PASSES):
        decoded_value = unquote(current)
        if decoded_value == current:
            return False
        if has_whitespace_or_control_character(decoded_value):
            return True
        current = decoded_value
    return False


def sensitive_query_keys(query: str) -> tuple[str, ...]:
    _require_exact_string(query, label="query")
    if not query:
        return ()
    keys = {
        key.lower()
        for key, _value in query_pairs(query)
        if is_sensitive_key(key)
    }
    return tuple(sorted(keys))


def query_pairs(query: str) -> tuple[tuple[str, str], ...]:
    _require_exact_string(query, label="query")
    pairs: list[tuple[str, str]] = []
    for candidate_query in query_pair_candidates(query):
        for chunk in candidate_query.replace(";", "&").split("&"):
            if chunk == "":
                continue
            pairs.extend(parse_qsl(chunk, keep_blank_values=True))
    return tuple(pairs)


def query_pair_candidates(query: str) -> tuple[str, ...]:
    _require_exact_string(query, label="query")
    candidates: list[str] = [query]
    current = query
    for _ in range(MAX_QUERY_DECODE_PASSES):
        decoded_query = unquote(current)
        if decoded_query == current:
            break
        candidates.append(decoded_query)
        current = decoded_query
    return tuple(candidates)


def _require_exact_string(value: str, *, label: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be an exact string")
