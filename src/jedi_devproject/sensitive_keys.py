"""Shared names that commonly carry credentials or auth material."""

from __future__ import annotations

SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "accesstoken",
        "api_key",
        "apikey",
        "aws_secret_access_key",
        "awssecretaccesskey",
        "aws_session_token",
        "awssessiontoken",
        "azure_client_secret",
        "azureclientsecret",
        "authorization",
        "client_secret",
        "clientsecret",
        "code",
        "cookie",
        "id_token",
        "idtoken",
        "password",
        "private_key",
        "privatekey",
        "refresh_token",
        "refreshtoken",
        "secret",
        "set_cookie",
        "ssh_private_key",
        "sshprivatekey",
        "signature",
        "token",
        "x_api_key",
        "xapikey",
        "x_client_secret",
        "xclientsecret",
    }
)


def normalize_sensitive_key(key: object) -> str:
    """Return the canonical comparison form for credential-like field names."""
    if type(key) is not str:
        return ""
    return key.strip().lower().replace("-", "_")


def is_sensitive_key(key: object) -> bool:
    """Return whether a structured field or query key commonly carries secrets."""
    return normalize_sensitive_key(key) in SENSITIVE_QUERY_KEYS
