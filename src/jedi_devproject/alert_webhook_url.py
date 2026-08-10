"""Shared validation for external alert webhook sink URLs."""

from __future__ import annotations

from urllib.parse import urlparse

from jedi_devproject.url_host_safety import ip_address_from_hostname, normalize_hostname
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
    sensitive_query_keys,
)


def validate_alert_webhook_url(
    webhook_url: str,
    *,
    subject: str = "alert webhook URL",
) -> tuple[str, ...]:
    errors: list[str] = []
    if has_whitespace_or_control_character(webhook_url):
        errors.append(f"{subject} must not include whitespace or control characters")
    if has_encoded_whitespace_or_control_character(webhook_url):
        errors.append(
            f"{subject} must not include encoded whitespace or control characters"
        )
    parsed = urlparse(webhook_url)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        errors.append(f"{subject} must use HTTPS")
    if parsed.username or parsed.password:
        errors.append(f"{subject} must not include credentials")
    if _is_local_or_link_local_target(parsed.hostname):
        errors.append(f"{subject} must not target local or link-local addresses")
    if parsed.fragment:
        errors.append(f"{subject} must not include fragments")
    query_keys = sensitive_query_keys(parsed.query)
    if query_keys:
        errors.append(
            f"{subject} must not include sensitive query parameters: "
            + ", ".join(query_keys)
        )
    return tuple(errors)


def _is_local_or_link_local_target(hostname: str | None) -> bool:
    if hostname is None:
        return False
    normalized_hostname = normalize_hostname(hostname)
    if normalized_hostname in {"localhost", "localhost.localdomain"}:
        return True
    if normalized_hostname.endswith(".localhost"):
        return True
    address = ip_address_from_hostname(normalized_hostname)
    if address is None:
        return False
    return address.is_loopback or address.is_link_local or address.is_unspecified

