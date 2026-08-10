"""Shared hostname normalization and legacy IP parsing for outbound URL guards."""

from __future__ import annotations

import ipaddress

HOST_DOT_ALIASES = {
    "\u3002",  # ideographic full stop
    "\uff0e",  # fullwidth full stop
    "\uff61",  # halfwidth ideographic full stop
}


def normalize_hostname(hostname: str) -> str:
    normalized = hostname.strip().lower()
    for dot_alias in HOST_DOT_ALIASES:
        normalized = normalized.replace(dot_alias, ".")
    return normalized.rstrip(".")


def ip_address_from_hostname(
    hostname: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return legacy_ipv4_address(hostname)


def is_non_public_hostname(hostname: str) -> bool:
    normalized_hostname = normalize_hostname(hostname)
    if normalized_hostname in {"localhost", "localhost.localdomain"}:
        return True
    if normalized_hostname.endswith(".localhost"):
        return True
    address = ip_address_from_hostname(normalized_hostname)
    if address is None:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def legacy_ipv4_address(hostname: str) -> ipaddress.IPv4Address | None:
    if ":" in hostname:
        return None
    components = hostname.split(".")
    if not 1 <= len(components) <= 4:
        return None
    values: list[int] = []
    for component in components:
        value = legacy_ipv4_component(component)
        if value is None:
            return None
        values.append(value)

    if len(values) == 1:
        if values[0] > 0xFFFFFFFF:
            return None
        address_int = values[0]
    elif len(values) == 2:
        if values[0] > 0xFF or values[1] > 0xFFFFFF:
            return None
        address_int = (values[0] << 24) | values[1]
    elif len(values) == 3:
        if values[0] > 0xFF or values[1] > 0xFF or values[2] > 0xFFFF:
            return None
        address_int = (values[0] << 24) | (values[1] << 16) | values[2]
    else:
        if any(value > 0xFF for value in values):
            return None
        address_int = (
            (values[0] << 24)
            | (values[1] << 16)
            | (values[2] << 8)
            | values[3]
        )
    return ipaddress.IPv4Address(address_int)


def legacy_ipv4_component(component: str) -> int | None:
    if component == "":
        return None
    text = component.lower()
    if text.startswith("0x"):
        digits = text[2:]
        if not digits or any(character not in "0123456789abcdef" for character in digits):
            return None
        return int(digits, 16)
    if len(text) > 1 and text.startswith("0"):
        digits = text[1:]
        if any(character not in "01234567" for character in digits):
            return None
        return int(digits or "0", 8)
    if not text.isdigit():
        return None
    return int(text, 10)
