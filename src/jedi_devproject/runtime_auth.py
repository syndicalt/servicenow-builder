"""Admin authentication and rate-limit guards for the runtime API.

Security-sensitive compliance controls: fail-closed admin token checks,
dev-only basic-auth console credentials, and admin rate limiting.
"""

from __future__ import annotations

import base64
import binascii
import secrets

from fastapi import HTTPException, status

from jedi_devproject.rate_limit import InMemoryRateLimiter
from jedi_devproject.runtime_config import RuntimeSettings


def _require_admin_token(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin artifact API is not configured",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin bearer token required",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin bearer token rejected",
        )


def _require_admin_rate_limit(
    *,
    admin_rate_limiter: InMemoryRateLimiter | None,
    key: str,
) -> None:
    if admin_rate_limiter is None:
        return
    decision = admin_rate_limiter.check(key)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


def _require_admin_console_credentials(
    *,
    settings: RuntimeSettings,
    authorization: str | None,
) -> None:
    if settings.admin_auth_mode == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console authentication is disabled",
        )
    if settings.admin_auth_mode in {"oidc", "servicenow_oauth"}:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"admin auth mode is not implemented: {settings.admin_auth_mode}",
        )
    if settings.admin_auth_mode != "dev_basic":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"admin auth mode is not supported: {settings.admin_auth_mode}",
        )
    if settings.runtime_environment.strip().lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="dev_basic admin auth is development-only",
        )
    if not settings.admin_console_username or not settings.admin_console_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin console is not configured",
        )
    credentials = _basic_auth_credentials(authorization)
    if credentials is None:
        raise _admin_console_unauthorized()
    username, password = credentials
    username_ok = secrets.compare_digest(username, settings.admin_console_username)
    password_ok = secrets.compare_digest(password, settings.admin_console_password)
    if not (username_ok and password_ok):
        raise _admin_console_unauthorized()


def _basic_auth_credentials(authorization: str | None) -> tuple[str, str] | None:
    if authorization is None or not authorization.startswith("Basic "):
        return None
    encoded = authorization.removeprefix("Basic ").strip()
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    username, separator, password = decoded.partition(":")
    if separator != ":":
        return None
    return username, password


def _admin_console_unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="admin console credentials required",
        headers={"WWW-Authenticate": 'Basic realm="jedi-admin"'},
    )
