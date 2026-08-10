"""Shared redaction for diagnostic strings that may contain secret material."""

from __future__ import annotations

import re
from urllib.parse import unquote_plus, urlsplit, urlunsplit

from jedi_devproject.sensitive_keys import SENSITIVE_QUERY_KEYS, is_sensitive_key

SENSITIVE_ASSIGNMENT_KEYS = frozenset(
    SENSITIVE_QUERY_KEYS | {key.replace("_", "-") for key in SENSITIVE_QUERY_KEYS}
)
NON_STRING_DIAGNOSTIC_TEXT_LABEL = "[non-string diagnostic text]"

URL_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>'\"]+")
PEM_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
AUTHORIZATION_SCHEME_PATTERN = re.compile(
    r"\b(authorization\s*[=:]\s*)(bearer|basic)(\s+)([^\s,;&]+)",
    re.IGNORECASE,
)
COOKIE_HEADER_PATTERN = re.compile(
    r"\b((?:set-cookie|cookie)\s*[=:]\s*)([^\r\n]*)",
    re.IGNORECASE,
)
SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"\b("
    + "|".join(
        re.escape(key) for key in sorted(SENSITIVE_ASSIGNMENT_KEYS, key=len, reverse=True)
    )
    + r""")(\s*[=:]\s*)("[^"]*"|'[^']*'|[^\s,;&]+)""",
    re.IGNORECASE,
)


def _redact_diagnostic_text(text: str | None) -> str | None:
    if text is None:
        return None
    if type(text) is not str:
        return NON_STRING_DIAGNOSTIC_TEXT_LABEL
    redacted = URL_PATTERN.sub(lambda match: _redact_url(match.group(0)), text)
    redacted = PEM_PRIVATE_KEY_PATTERN.sub("***REDACTED***", redacted)
    redacted = COOKIE_HEADER_PATTERN.sub(
        lambda match: f"{match.group(1)}***REDACTED***",
        redacted,
    )
    redacted = AUTHORIZATION_SCHEME_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}{match.group(2)}{match.group(3)}***REDACTED***"
        ),
        redacted,
    )
    return SENSITIVE_ASSIGNMENT_PATTERN.sub(_redact_sensitive_assignment, redacted)


def _redact_sensitive_assignment(match: re.Match[str]) -> str:
    key = match.group(1)
    value = match.group(3)
    if is_sensitive_key(key) and key.lower() == "authorization" and value.lower() in {
        "bearer",
        "basic",
    }:
        return match.group(0)
    return f"{key}{match.group(2)}***REDACTED***"


def _redact_url(url: str) -> str:
    url_body, trailing = _split_trailing_url_punctuation(url)
    try:
        parts = urlsplit(url_body)
    except ValueError:
        return "***REDACTED***" + trailing
    if not parts.netloc:
        return url
    query = _redact_sensitive_query_values(parts.query)
    if parts.username is None and parts.password is None:
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, query, parts.fragment)
        ) + trailing
    host = parts.hostname or ""
    try:
        port = f":{parts.port}" if parts.port is not None else ""
    except ValueError:
        return "***REDACTED***" + trailing
    userinfo = "***REDACTED***@"
    netloc = f"{userinfo}{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment)) + trailing


def _split_trailing_url_punctuation(url: str) -> tuple[str, str]:
    stripped = url.rstrip(".,);]")
    return stripped, url[len(stripped) :]


def _redact_sensitive_query_values(query: str) -> str:
    if not query:
        return query
    parts = re.split(r"([&;])", query)
    redacted_parts: list[str] = []
    for item in parts:
        if item in {"&", ";"}:
            redacted_parts.append(item)
            continue
        key, separator, value = item.partition("=")
        decoded_key = unquote_plus(key)
        if separator and is_sensitive_key(decoded_key):
            redacted_parts.append(f"{key}=***REDACTED***")
        else:
            redacted_parts.append(item if value or separator else key)
    return "".join(redacted_parts)
